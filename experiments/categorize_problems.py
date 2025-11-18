"""
Categorize Fitch problems into 4 types for course website

Type 1 — Basic
Allowed: ∧I, ∧E, →I, →E
Must use: (implicit—any of the above)

Type 2 — Positive Logic  
Allowed: Type 1 + ∨I, ∨E, ↔I, ↔E
New-rule condition: uses ≥1 of {∨I, ∨E, ↔I, ↔E}

Type 3 — Add Negation (no EFQ/IP)
Allowed: Type 2 + ¬I, ¬E
New-rule condition: uses ≥1 of {¬I, ¬E}

Type 4 — Full TFL Core (IP + EFQ)
Allowed: Type 3 + IP, ⊥E (EFQ)
New-rule condition: uses ≥1 of {IP, ⊥E} (rules not in Type 3)
"""

import json
import sys
from pathlib import Path



# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# ... existing TYPE_RULES and NEW_RULES definitions ...

from src.symbol_standardizer import standardize_symbols


# Define rule sets for each type
TYPE_RULES = {
    1: {"∧I", "∧E", "→I", "→E"},
    2: {"∧I", "∧E", "→I", "→E", "∨I", "∨E", "↔I", "↔E"},
    3: {"∧I", "∧E", "→I", "→E", "∨I", "∨E", "↔I", "↔E", "¬I", "¬E"},
    4: {"∧I", "∧E", "→I", "→E", "∨I", "∨E", "↔I", "↔E", "¬I", "¬E", "IP", "⊥E"}
}

# New rules for each type (rules that weren't in previous type)
NEW_RULES = {
    2: {"∨I", "∨E", "↔I", "↔E"},
    3: {"¬I", "¬E"},
    4: {"IP", "⊥E"}
}

def categorize_problem(rules_used):
    """Categorize a problem based on rules used"""
    rules_set = set(rules_used)
    
    # Check if problem fits in each type
    for type_num in [4, 3, 2, 1]:
        allowed_rules = TYPE_RULES[type_num]
        
        # Must only use allowed rules for this type
        if not rules_set.issubset(allowed_rules):
            continue
            
        # For types 2+, must use at least one new rule
        if type_num > 1:
            new_rules = NEW_RULES[type_num]
            if not any(rule in new_rules for rule in rules_set):
                continue
                
        return type_num
    
    # If no type matches, return None
    return None

def load_problems(bank_file):
    """Load problems from JSONL file"""
    problems = []
    with open(bank_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                problems.append(json.loads(line))
    return problems




def main():
    bank_file = Path("data/problems/fitch_problem_bank.jsonl")
    
    if not bank_file.exists():
        print(f"❌ Problem bank not found at: {bank_file}")
        return
    
    print("📚 Loading problems from problem bank...")
    problems = load_problems(bank_file)
    print(f"✅ Loaded {len(problems)} problems")
    
    # Categorize problems
    categorized = {1: [], 2: [], 3: [], 4: []}
    uncategorized = []
    
    for problem in problems:
        rules_used = problem['metadata']['rules_used']
        # Use total_steps instead of line_count for actual proof length
        proof_length = problem['metadata']['total_steps']
        
        category = categorize_problem(rules_used)
        
        if category:
            # Standardize symbols for display
            standardized_premises = [standardize_symbols(p) for p in problem['premises']]
            standardized_conclusion = standardize_symbols(problem['conclusion'])
            
            categorized[category].append({
                'id': problem['id'],
                'premises': standardized_premises,
                'conclusion': standardized_conclusion,
                'rules_used': rules_used,
                'proof_length': proof_length
            })
        else:
            uncategorized.append({
                'id': problem['id'],
                'rules_used': rules_used,
                'proof_length': proof_length
            })
    
    # Print clean lists for each type
    print(f"\n{'='*60}")
    print("📋 PROBLEMS BY TYPE (for course website)")
    print(f"{'='*60}")
    
    for type_num in [1, 2, 3, 4]:
        problems_in_type = categorized[type_num]
        print(f"\n{'#'*60}")
        print(f"TYPE {type_num}: {len(problems_in_type)} problems")
        print(f"{'#'*60}")
        
        if type_num == 1:
            print("Allowed: ∧I, ∧E, →I, →E")
            print("Must use: (any of the above)")
        elif type_num == 2:
            print("Allowed: Type 1 + ∨I, ∨E, ↔I, ↔E")
            print("Must use: ≥1 of {∨I, ∨E, ↔I, ↔E}")
        elif type_num == 3:
            print("Allowed: Type 2 + ¬I, ¬E")
            print("Must use: ≥1 of {¬I, ¬E}")
        elif type_num == 4:
            print("Allowed: Type 3 + IP, ⊥E (EFQ)")
            print("Must use: ≥1 of {IP, ⊥E}")
        
        print("\nProblems:")
        for i, problem in enumerate(problems_in_type, 1):
            print(f"\n{i}. Premises: {', '.join(problem['premises'])}")
            print(f"   Conclusion: {problem['conclusion']}")
            print(f"   Rules used: {', '.join(problem['rules_used'])}")
            print(f"   Proof length: {problem['proof_length']}")
    
    # Summary
    print(f"\n{'='*60}")
    print("📈 SUMMARY")
    print(f"{'='*60}")
    total_categorized = sum(len(categorized[t]) for t in [1,2,3,4])
    print(f"Total problems: {len(problems)}")
    print(f"Categorized: {total_categorized} ({total_categorized/len(problems)*100:.1f}%)")
    print(f"Uncategorized: {len(uncategorized)}")
    
    if uncategorized:
        print("\nUncategorized problems (rules don't match any type):")
        for problem in uncategorized:
            print(f"  ID: {problem['id']}, Rules: {problem['rules_used']}")


if __name__ == "__main__":
    main()
