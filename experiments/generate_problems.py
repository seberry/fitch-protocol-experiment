"""
Generate proof problems from entailment_finder output.

Converts the console output format to structured JSON.
"""

import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# We'll manually run entailment_finder and capture output
# For now, let's create a small test set manually

def create_test_problems(output_file: str, num_problems: int = 10):
    """Create a small set of test problems."""
    
    # These are hand-crafted simple problems for initial testing
    problems = [
        {
            "id": "test_001",
            "premises": ["(P → Q)", "P"],
            "conclusion": "Q",
            "difficulty": {"depth": 0, "length": 3}
        },
        {
            "id": "test_002", 
            "premises": ["(P → Q)", "(Q → R)", "P"],
            "conclusion": "R",
            "difficulty": {"depth": 0, "length": 4}
        },
        {
            "id": "test_003",
            "premises": ["(P ∧ Q)"],
            "conclusion": "P",
            "difficulty": {"depth": 0, "length": 2}
        },
        {
            "id": "test_004",
            "premises": ["P", "Q"],
            "conclusion": "(P ∧ Q)",
            "difficulty": {"depth": 0, "length": 3}
        },
        {
            "id": "test_005",
            "premises": ["(P ∨ Q)", "(P → R)", "(Q → R)"],
            "conclusion": "R",
            "difficulty": {"depth": 1, "length": 6}
        }
    ]
    
    # Limit to requested number
    problems = problems[:num_problems]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(problems, f, indent=2, ensure_ascii=False)
    
    print(f"Created {len(problems)} test problems in {output_file}")


if __name__ == "__main__":
    output_file = "data/problems/test_set.json"
    
    # Create data/problems directory if needed
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    create_test_problems(output_file, num_problems=5)
    print(f"\nTo run experiment:")
    print(f"  python experiments/run_experiment.py --problems {output_file} --output data/results/pilot_results.csv --max-problems 5")