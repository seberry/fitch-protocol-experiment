"""
ASCII Fitch Proof to JSON Converter

Converts messy ASCII Fitch proofs (with notes, annotations, etc.) 
to clean JSON format using an LLM API call.
"""

import json
from pathlib import Path
from litellm import completion


def load_conversion_prompt() -> str:
    """Load the ASCII-to-JSON conversion prompt template."""
    # Try multiple possible paths
    possible_paths = [
        Path(__file__).parent.parent / "prompts" / "ascii_to_json_conversion.md",
        Path("prompts/ascii_to_json_conversion.md"),
        Path("./prompts/ascii_to_json_conversion.md"),
    ]
    
    for prompt_path in possible_paths:
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"[DEBUG] Loaded prompt from: {prompt_path} ({len(content)} chars)")
                return content
    
    # If we get here, none of the paths worked
    raise FileNotFoundError(
        f"Could not find ascii_to_json_conversion.md. Tried:\n" + 
        "\n".join(f"  - {p}" for p in possible_paths)
    )

def convert_ascii_to_json(
    ascii_proof: str, 
    premises: list[str], 
    conclusion: str,
    model: str = "gpt-4"
) -> dict:
    """
    Converts ASCII Fitch proof to JSON format using LLM.
    
    Args:
        ascii_proof: The complete ASCII proof (possibly with notes/annotations)
        premises: List of premise formulas
        conclusion: Target conclusion formula
        model: LiteLLM model identifier (default: gpt-4)
    
    Returns:
        dict with keys: premises, conclusion, solution
        Example:
        {
            "premises": ["(A → B)", "A"],
            "conclusion": "B",
            "solution": [
                {"formula": "(A → B)", "justification": "Pr", "assumeno": 0},
                {"formula": "A", "justification": "Pr", "assumeno": 0},
                {"formula": "B", "justification": "→E 1, 2", "assumeno": 0}
            ]
        }
    
    Raises:
        ValueError: If LLM returns invalid JSON or conversion fails
    """
    # Load conversion prompt
    base_prompt = load_conversion_prompt()
    
    # Construct the full prompt
    full_prompt = f"""{base_prompt}

Now Convert This Proof:

Premises: {', '.join(premises)}
Conclusion: {conclusion}

{ascii_proof}

Return ONLY the JSON object, no additional text."""

    # Make API call
    try:
        response = completion(
            model=model,
            messages=[
                {"role": "user", "content": full_prompt}
            ],
            temperature=0  # Deterministic for conversion task
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON if wrapped in markdown code blocks
        if response_text.startswith("```"):
            # Remove markdown code fences
            lines = response_text.split('\n')
            # Remove first and last lines (the ``` markers)
            json_text = '\n'.join(lines[1:-1])
            # If first line was ```json, remove it
            if json_text.startswith('json'):
                json_text = '\n'.join(json_text.split('\n')[1:])
        else:
            json_text = response_text
        
        # Parse JSON
        result = json.loads(json_text)
        
        # Validate structure
        if not all(key in result for key in ['premises', 'conclusion', 'solution']):
            raise ValueError("Missing required keys in JSON output")
        
        if not isinstance(result['solution'], list):
            raise ValueError("'solution' must be a list")
        
        for i, line in enumerate(result['solution']):
            if not all(key in line for key in ['formula', 'justification', 'assumeno']):
                raise ValueError(f"Line {i} missing required keys")
        
        return result
        
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\nResponse: {response_text}")
    except Exception as e:
        raise ValueError(f"Conversion failed: {e}")


if __name__ == "__main__":
    # Test with a simple example
    test_ascii = """
1 | (A → B)              Premise
2 | A                    Premise
  |------------------------
3 | B                    →E 1, 2
"""
    
    result = convert_ascii_to_json(
        ascii_proof=test_ascii,
        premises=["(A → B)", "A"],
        conclusion="B"
    )
    
    print("Conversion successful!")
    print(json.dumps(result, indent=2))