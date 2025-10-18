"""Debug script to see what the LLM actually returns"""

from src.ascii_to_json import load_conversion_prompt
from litellm import completion
import json



# Load the prompt
base_prompt = load_conversion_prompt()

print("=== LENGTH OF LOADED PROMPT ===")
print(f"{len(base_prompt)} characters")

print("\n=== FIRST 500 CHARS OF PROMPT ===")
print(base_prompt[:500])

print("\n=== DOES IT CONTAIN 'solution'? ===")
print("'solution'" in base_prompt)
print("'steps'" in base_prompt)

