"""
Quick problem harvesting using baseline condition only
- Generate problems
- Test with baseline (one-shot)
- Add successful ones to bank
- Log failures for later analysis
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.proof_solver import solve_proof
from src.symbol_standardizer import standardize_symbols
from experiments.generate_and_save_problems import generate_problems_with_bundle

def generate_problems_batch(num_problems: int, bundle: str = "2"):
    """Generate a batch of problems without saving to file"""
    print(f"🔧 Generating {num_problems} problems with bundle {bundle}...")
    
    # Map bundle choice to connectives
    connectives_map = {
        "1": {'binary': ['&', '->']},
        "2": {'binary': ['&', '|', '->', '<->']},
        "3": {'binary': ['&', '|', '->', '<->'], 'unary': ['~']}
    }
    
    selected_connectives = connectives_map[bundle]
    
    problems = []
    attempts = 0
    max_attempts = num_problems * 10  # Prevent infinite loops
    
    while len(problems) < num_problems and attempts < max_attempts:
        attempts += 1
        num_premises = 2  # Fixed for simplicity
        premises = list(set(generate_formula(2, selected_connectives) for _ in range(num_premises)))
        
        if len(premises) < num_premises:
            continue
            
        conclusion = generate_formula(2, selected_connectives)

        # Apply filters
        if conclusion in premises: 
            continue
            
        try:
            if not check_entailment(premises, conclusion): 
                continue
            if check_contradiction(premises): 
                continue
                
            # Check if premises are necessary
            is_necessary = True
            if len(premises) > 1:
                for i in range(len(premises)):
                    subset_premises = premises[:i] + premises[i+1:]
                    if check_entailment(subset_premises, conclusion):
                        is_necessary = False
                        break
            if not is_necessary:
                continue
                
        except (ValueError, IndexError):
            continue

        # Create problem entry with proper structure
        problem = {
            'id': f"quick_{len(problems)+1:03d}",
            'premises': [standardize_symbols(p) for p in premises],  # Standardize symbols
            'conclusion': standardize_symbols(conclusion),
            'difficulty': {
                'depth': 2,
                'length': 3
            }
        }
        problems.append(problem)
        print(f"   Found problem {len(problems)}/{num_problems}")
    
    if len(problems) < num_problems:
        print(f"⚠️  Only found {len(problems)} problems after {attempts} attempts")
    
    return problems

def add_to_problem_bank(problems_with_solutions):
    """Add successful problems with their solutions to the problem bank"""
    if not problems_with_solutions:
        print("❌ No successful problems to add")
        return 0
    
    bank_file = Path("data/problems/fitch_problem_bank.jsonl")
    bank_file.parent.mkdir(parents=True, exist_ok=True)
    
    count = 0
    with open(bank_file, 'a', encoding='utf-8') as f:
        for problem in problems_with_solutions:
            bank_entry = {
                'id': problem['id'],
                'premises': problem['premises'],
                'conclusion': problem['conclusion'],
                'difficulty': problem.get('difficulty', {'depth': 2, 'length': 3}),
                'ascii_solution': problem['ascii_solution'],
                'json_solution': problem['json_solution'],
                'metadata': {
                    'line_count': len([line for line in problem['ascii_solution'].split('\n') if line.strip()]),
                    'rules_used': extract_rules_from_json(problem['json_solution']),
                    'subproof_depth': 0,  # Will be calculated from json_solution
                    'total_steps': len(problem['json_solution'].get('solution', []))
                },
                'validation_result': problem['validation_result'],
                'solved_at': datetime.now().isoformat(),
                'model_used': 'deepseek/deepseek-chat',
                'condition_used': 'baseline'
            }
            f.write(json.dumps(bank_entry, ensure_ascii=False) + '\n')
            count += 1
    
    print(f"✅ Added {count} problems to bank")
    return count

def extract_rules_from_json(json_proof):
    """Extract rules used from JSON proof"""
    rules_used = set()
    for step in json_proof.get('solution', []):
        justification = step.get('justification', '')
        if justification:
            rule_match = justification.split()[0]
            if rule_match and rule_match not in ['Pr', 'Hyp', 'R']:
                rules_used.add(rule_match)
    return list(rules_used)

def save_failures(failed_problems):
    """Save failed problems for later analysis"""
    if not failed_problems:
        print("🎉 No failures to save!")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    failures_file = Path(f"data/problems/failures_{timestamp}.json")
    failures_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(failures_file, 'w', encoding='utf-8') as f:
        json.dump(failed_problems, f, indent=2)
    
    print(f"📝 Saved {len(failed_problems)} failures to {failures_file}")

def quick_harvest_workflow(batch_size=10, bundle="2"):
    """Generate → Test → Harvest in one go"""
    print("🚀 QUICK HARVEST WORKFLOW")
    print("=" * 40)
    
    # 1. Generate problems
    problems = generate_problems_batch(batch_size, bundle)
    if not problems:
        print("❌ Failed to generate problems")
        return 0, 0
    
    print(f"📋 Generated {len(problems)} problems")
    
    # 2. Test with baseline only (saves tokens)
    results = []
    for i, problem in enumerate(problems, 1):
        print(f"🧪 Testing problem {i}/{len(problems)}: {problem['id']}")
        
        result = solve_proof(
            premises=problem['premises'],
            conclusion=problem['conclusion'], 
            condition='baseline',
            model='deepseek/deepseek-chat'
        )
        results.append((problem, result))
        
        status = "✅ SOLVED" if result['solved'] else "❌ FAILED"
        print(f"   {status} in {result['time_seconds']:.2f}s")
    
    # 3. Process results
    successful_problems = []
    failed_problems = []
    
    for problem, result in results:
        if result['solved']:
            # Add solution data to the problem
            problem['ascii_solution'] = result['ascii_proof']
            problem['json_solution'] = result['json_proof']
            problem['validation_result'] = result['validation']
            successful_problems.append(problem)
        else:
            failed_problems.append({
                'problem': problem,
                'error': result.get('error', 'Unknown error'),
                'time_seconds': result['time_seconds']
            })
    
    # 4. Add successful ones to bank
    added_count = add_to_problem_bank(successful_problems)
    
    # 5. Store failures for analysis
    save_failures(failed_problems)
    
    print(f"\n📊 SUMMARY: {len(successful_problems)} successful, {len(failed_problems)} failures")
    print(f"🎯 {added_count} new problems added to bank")
    
    return len(successful_problems), len(failed_problems)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick harvest problems for student bank')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of problems to generate')
    parser.add_argument('--bundle', type=str, default='2', help='Problem bundle (1=basic, 2=positive, 3=full)')
    
    args = parser.parse_args()
    
    successful, failures = quick_harvest_workflow(
        batch_size=args.batch_size,
        bundle=args.bundle
    )