"""Quick test of protocol condition on test_001"""

from src.proof_solver import solve_proof
import json
from pathlib import Path

# Test problem
# premises = [ "(M → N)",
#       "(M ↔ A)"]
# conclusion = "((M ∧ N) ↔ A)"

premises = ["(R -> (S & P))",
      "(Q & (Q -> R))"]
conclusion = "((S -> Q) -> (Q & S))"


print("Testing protocol condition on medium difficulty problem...")
print(f"Premises: {', '.join(premises)}")
print(f"Conclusion: {conclusion}\n")

result = solve_proof(
    premises=premises,
    conclusion=conclusion,
    condition="protocol",
    model="gpt-4"
)

print(f"\nResult:")
print(f"  Solved: {result['solved']}")
print(f"  Time: {result['time_seconds']:.2f}s")
print(f"  Turns: {result['conversation_turns']}")
print(f"  Error: {result.get('error', 'None')}")

if not result['solved']:
    print(f"\n  Validation: {result.get('validation', {})}")
    print(f"\n  JSON proof: {json.dumps(result.get('json_proof', {}), indent=2)}")

# Save conversation to file
conv_dir = Path("data/results/conversations")
conv_dir.mkdir(parents=True, exist_ok=True)

conv_file = conv_dir / "quick_test_protocol.txt"
with open(conv_file, 'w', encoding='utf-8') as f:
    f.write("Quick Test - Protocol Condition\n")
    f.write("="*70 + "\n\n")
    
    for i, msg in enumerate(result['conversation_history'], 1):
        f.write(f"{'='*70}\n")
        f.write(f"TURN {i}: {msg['role'].upper()}\n")
        f.write(f"{'='*70}\n")
        f.write(f"{msg['content']}\n\n")

print(f"\nConversation saved to: {conv_file}")
print("\nTo view:")
print(f"  type {conv_file}")