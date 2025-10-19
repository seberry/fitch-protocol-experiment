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



def save_conversation(
    problem_id: str,
    condition: str,
    conversation: List[Dict[str, str]],
    output_dir: str = "data/results/conversations"
):
    """
    Save a conversation to a readable text file.
    
    Args:
        problem_id: ID of the problem (e.g., 'test_001')
        condition: Experimental condition (baseline/multi_shot/protocol)
        conversation: List of message dicts with 'role' and 'content'
        output_dir: Directory to save conversation files
    """
    from pathlib import Path
    
    # Create directory if needed
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Filename: test_001_protocol_conv.txt
    filename = f"{problem_id}_{condition}_conv.txt"
    filepath = Path(output_dir) / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Problem: {problem_id}\n")
        f.write(f"Condition: {condition}\n")
        f.write("="*70 + "\n\n")
        
        for i, msg in enumerate(conversation, 1):
            role = msg['role'].upper()
            content = msg['content']
            
            f.write(f"{'='*70}\n")
            f.write(f"TURN {i}: {role}\n")
            f.write(f"{'='*70}\n")
            f.write(f"{content}\n\n")
        
        f.write(f"{'='*70}\n")
        f.write(f"END OF CONVERSATION\n")
        f.write(f"{'='*70}\n")


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
    """Append a single result to CSV file with FULL logging."""
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
        # NEW: Save all the intermediate data!
        'ascii_proof',           # The raw ASCII the LLM generated
        'json_proof',            # The flat JSON with assumeno
        'conversation_history',  # Full message history
        'error',
        'validation_issues'
    ]
    
    file_exists = Path(output_file).exists()
    
    with open(output_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        # Prepare row with ALL the data
        row = {
            'timestamp': datetime.now().isoformat(),
            'problem_id': result.get('problem_id', 'unknown'),
            'condition': result['condition'],
            'model': result['model'],
            'premises': json.dumps(result['premises'], ensure_ascii=False),
            'conclusion': result['conclusion'],
            'solved': result['solved'],
            'time_seconds': round(result['time_seconds'], 2),
            'conversation_turns': result['conversation_turns'],
            # Save the actual proofs and conversation!
            'ascii_proof': result.get('ascii_proof', ''),
            'json_proof': json.dumps(result.get('json_proof', {}), ensure_ascii=False),
            'conversation_history': json.dumps(result.get('conversation_history', []), ensure_ascii=False),
            'error': result.get('error', ''),
            'validation_issues': json.dumps(result.get('validation', {}).get('issues', []), ensure_ascii=False)
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
                
                # NEW: Save conversation to readable file
                if 'conversation_history' in result and result['conversation_history']:
                    save_conversation(
                        problem_id=problem_id,
                        condition=condition,
                        conversation=result['conversation_history'],
                        output_dir="data/results/conversations"
            )
                
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
    
    args = parser.parse_args()  # ← THIS LINE IS CRITICAL
    
    run_experiment(
        problems_file=args.problems,
        output_file=args.output,
        conditions=args.conditions,
        model=args.model,
        max_problems=args.max_problems
    )