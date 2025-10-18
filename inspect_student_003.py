import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.proof_solver import solve_proof

result = solve_proof(
    premises=['((D ∧ E) ∨ (F ∧ G))'],
    conclusion='(E ∨ G)',
    condition='protocol',
    model='gpt-4'
)

print('='*60)
print('SOLVED:', result['solved'])
print('TIME:', result['time_seconds'], 'seconds')
print('='*60)
print('\nASCII PROOF:')
print(result['ascii_proof'])
print('\n' + '='*60)
if not result['solved']:
    print('ERROR:', result.get('error'))
    if result.get('validation'):
        print('VALIDATION ISSUES:', result['validation'].get('issues'))
        print('CONCLUSION REACHED:', result['validation'].get('concReached'))
