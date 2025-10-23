
"""
Problem Bank Builder

Systematically generates and validates Fitch proofs to build a reliable problem bank.
Uses existing components: problem generator → proof solver → validator → bank storage.
"""

import json
import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.proof_solver import solve_proof
from src.ascii_to_json import convert_ascii_to_json
from src.proof_checker import check_proof

class ProblemBankBuilder:
    def __init__(self, output_file: str = "data/problems/problem_bank.jsonl"):
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_generated': 0,
            'successful_proofs': 0,
            'failed_proofs': 0,
            'validation_errors': 0
        }
    
    def load_existing_problems(self, problems_file: str) -> List[Dict[str, Any]]:
        """Load problems from existing JSON file."""
        with open(problems_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_proof_metadata(self, ascii_proof: str, json_proof: Dict) -> Dict[str, Any]:
        """Extract metadata about the proof (line count, rules used, etc.)."""
        # Count lines in ASCII proof
        proof_lines = [line for line in ascii_proof.split('\n') if line.strip()]
        
        # Extract rules used from JSON proof
        rules_used = set()
        for step in json_proof.get('solution', []):
            justification = step['justification']
            # Extract rule name (part before space or number)
            rule_match = justification.split()[0] if justification else ''
            if rule_match and rule_match not in ['Pr', 'Hyp', 'R']:
                rules_used.add(rule_match)
        
        return {
            'line_count': len(proof_lines),
            'rules_used': list(rules_used),
            'subproof_depth': max(step.get('assumeno', 0) for step in json_proof.get('solution', [])),
            'total_steps': len(json_proof.get('solution', []))
        }
    
    def test_problem_with_llm(self, problem: Dict[str, Any], model: str = "deepseek/deepseek-chat") -> Optional[Dict[str, Any]]:
        """Test if LLM can solve this problem and return solution if successful."""
        try:
            print(f"  Testing problem {problem['id']}...")
            
            # Use protocol condition (most structured approach)
            result = solve_proof(
                premises=problem['premises'],
                conclusion=problem['conclusion'],
                condition='protocol',  # Use full protocol for best results
                model=model
            )
            
            if result['solved']:
                print(f"    ✅ SOLVED in {result['time_seconds']:.2f}s")
                
                # Extract metadata
                metadata = self.extract_proof_metadata(
                    result['ascii_proof'], 
                    result['json_proof']
                )
                
                # Combine problem with solution and metadata
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
                
                return bank_entry
            else:
                print(f"    ❌ FAILED: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"    💥 EXCEPTION: {e}")
            return None
    
    def save_to_bank(self, bank_entry: Dict[str, Any]):
        """Append successful problem to JSONL bank file."""
        with open(self.output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(bank_entry, ensure_ascii=False) + '\n')
    
    def build_from_existing_problems(self, problems_file: str, max_problems: int = None, model: str = "deepseek/deepseek-chat"):
        """Build problem bank from existing problem set."""
        print(f"📚 Building problem bank from {problems_file}")
        
        problems = self.load_existing_problems(problems_file)
        if max_problems:
            problems = problems[:max_problems]
        
        print(f"Testing {len(problems)} problems...\n")
        
        successful_entries = []
        
        for i, problem in enumerate(problems, 1):
            print(f"[{i}/{len(problems)}] ", end="")
            
            bank_entry = self.test_problem_with_llm(problem, model)
            
            if bank_entry:
                self.save_to_bank(bank_entry)
                successful_entries.append(bank_entry)
                self.stats['successful_proofs'] += 1
            else:
                self.stats['failed_proofs'] += 1
            
            self.stats['total_generated'] += 1
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"📊 PROBLEM BANK BUILD SUMMARY")
        print(f"{'='*60}")
        print(f"Total problems tested: {self.stats['total_generated']}")
        print(f"Successful proofs: {self.stats['successful_proofs']} ({self.stats['successful_proofs']/self.stats['total_generated']*100:.1f}%)")
        print(f"Failed proofs: {self.stats['failed_proofs']}")
        print(f"Problem bank: {self.output_file}")
        print(f"Entries saved: {len(successful_entries)}")
        
        return successful_entries

def main():
    """Main function to build problem bank."""
    builder = ProblemBankBuilder("data/problems/fitch_problem_bank.jsonl")
    
    # Build from your existing 50 medium problems
    successful_entries = builder.build_from_existing_problems(
        problems_file="data/problems/50_medium_problems.json",
        max_problems=10,  # Start small for testing
        model="deepseek/deepseek-chat"
    )
    
    print(f"\n🎉 Problem bank created with {len(successful_entries)} validated proofs!")
    print(f"Next steps:")
    print(f"  1. Run: python experiments/build_problem_bank.py")
    print(f"  2. Check: data/problems/fitch_problem_bank.jsonl")
    print(f"  3. Use the problem sampler to create student exercises")

if __name__ == "__main__":
    main()