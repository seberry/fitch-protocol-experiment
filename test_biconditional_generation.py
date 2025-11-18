from pysat.solvers import Glucose3
from pysat.formula import WCNF
import re 




# Atom mapping just as in your main code
ATOMS = ['P', 'Q', 'R']
ATOM_MAP = {atom: i + 1 for i, atom in enumerate(ATOMS)}

def formula_to_clauses(formula_str, cnf_writer, top_var_ref):
    formula_str = formula_str.strip()
    if formula_str in ATOM_MAP:
        return ATOM_MAP[formula_str]
    if formula_str.startswith('(') and formula_str.endswith(')'):
        content = formula_str[1:-1].strip()
        if content.startswith('~'):
            sub_formula = content[1:]
            sub_literal = formula_to_clauses(sub_formula, cnf_writer, top_var_ref)
            return -sub_literal
        # Find the main operator outside parentheses using regex
        # Matches: (... <-> ...) or (... -> ...) or (... & ...) or (... | ...)
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
    wcnf = WCNF()
    top_var_list = [len(ATOM_MAP)]
    for p in premises:
        p_lit = formula_to_clauses(p, wcnf, top_var_list)
        wcnf.append([p_lit])
    c_lit = formula_to_clauses(conclusion, wcnf, top_var_list)
    wcnf.append([-c_lit])
    with Glucose3(bootstrap_with=wcnf.hard) as g:
        return not g.solve()

if __name__ == "__main__":
    # Premises
    premises = ["(P <-> Q)", "(Q <-> R)"]
    # Conclusion
    conclusion = "(P <-> R)"

    entails = check_entailment(premises, conclusion)
    print(f"Premises: {premises}")
    print(f"Conclusion: {conclusion}")
    print(f"Does the SAT solver find that the premises entail the conclusion? {'YES' if entails else 'NO'}")