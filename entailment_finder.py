import random
import itertools
from pysat.solvers import Glucose3
from pysat.formula import WCNF

# --- Configuration based on our specifications ---
ATOMS = ['P', 'Q', 'R', 'S']
CONNECTIVES = {
    'binary': ['&', '|', '->', '<->'],
    'unary': ['~']
}
MAX_DEPTH = 2
NUM_PREMISES_RANGE = (2, 3)
TARGET_ENTAILMENTS = 10

# A global mapping from atom names to integer variables for the SAT solver
ATOM_MAP = {atom: i + 1 for i, atom in enumerate(ATOMS)}

def generate_formula(depth):
    """Recursively generates a random well-formed formula string."""
    if depth <= 0 or random.random() < 0.25: # Chance to terminate early
        return random.choice(ATOMS)

    op_type = random.choice(['binary', 'unary'])

    if op_type == 'unary':
        op = random.choice(CONNECTIVES['unary'])
        sub_formula = generate_formula(depth - 1)
        return f"({op}{sub_formula})"
    else: # binary
        op = random.choice(CONNECTIVES['binary'])
        left = generate_formula(depth - 1)
        right = generate_formula(depth - 1)
        return f"({left} {op} {right})"

def formula_to_clauses(formula_str, cnf_writer, top_var_ref):
    """
    Parses a formula string and adds its CNF representation to a WCNF object.
    This is a simple parser that works for our generated formulas.
    It returns the integer literal representing the top-level formula.
    
    The 'top_var_ref' is a list containing the current top variable, e.g., [4],
    which allows us to modify it by reference.
    """
    formula_str = formula_str.strip()

    # Base case: It's just an atom
    if formula_str in ATOM_MAP:
        return ATOM_MAP[formula_str]

    # It's a complex formula, so it must be parenthesized
    if formula_str.startswith('(') and formula_str.endswith(')'):
        # Strip outer parentheses
        content = formula_str[1:-1]

        # Handle unary negation
        if content.startswith('~'):
            sub_formula = content[1:]
            sub_literal = formula_to_clauses(sub_formula, cnf_writer, top_var_ref)
            return -sub_literal

        # Handle binary connectives by finding the main operator
        balance = 0
        split_idx = -1
        for i, char in enumerate(content):
            if char == '(':
                balance += 1
            elif char == ')':
                balance -= 1
            elif char in ' &|-' and balance == 0:
                if content[i:i+3] == '<->':
                    split_idx = i
                    break
                if content[i:i+2] == '->':
                    split_idx = i
                    break
                if content[i] in ['&', '|']:
                    split_idx = i
                    break
        
        op_str = content[split_idx:].split()[0]
        left_str = content[:split_idx].strip()
        right_str = content[split_idx + len(op_str):].strip()

        # Recursively get literals for subformulas
        a = formula_to_clauses(left_str, cnf_writer, top_var_ref)
        b = formula_to_clauses(right_str, cnf_writer, top_var_ref)
        
        # *** THE FIX IS HERE ***
        # Instead of calling a method, we manually increment our own variable counter.
        top_var_ref[0] += 1
        v = top_var_ref[0]

        # Add clauses that define v <=> (a op b) using Tseitin transformation
        if op_str == '&':
            cnf_writer.append([-v, a])
            cnf_writer.append([-v, b])
            cnf_writer.append([-a, -b, v])
        elif op_str == '|':
            cnf_writer.append([-v, a, b])
            cnf_writer.append([-a, v])
            cnf_writer.append([-b, v])
        elif op_str == '->': # v <=> (~a | b)
            cnf_writer.append([-v, -a, b])
            cnf_writer.append([a, v])
            cnf_writer.append([-b, v])
        elif op_str == '<->': # v <=> (a <-> b)
            cnf_writer.append([-v, -a, b])
            cnf_writer.append([-v, -b, a])
            cnf_writer.append([a, b, v])
            cnf_writer.append([-a, -b, v])
        return v
    raise ValueError(f"Could not parse formula: {formula_str}")

def check_entailment(premises, conclusion):
    """Checks if premises entail the conclusion using a SAT solver."""
    wcnf = WCNF()
    # *** THE FIX IS HERE ***
    # Initialize our variable counter. It must be a list to be passed by reference.
    top_var_list = [len(ATOM_MAP)]
    
    # Add premises as hard clauses (they must be true)
    for p in premises:
        p_lit = formula_to_clauses(p, wcnf, top_var_list)
        wcnf.append([p_lit])

    # Add the NEGATION of the conclusion as a hard clause
    c_lit = formula_to_clauses(conclusion, wcnf, top_var_list)
    wcnf.append([-c_lit])
    
    # Check for unsatisfiability
    with Glucose3(bootstrap_with=wcnf.hard) as g:
        return not g.solve()

def check_contradiction(premises):
    """Checks if a set of premises is self-contradictory."""
    wcnf = WCNF()
    # *** THE FIX IS HERE ***
    top_var_list = [len(ATOM_MAP)]
    for p in premises:
        p_lit = formula_to_clauses(p, wcnf, top_var_list)
        wcnf.append([p_lit])
    
    with Glucose3(bootstrap_with=wcnf.hard) as g:
        return not g.solve()

def main():
    """Main function to find and print entailments."""
    print("--- Entailment Finder ---")
    print(f"Searching for {TARGET_ENTAILMENTS} valid, non-trivial entailments...")
    found_entailments = []
    
    attempts = 0
    while len(found_entailments) < TARGET_ENTAILMENTS:
        attempts += 1
        num_premises = random.choice(NUM_PREMISES_RANGE)
        # Use a set to avoid duplicate premises from the start
        premises = list(set(generate_formula(MAX_DEPTH) for _ in range(num_premises)))
        # Reroll if we got fewer premises than intended due to duplicates
        if len(premises) < num_premises:
            continue
        conclusion = generate_formula(MAX_DEPTH)

        # FILTER 1: Trivial Premise (conclusion is one of the premises)
        if conclusion in premises:
            continue

        # Check for validity
        try:
            is_valid = check_entailment(premises, conclusion)
        except (ValueError, IndexError): # Catch parsing errors
            continue 

        if is_valid:
            # FILTER 2: Contradictory Premises
            if check_contradiction(premises):
                continue
            
            # FILTER 3: Unnecessary Premises
            is_necessary = True
            if len(premises) > 1:
                for i in range(len(premises)):
                    subset_premises = premises[:i] + premises[i+1:]
                    if check_entailment(subset_premises, conclusion):
                        is_necessary = False
                        break
            if not is_necessary:
                continue

            # If all filters passed, we found a good one!
            found_entailments.append((premises, conclusion))
            print(f"\n--- Found Entailment #{len(found_entailments)} (on attempt {attempts}) ---")
            print("Premises:")
            for i, p in enumerate(premises):
                print(f"  {i+1}: {p}")
            print("Conclusion:")
            print(f"  ⊢ {conclusion}")
            attempts = 0 # Reset counter for next find

if __name__ == "__main__":
    main()