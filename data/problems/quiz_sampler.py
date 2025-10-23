# experiments/quiz_sampler.py
"""
Quiz Sampler for Student Exercises

Creates customized quiz sets based on your specific rule-based quiz types.
Provides problems in a format easy for visual inspection and LaTeX typesetting.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any, Set
import textwrap

class QuizSampler:
    def __init__(self, bank_file: str = "data/problems/enhanced_problem_bank.jsonl"):
        self.bank_file = Path(bank_file)
        self.problems = self.load_bank()
        
        # Your exact quiz types with descriptions
        self.quiz_types = {
            'quiz_1': {
                'name': 'Basic & and →E',
                'description': 'Using only & rules and →E',
                'allowed_rules': {'&E', '→E'},
                'max_lines': 10,
                'max_depth': 0
            },
            'quiz_2': {
                'name': '& and → rules', 
                'description': 'Using & and → rules',
                'allowed_rules': {'&E', '&I', '→E', '→I'},
                'max_lines': 15,
                'max_depth': 1
            },
            'quiz_3': {
                'name': '&, →, ↔, ∨ rules',
                'description': 'Using &, →, ↔ and ∨ rules',
                'allowed_rules': {'&E', '&I', '→E', '→I', '↔E', '↔I', '∨E', '∨I'},
                'max_lines': 20,
                'max_depth': 2
            },
            'quiz_4': {
                'name': 'Add ¬E for ⊥',
                'description': 'Using previous rules plus ¬E to derive ⊥',
                'allowed_rules': {'&E', '&I', '→E', '→I', '↔E', '↔I', '∨E', '∨I', '¬E'},
                'max_lines': 25,
                'max_depth': 2
            },
            'quiz_5': {
                'name': 'Add ¬ rules',
                'description': 'Using &, →, ↔, ∨ and ¬ rules',
                'allowed_rules': {'&E', '&I', '→E', '→I', '↔E', '↔I', '∨E', '∨I', '¬E', '¬I'},
                'max_lines': 30,
                'max_depth': 3
            },
            'quiz_6': {
                'name': 'Everything',
                'description': 'Using all rules (adding IP and ⊥E/Explosion)',
                'allowed_rules': {'&E', '&I', '→E', '→I', '↔E', '↔I', '∨E', '∨I', '¬E', '¬I', '⊥E', 'IP'},
                'max_lines': 35,
                'max_depth': 3
            }
        }
    
    def load_bank(self) -> List[Dict[str, Any]]:
        """Load problems from bank file."""
        problems = []
        if self.bank_file.exists():
            with open(self.bank_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        problems.append(json.loads(line))
        return problems
    
    def get_problems_by_quiz_type(self, quiz_type: str) -> List[Dict[str, Any]]:
        """Get all problems compatible with a specific quiz type."""
        quiz_config = self.quiz_types[quiz_type]
        
        compatible = []
        for problem in self.problems:
            problem_rules = set(problem.get('metadata', {}).get('rules_used', []))
            metadata = problem.get('metadata', {})
            
            # Check rule compatibility
            if not problem_rules.issubset(quiz_config['allowed_rules']):
                continue
            
            # Check difficulty constraints
            if quiz_config['max_lines'] and metadata.get('line_count', 0) > quiz_config['max_lines']:
                continue
            if quiz_config['max_depth'] and metadata.get('subproof_depth', 0) > quiz_config['max_depth']:
                continue
            
            compatible.append(problem)
        
        return compatible
    
    def create_quiz(self, quiz_type: str, num_problems: int = 3) -> List[Dict[str, Any]]:
        """Create a quiz with specified number of problems."""
        compatible_problems = self.get_problems_by_quiz_type(quiz_type)
        
        if len(compatible_problems) < num_problems:
            print(f"Warning: Only {len(compatible_problems)} problems available for {quiz_type}")
            return compatible_problems
        
        return random.sample(compatible_problems, num_problems)
    
    def create_progressive_quiz_set(self, num_per_type: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """Create a complete set of quizzes across all types (for a full course)."""
        quiz_set = {}
        
        for quiz_type in self.quiz_types:
            quiz_set[quiz_type] = self.create_quiz(quiz_type, num_per_type)
        
        return quiz_set
    
    def print_quiz(self, quiz_type: str, problems: List[Dict[str, Any]], show_solutions: bool = False):
        """Print a beautifully formatted quiz."""
        quiz_config = self.quiz_types[quiz_type]
        
        print("=" * 70)
        print(f"QUIZ: {quiz_config['name']}")
        print(f"Description: {quiz_config['description']}")
        print("=" * 70)
        
        for i, problem in enumerate(problems, 1):
            print(f"\n{'─' * 70}")
            print(f"PROBLEM {i}:")
            print(f"{'─' * 70}")
            
            # Print problem statement
            print("Premises:")
            for j, premise in enumerate(problem['premises'], 1):
                print(f"  {j}. {premise}")
            print(f"Conclusion: {problem['conclusion']}")
            
            # Print metadata
            metadata = problem.get('metadata', {})
            print(f"\n[Metadata: {metadata.get('line_count', '?')} lines, " 
                  f"depth {metadata.get('subproof_depth', '?')}, "
                  f"rules: {', '.join(metadata.get('rules_used', []))}]")
            
            # Print solution if requested
            if show_solutions:
                print(f"\nSOLUTION:")
                print(problem.get('ascii_solution', 'No solution available'))
        
        print(f"\n{'=' * 70}")
        print(f"END OF QUIZ")
        print(f"{'=' * 70}")
    
    def export_quiz_latex(self, quiz_type: str, problems: List[Dict[str, Any]], output_file: str):
        """Export quiz to LaTeX format for typesetting."""
        quiz_config = self.quiz_types[quiz_type]
        
        latex_content = [
            "\\documentclass{article}",
            "\\usepackage{amsmath, amssymb}",
            "\\usepackage{logicproof}",
            "\\usepackage[margin=1in]{geometry}",
            "\\title{Fitch Proof Quiz: " + quiz_config['name'] + "}",
            "\\author{Logic Course}",
            "\\date{}",
            "\\begin{document}",
            "\\maketitle",
            "\\noindent\\textbf{Instructions:} Prove each of