# experiments/enhanced_problem_bank.py
"""
Enhanced Problem Bank Builder

Automatically generates problems, tests them with LLM, and adds validated proofs to a growing bank.
Categorizes problems by rule sets for easy quiz creation.
"""

import json
import random
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import itertools

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.proof_solver import solve_proof
from entailment_finder import generate_formula, check_entailment, check_contradiction

class EnhancedProblemBank:
    def __init__(self, bank_file: str = "data/problems/enhanced_problem_bank.jsonl"):
        self.bank_file = Path(bank_file)
        self.bank_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Your quiz rule sets
        self.quiz_types = {
            'quiz_1': {'&E', '→E'},  # Only & rules and →E
            'quiz_2': {'&E', '&I', '→E', '→I'},  # & and → rules
            'quiz_3': {'&E', '&I', '→E', '→I', '↔E', '↔I', '∨E', '∨I'},  # &, →, ↔, ∨
            'quiz_4': {'&E', '&I', '→E', '→I', '↔E', '↔I', '∨E', '∨I', '¬E'},  # Add ¬E for ⊥
            'quiz_5': {'&E', '&I', '→E', '→I', '↔E', '↔I', '∨E', '∨I', '¬E', '¬I'},  # Add ¬ rules
            'quiz_6': {'&E', '&I', '→E', '→I', '↔E', '↔I', '∨E', '∨I', '¬E', '¬I', '⊥E', 'IP'}  # Everything
        }
        
        self.stats = {
            'total_generated': 0,
            'successful_proofs': 0,
            'failed_proofs': 0,
            'by_quiz_type': {quiz_type: 0 for quiz_type in self.quiz_types}
        }
    
    def load_bank(self) -> List[Dict[str, Any]]:
        """Load existing problems from bank."""
        problems = []
        if self.bank_file.exists():
            with open(self.bank_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        problems.append(json.loads(line))
        return problems
    
    def generate_new_problem(self, max_depth: int = 2, num_premises_range: tuple = (2, 3)) -> Optional[Dict[str, Any]]:
        """Generate a new valid entailment problem."""
        attempts = 0
        max_attempts = 100
        
        while attempts < max_attempts:
            attempts += 1
            
            # Generate random problem
            num_premises = random.randint(*num_premises_range)
            premises = list(set(generate_formula(max_depth) for _ in range(num_premises)))
            
            # Ensure we have the right number of premises (no duplicates)
            if len(premises) < num_premises:
                continue
                
            conclusion = generate_formula(max_depth)
            
            # Filter: conclusion shouldn't be in premises
            if conclusion in premises:
                continue
            
            # Check if valid entailment
            try:
                is_valid = check_entailment(premises, conclusion)
            except (ValueError, IndexError):
                continue
            
            if is_valid:
                # Filter: premises shouldn't be contradictory
                if check_contradiction(premises):
                    continue
                
                # Filter: check if all premises are necessary
                is_necessary = True
                if len(premises) > 1:
                    for i in range(len(premises)):
                        subset_premises = premises[:i] + premises[i+1:]
                        if check_entailment(subset_premises, conclusion):
                            is_necessary = False
                            break
                
                if is_necessary:
                    problem_id = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
                    
                    return {
                        'id': problem_id,
                        'premises': premises,
                        'conclusion': conclusion,
                        'difficulty': {
                            'depth': max_depth,
                            'length': len(premises) + 1  # +1 for conclusion
                        },
                        'generated_at': datetime.now().isoformat()
                    }
        
        return None
    
    def extract_proof_metadata(self, ascii_proof: str, json_proof: Dict) -> Dict[str, Any]:
        """Extract metadata including quiz type categorization."""
        proof_lines = [line for line in ascii_proof.split('\n') if line.strip()]
        
        # Extract rules used
        rules_used = set()
        for step in json_proof.get('solution', []):
            justification = step['justification']
            rule_match = justification.split()[0] if justification else ''
            if rule_match and rule_match not in ['Pr', 'Hyp', 'R']:
                rules_used.add(rule_match)
        
        # Determine which quiz types this problem fits
        compatible_quiz_types = []
        for quiz_type, required_rules in self.quiz_types.items():
            if rules_used.issubset(required_rules):
                compatible_quiz_types.append(quiz_type)
        
        return {
            'line_count': len(proof_lines),
            'rules_used': list(rules_used),
            'subproof_depth': max(step.get('assumeno', 0) for step in json_proof.get('solution', [])),
            'total_steps': len(json_proof.get('solution', [])),
            'compatible_quiz_types': compatible_quiz_types
        }
    
    def test_and_save_problem(self, problem: Dict[str, Any], model: str = "deepseek/deepseek-chat") -> bool:
        """Test problem with LLM and save if successful."""
        try:
            print(f"  Testing {problem['id']}...")
            
            result = solve_proof(
                premises=problem['premises'],
                conclusion=problem['conclusion'],
                condition='protocol',
                model=model
            )
            
            if result['solved']:
                print(f"    ✅ SOLVED in {result['time_seconds']:.2f}s")
                
                # Extract metadata
                metadata = self.extract_proof_metadata(
                    result['ascii_proof'], 
                    result['json_proof']
                )
                
                # Create bank entry
                bank_entry = {
                    **problem,
                    'ascii_solution': result['ascii_proof'],
                    'json_solution': result['json_proof'],
                    'metadata': metadata,
                    'validation_result': result['validation'],
                    'solved_at': datetime.now().isoformat(),
                    'model_used': model,
                    'condition_used': 'protocol'
                }
                
                # Save to bank
                self.save_to_bank(bank_entry)
                
                # Update stats
                self.stats['successful_proofs'] += 1
                for quiz_type in metadata['compatible_quiz_types']:
                    self.stats['by_quiz_type'][quiz_type] += 1
                
                return True
            else:
                print(f"    ❌ FAILED: {result.get('error', 'Unknown error')}")
                self.stats['failed_proofs'] += 1
                return False
                
        except Exception as e:
            print(f"    💥 EXCEPTION: {e}")
            self.stats['failed_proofs'] += 1
            return False
    
    def save_to_bank(self, bank_entry: Dict[str, Any]):
        """Append to growing bank file."""
        with open(self.bank_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(bank_entry, ensure_ascii=False) + '\n')
    
    def generate_and_test_batch(self, batch_size: int = 10, model: str = "deepseek/deepseek-chat"):
        """Generate and test a batch of new problems."""
        print(f"🎲 Generating {batch_size} new problems...")
        
        successful = 0
        
        for i in range(batch_size):
            print(f"[{i+1}/{batch_size}] ", end="")
            
            problem = self.generate_new_problem()
            if problem:
                if self.test_and_save_problem(problem, model):
                    successful += 1
            else:
                print("    ⚠️  Could not generate valid problem")
                self.stats['failed_proofs'] += 1
            
            self.stats['total_generated'] += 1
        
        return successful
    
    def print_stats(self):
        """Print comprehensive statistics."""
        bank_problems = self.load_bank()
        
        print(f"\n{'='*60}")
        print(f"📊 ENHANCED PROBLEM BANK STATISTICS")
        print(f"{'='*60}")
        print(f"Total problems in bank: {len(bank_problems)}")
        print(f"Current session:")
        print(f"  Generated: {self.stats['total_generated']}")
        print(f"  Successful: {self.stats['successful_proofs']}")
        print(f"  Failed: {self.stats['failed_proofs']}")
        print(f"  Success rate: {self.stats['successful_proofs']/self.stats['total_generated']*100:.1f}%")
        
        print(f"\nProblems by quiz type:")
        for quiz_type, count in self.stats['by_quiz_type'].items():
            if count > 0:
                print(f"  {quiz_type}: {count} problems")

def main():
    """Main function - generate a batch of new problems."""
    bank = EnhancedProblemBank()
    
    # Generate 5 new problems
    successful = bank.generate_and_test_batch(batch_size=5)
    
    bank.print_stats()
    
    print(f"\n🎉 Added {successful} new problems to the bank!")
    print(f"Bank file: {bank.bank_file}")

if __name__ == "__main__":
    main()