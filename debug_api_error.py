import litellm
litellm.set_verbose = True  # Turn on debug mode

from src.proof_solver import solve_proof

result = solve_proof(
    premises=['(P ∨ Q)', '(P → R)', '(Q → R)'],
    conclusion='R',
    condition='baseline',
    model='gpt-4'
)

print('Result:', result)
