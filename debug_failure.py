import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.proof_solver import solve_proof

result = solve_proof(
    premises=['(P → Q)', '(Q → R)', 'P'],
    conclusion='R',
    condition='multi_shot',
    model='gpt-4'
)

print('Solved:', result['solved'])
print('\nASCII Proof:')
print(result['ascii_proof'])
print('\nValidation:')
print(result['validation'])
