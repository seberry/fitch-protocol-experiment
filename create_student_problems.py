import json
from pathlib import Path

# Your student-level problems
problems = [
    {
        'id': 'student_001',
        'premises': ['(M → N)', '(M ↔ A)'],
        'conclusion': '((M ∧ N) ↔ A)',
        'difficulty': {'depth': 1, 'length': 3}
    },
    {
        'id': 'student_002',
        'premises': ['(P ∨ (Q ∧ R))', '(P ↔ R)'],
        'conclusion': 'R',
        'difficulty': {'depth': 1, 'length': 3}
    },
    {
        'id': 'student_003',
        'premises': ['((D ∧ E) ∨ (F ∧ G))'],
        'conclusion': '(E ∨ G)',
        'difficulty': {'depth': 1, 'length': 2}
    }
]

output_file = 'data/problems/student_problems.json'
Path(output_file).parent.mkdir(parents=True, exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(problems, f, indent=2, ensure_ascii=False)

print(f'Created {len(problems)} student-level problems')
print(f'\nTo run experiment:')
print(f'  python experiments/run_experiment.py --problems {output_file} --output data/results/student_results.csv')
