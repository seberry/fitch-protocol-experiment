"""
Automated problem generation with automatic file naming
"""
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import entailment_finder functions
sys.path.insert(0, str(Path(__file__).parent.parent))

from entailment_finder_interactive import generate_formula, check_entailment, check_contradiction

def generate_problems_with_bundle(bundle_choice="2"):
    """Generate problems by calling the functions directly"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(f"data/problems/problems_{timestamp}.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating problems with bundle {bundle_choice}...")
    print(f"Output: {output_file}")
    
    # Map bundle choice to connectives
    connectives_map = {
        "1": {'binary': ['&', '->']},
        "2": {'binary': ['&', '|', '->', '<->']},
        "3": {'binary': ['&', '|', '->', '<->'], 'unary': ['~']}
    }
    
    selected_connectives = connectives_map[bundle_choice]
    
    problems = []
    attempts = 0
    target_entailments = 10  # Start small for testing
    
    while len(problems) < target_entailments:
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
            'id': f"entailment_{len(problems)+1:03d}",
            'premises': premises,
            'conclusion': conclusion,
            'difficulty': {
                'depth': 2,
                'length': 3
            }
        }
        problems.append(problem)
        
        print(f"Found problem {len(problems)}/{target_entailments}")

    # Save problems
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(problems, f, indent=2)
    
    print(f"Generated {len(problems)} problems to {output_file}")
    return output_file

if __name__ == "__main__":
    bundle = input("Choose bundle (1=basic, 2=positive, 3=full) [2]: ") or "2"
    generate_problems_with_bundle(bundle)