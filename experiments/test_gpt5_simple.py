# experiments/test_gpt5_simple.py
import os, litellm
from litellm import completion

print("Testing GPT-5 access...")
print(f"API key set: {'OPENAI_API_KEY' in os.environ}")

try:
    litellm._turn_on_debug()
except Exception:
    pass

MODEL = "gpt-5"  # <-- use real id, not 'gpt5'

resp = completion(
    model=MODEL,
    messages=[{"role": "user", "content": "Say 'hello' exactly."}],
    temperature=1,    # GPT-5 chat quirk: only 1 is supported
    timeout=60,
    drop_params=True, # belt & suspenders
)

print(resp.choices[0].message.content)