import random
import itertools
import sys
from pysat.solvers import Glucose3
from pysat.formula import WCNF    
from src.symbol_standardizer import standardize_symbols
import re



# --- Configuration ---
ATOMS = ['P', 'Q', 'R', 'S']
# NEW: Define all possible connectives here
ALL_CONNECTIVES = {
    'binary': ['&', '|', '->', '<->'],
    'unary': ['~']
}
MAX_DEPTH = 2
NUM_PREMISES_RANGE = (2, 3)
TARGET_ENTAILMENTS = 50

# A global mapping from atom names to integer variables for the SAT solver
ATOM_MAP = {atom: i + 1 for i, atom in enumerate(ATOMS)}


# MODIFIED: The function now takes a 'connectives' dictionary as an argument
def generate_formula(depth, connectives):
    """Recursively generates a random well-formed formula string using only the allowed connectives."""
    # The set of available operator types ('unary', 'binary') depends on the chosen bundle
    available_op_types = list(connectives.keys())

    # If we are at the bottom of recursion, or if there's a chance to terminate early
    if depth <= 0 or random.random() < 0.25:
        return random.choice(ATOMS)

    # If there are no connectives to choose from (e.g., a custom empty set), just return an atom
    if not available_op_types:
        return random.choice(ATOMS)

    op_type = random.choice(available_op_types)

    if op_type == 'unary':
        op = random.choice(connectives['unary'])
        sub_formula = generate_formula(depth - 1, connectives)
        return f"({op}{sub_formula})"
    else:  # binary
        op = random.choice(connectives['binary'])
        left = generate_formula(depth - 1, connectives)
        right = generate_formula(depth - 1, connectives)
        return f"({left} {op} {right})"


def formula_to_clauses(formula_str, cnf_writer, top_var_ref):
    """
    Parses a formula string and adds its CNF representation to a WCNF object.
    Updated: robustly handles multi-character operators using regex.
    """
    formula_str = formula_str.strip()
    if formula_str in ATOM_MAP:
        return ATOM_MAP[formula_str]
    if formula_str.startswith('(') and formula_str.endswith(')'):
        content = formula_str[1:-1].strip()
        if content.startswith('~'):
            sub_formula = content[1:]
            sub_literal = formula_to_clauses(sub_formula, cnf_writer, top_var_ref)
            return -sub_literal
        # Main operator outside parentheses (now using regex)
        match = re.search(r'^(.*)\s(<->|->|&|\|)\s(.*)$', content)
        if match:
            left_str, op_str, right_str = match.groups()
            left_str = left_str.strip()
            right_str = right_str.strip()
            a = formula_to_clauses(left_str, cnf_writer, top_var_ref)
            b = formula_to_clauses(right_str, cnf_writer, top_var_ref)
            top_var_ref[0] += 1
            v = top_var_ref[0]
            if op_str == '&': cnf_writer.extend([[-v, a], [-v, b], [-a, -b, v]])
            elif op_str == '|': cnf_writer.extend([[-v, a, b], [-a, v], [-b, v]])
            elif op_str == '->': cnf_writer.extend([[-v, -a, b], [a, v], [-b, v]])
            elif op_str == '<->': cnf_writer.extend([[-v, -a, b], [-v, -b, a], [a, b, v], [-a, -b, v]])
            return v
    raise ValueError(f"Could not parse formula: {formula_str}")
def check_entailment(premises, conclusion):
    """Checks if premises entail the conclusion using a SAT solver."""
    wcnf = WCNF()
    top_var_list = [len(ATOM_MAP)]
    for p in premises:
        p_lit = formula_to_clauses(p, wcnf, top_var_list)
        wcnf.append([p_lit])
    c_lit = formula_to_clauses(conclusion, wcnf, top_var_list)
    wcnf.append([-c_lit])
    with Glucose3(bootstrap_with=wcnf.hard) as g:
        return not g.solve()


def check_contradiction(premises):
    """Checks if a set of premises is self-contradictory."""
    wcnf = WCNF()
    top_var_list = [len(ATOM_MAP)]
    for p in premises:
        p_lit = formula_to_clauses(p, wcnf, top_var_list)
        wcnf.append([p_lit])
    with Glucose3(bootstrap_with=wcnf.hard) as g:
        return not g.solve()


def main():
    """Main function to find and print entailments."""
    
    # --- NEW: Interactive Menu ---
    print("--- Entailment Finder (Interactive) ---")
    
    print("Please select a bundle of connectives to use for generation:")
    print("  1. Basic Implication & Conjunction (&, ->)")
    print("  2. Positive Logic (&, ->, <->, v)")
    print("  3. Full TFL (all connectives including ~)")

    selected_connectives = {}
    while True:
        choice = input("Enter your choice (1, 2, or 3): ").strip()
        if choice == '1':
            selected_connectives = {'binary': ['&', '->']}
            print("Searching for problems using only '&' and '->'...")
            break
        elif choice == '2':
            # Note: The '|' character is used for 'v' in our generator
            selected_connectives = {'binary': ['&', '|', '->', '<->']}
            print("Searching for problems using only positive connectives...")
            break
        elif choice == '3':
            selected_connectives = ALL_CONNECTIVES
            print("Searching for problems using all TFL connectives...")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

    # --- Main Loop (now uses the selected connectives) ---
    print(f"Searching for {TARGET_ENTAILMENTS} valid, non-trivial entailments...")
    found_entailments = []
    attempts = 0
    while len(found_entailments) < TARGET_ENTAILMENTS:
        attempts += 1
        num_premises = random.choice(NUM_PREMISES_RANGE)
        # MODIFIED: Pass the chosen connectives to the generator
        premises = list(set(generate_formula(MAX_DEPTH, selected_connectives) for _ in range(num_premises)))
        if len(premises) < num_premises:
            continue
        conclusion = generate_formula(MAX_DEPTH, selected_connectives)

        # The filtering logic remains the same
        if conclusion in premises: continue
        try:
            if not check_entailment(premises, conclusion): continue
            if check_contradiction(premises): continue
            is_necessary = True
            if len(premises) > 1:
                for i in range(len(premises)):
                    subset_premises = premises[:i] + premises[i+1:]
                    if check_entailment(subset_premises, conclusion):
                        is_necessary = False; break
            if not is_necessary: continue
        except (ValueError, IndexError):
            continue

         # STANDARDIZE SYMBOLS: Convert to student-friendly format after SAT validation
        standardized_premises = [standardize_symbols(p) for p in premises]
        standardized_conclusion = standardize_symbols(conclusion)
        
        found_entailments.append((standardized_premises, standardized_conclusion))
        print(f"\n--- Found Entailment #{len(found_entailments)} (on attempt {attempts}) ---")
        print("Premises:")
        for i, p in enumerate(standardized_premises):
            print(f"  {i+1}: {p}")
        print("Conclusion:")
        print(f"  |= {standardized_conclusion}")
        attempts = 0# Fix Windows terminal encoding



if __name__ == "__main__":
    main()