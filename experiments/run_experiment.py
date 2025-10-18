"""
Experimental Runner

Runs the Fitch protocol experiment:
- Generates N proof problems
- Attempts each problem in 3 conditions (baseline, multi_shot, protocol)
- Logs results to CSV
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path so we can import from src/
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.proof_solver import solve_proof


def load_problems(problems_file: str) -> List[Dict[str, Any]]:
    """
    Load proof problems from JSON file.
    
    Expected format:
    [
        {
            "id": "prob_001",
            "premises": ["(P → Q)", "P"],
            "conclusion": "Q",
            "difficulty": {"depth": 1, "length": 3}
        },
        ...
    ]
    """
    with open(problems_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_result(result: Dict[str, Any], output_file: str):
    """Append a single result to CSV file."""
    fieldnames = [
        'timestamp',
        'problem_id',
        'condition',
        'model',
        'premises',
        'conclusion',
        'solved',
        'time_seconds',
        'conversation_turns',
        'error',
        'validation_issues'
    ]
    
    # Check if file exists to determine if we need to write header
    file_exists = Path(output_file).exists()
    
    with open(output_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        # Prepare row
        row = {
            'timestamp': datetime.now().isoformat(),
            'problem_id': result.get('problem_id', 'unknown'),
            'condition': result['condition'],
            'model': result['model'],
            'premises': json.dumps(result['premises']),
            'conclusion': result['conclusion'],
            'solved': result['solved'],
            'time_seconds': round(result['time_seconds'], 2),
            'conversation_turns': result['conversation_turns'],
            'error': result.get('error', ''),
            'validation_issues': json.dumps(result.get('validation', {}).get('issues', []))
        }
        
        writer.writerow(row)


def run_experiment(
    problems_file: str,
    output_file: str,
    conditions: List[str] = ['baseline', 'multi_shot', 'protocol'],
    model: str = 'gpt-4',
    max_problems: int = None
):
    """
    Run the full experiment.
    
    Args:
        problems_file: Path to JSON file with proof problems
        output_file: Path to output CSV file
        conditions: List of conditions to test
        model: LLM model to use
        max_problems: Limit number of problems (None = all)
    """
    print(f"Loading problems from {problems_file}...")
    problems = load_problems(problems_file)
    
    if max_problems:
        problems = problems[:max_problems]
    
    print(f"Running experiment: {len(problems)} problems × {len(conditions)} conditions = {len(problems) * len(conditions)} total runs")
    print(f"Model: {model}")
    print(f"Output: {output_file}\n")
    
    total_runs = len(problems) * len(conditions)
    current_run = 0
    
    for problem in problems:
        problem_id = problem['id']
        premises = problem['premises']
        conclusion = problem['conclusion']
        
        print(f"\n{'='*60}")
        print(f"Problem {problem_id}")
        print(f"Premises: {', '.join(premises)}")
        print(f"Conclusion: {conclusion}")
        print(f"{'='*60}")
        
        for condition in conditions:
            current_run += 1
            print(f"\n[{current_run}/{total_runs}] Testing condition: {condition}")
            
            try:
                result = solve_proof(
                    premises=premises,
                    conclusion=conclusion,
                    condition=condition,
                    model=model
                )
                
                # Add problem_id to result
                result['problem_id'] = problem_id
                
                # Save result
                save_result(result, output_file)
                
                # Print summary
                status = "✓ SOLVED" if result['solved'] else "✗ FAILED"
                print(f"  {status} in {result['time_seconds']:.2f}s ({result['conversation_turns']} turns)")
                if result['error']:
                    print(f"  Error: {result['error']}")
                
            except Exception as e:
                print(f"  ✗ EXCEPTION: {e}")
                # Log the exception
                error_result = {
                    'problem_id': problem_id,
                    'condition': condition,
                    'model': model,
                    'premises': premises,
                    'conclusion': conclusion,
                    'solved': False,
                    'time_seconds': 0,
                    'conversation_turns': 0,
                    'error': f'Exception: {e}'
                }
                save_result(error_result, output_file)
    
    print(f"\n{'='*60}")
    print(f"Experiment complete! Results saved to {output_file}")
    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Fitch protocol experiment')
    parser.add_argument('--problems', type=str, required=True,
                       help='Path to problems JSON file')
    parser.add_argument('--output', type=str, required=True,
                       help='Path to output CSV file')
    parser.add_argument('--conditions', type=str, nargs='+',
                       default=['baseline', 'multi_shot', 'protocol'],
                       help='Conditions to test')
    parser.add_argument('--model', type=str, default='gpt-4',
                       help='LLM model to use')
    parser.add_argument('--max-problems', type=int, default=None,
                       help='Maximum number of problems to test')
    
    args = parser.parse_args()
    
    run_experiment(
        problems_file=args.problems,
        output_file=args.output,
        conditions=args.conditions,
        model=args.model,
        max_problems=args.max_problems
    ) 