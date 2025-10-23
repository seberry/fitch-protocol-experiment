# experiments/problem_sampler.py
"""
Problem Sampler for Student Exercises

Selects problems from the bank based on rule constraints and difficulty.
No API calls at runtime - works entirely offline.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any, Set

class ProblemSampler:
    def __init__(self, bank_file: str = "data/problems/fitch_problem_bank.jsonl"):
        self.bank_file = Path(bank_file)
        self.problems = self.load_bank()
    
    def load_bank(self) -> List[Dict[str, Any]]:
        """Load problems from JSONL bank file."""
        problems = []
        if self.bank_file.exists():
            with open(self.bank_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        problems.append(json.loads(line))
        return problems
    
    def filter_by_rules(self, allowed_rules: Set[str]) -> List[Dict[str, Any]]:
        """Filter problems to only include specified rules."""
        filtered = []
        for problem in self.problems:
            problem_rules = set(problem.get('metadata', {}).get('rules_used', []))
            if problem_rules.issubset(allowed_rules):
                filtered.append(problem)
        return filtered
    
    def filter_by_difficulty(self, max_lines: int = None, max_depth: int = None) -> List[Dict[str, Any]]:
        """Filter problems by difficulty constraints."""
        filtered = []
        for problem in self.problems:
            metadata = problem.get('metadata', {})
            if max_lines and metadata.get('line_count', 0) > max_lines:
                continue
            if max_depth and metadata.get('subproof_depth', 0) > max_depth:
                continue
            filtered.append(problem)
        return filtered
    
    def sample_problems(self, count: int = 5, allowed_rules: Set[str] = None, **difficulty_kwargs) -> List[Dict[str, Any]]:
        """Sample problems with optional constraints."""
        candidates = self.problems
        
        # Apply rule filters
        if allowed_rules:
            candidates = self.filter_by_rules(allowed_rules)
        
        # Apply difficulty filters
        if difficulty_kwargs:
            candidates = self.filter_by_difficulty(**difficulty_kwargs)
        
        # Sample randomly
        if len(candidates) < count:
            print(f"Warning: Only {len(candidates)} problems match criteria (requested {count})")
            return candidates
        else:
            return random.sample(candidates, count)
    
    def print_problem_set(self, problems: List[Dict[str, Any]]):
        """Print a nicely formatted problem set."""
        print("Fitch Proof Exercises")
        print("=" * 50)
        
        for i, problem in enumerate(problems, 1):
            print(f"\nProblem {i}:")
            print(f"Premises: {', '.join(problem['premises'])}")
            print(f"Conclusion: {problem['conclusion']}")
            print(f"Difficulty: {problem['metadata']['line_count']} lines, depth {problem['metadata']['subproof_depth']}")
            print(f"Rules needed: {', '.join(problem['metadata']['rules_used'])}")

def main():
    """Example usage of problem sampler."""
    sampler = ProblemSampler()
    
    # Example: Sample problems using only basic rules
    basic_rules = {'→E', '→I', '∧E', '∧I'}
    problems = sampler.sample_problems(
        count=3,
        allowed_rules=basic_rules,
        max_lines=15,
        max_depth=1
    )
    
    sampler.print_problem_set(problems)

if __name__ == "__main__":
    main()