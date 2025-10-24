"""
ASCII Fitch Proof to JSON Converter

Hybrid approach:
1. Try deterministic parsing first (fast, free)
2. Fall back to LLM conversion on parse failure
"""

import json
import re
from pathlib import Path
from litellm import completion
from typing import Dict, List, Any, Optional
import sys

# FIX: Add parent directory to path so we can import from src/
sys.path.insert(0, str(Path(__file__).parent.parent))



class ParseError(Exception):
    """Raised when ASCII proof cannot be parsed deterministically."""
    pass


# ============================================================================
# DETERMINISTIC PARSER (new code)
# ============================================================================

def extract_code_block(text: str) -> str:
    """Extract content from markdown code fence, if present."""
    match = re.search(r'```(?:fitch|text|)?\n(.*?)\n```', text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def normalize_symbols(text: str) -> str:
    """
    Normalize logical symbols to Unicode expected by checker.
    
    Critical normalizations based on checker requirements:
    - & → ∧ (conjunction - checker is strict about this)
    - v → ∨ (disjunction, when clearly an operator)
    - -> → → (conditional, optional but cleaner)
    - <-> → ↔ (biconditional)
    - ~ → ¬ (negation)
    """
    replacements = {
        '&': '∧',
        '->': '→', 
        '<->': '↔',
        '~': '¬',
        '|': '∨'
    }
    
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    # Handle 'v' for disjunction (only when clearly an operator)
    # Pattern: space/start/( + v + space/end/)
    result = re.sub(r'(\s|\(|^)v(\s|\)|$)', r'\1∨\2', result)
    
    return result


def parse_proof_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single proof line.
    
    Expected format: "3 |  | M                 ∧E 3"
    
    Returns:
        {"formula": "M", "justification": "∧E 3", "assumeno": 1}
        or None if line is not a proof line (blank, separator, etc.)
    """
    # Skip blank lines
    if not line.strip():
        return None
    
    # Skip lines with only vertical bars and whitespace (spacing between subproofs)
    # These look like: "  |" or "  |  |"
    if re.match(r'^\s*(\|\s*)+$', line):
        return None

    # Skip separator lines (horizontal bars at any depth)
    # These look like: "  |------------------------"
    # or:              "  |  |--------------------"
    # Pattern: optional whitespace, any number of | and spaces, then only dashes
    if re.match(r'^\s*(\|\s*)*\|[\s\-]+$', line):
        return None
    
    # Match: line_num | [vertical bars] formula    justification
    # The formula and justification must be separated by at least 2 spaces
    match = re.match(r'^\s*(\d+)\s*\|((?:\s*\|)*)\s*([^\s].*?)\s{2,}(.+)$', line)
    
    if not match:
        raise ParseError(f"Cannot parse line: {line}")
    
    line_num = int(match.group(1))
    vertical_bars = match.group(2)
    formula = match.group(3).strip()
    justification = match.group(4).strip()
    
    # Count depth: number of | characters
    depth = vertical_bars.count('|')

    # Normalize symbols in both formula and justification
    formula = normalize_symbols(formula)
    justification = normalize_symbols(justification)
    
    return {
        'formula': formula,
        'justification': justification,
        'assumeno': depth
    }


def normalize_justification(just: str) -> str:
    """Normalize justification format (Premise → Pr, Assumption → Hyp)."""
    just = just.strip()
    
    if just.lower() in ['premise', 'prem']:
        return 'Pr'
    if just.lower() in ['assumption', 'hyp', 'hypothesis']:
        return 'Hyp'
    
    return just


def extract_premises_conclusion(text: str) -> tuple[List[str], Optional[str]]:
    """Extract premises and conclusion from surrounding text."""
    premises = []
    conclusion = None
    
    # Try to find premises line
    prem_match = re.search(r'Premises?:\s*(.+)', text, re.IGNORECASE)
    if prem_match:
        prem_str = prem_match.group(1)
        premises = [p.strip() for p in prem_str.split(',')]
    
    # Try to find conclusion line
    conc_match = re.search(r'Conclusion:\s*(.+)', text, re.IGNORECASE)
    if conc_match:
        conclusion = conc_match.group(1).strip()
    
    return premises, conclusion


def parse_ascii_proof_deterministic(
    ascii_text: str,
    premises: Optional[List[str]] = None,
    conclusion: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse clean ASCII Fitch proof to JSON deterministically.
    
    Raises ParseError if proof cannot be parsed.
    """
    # Extract from code block if wrapped
    proof_text = extract_code_block(ascii_text)
    
    # Try to extract premises/conclusion if not provided
    if premises is None or conclusion is None:
        extracted_prem, extracted_conc = extract_premises_conclusion(ascii_text)
        premises = premises or extracted_prem
        conclusion = conclusion or extracted_conc
    
    if not premises:
        raise ParseError("No premises found or provided")
    if not conclusion:
        raise ParseError("No conclusion found or provided")
    
    # FIX: Always normalize premises and conclusion to Unicode symbols
    premises = [normalize_symbols(p) for p in premises]
    conclusion = normalize_symbols(conclusion)
    
    # Parse each line
    solution = []
    for line in proof_text.split('\n'):
        parsed = parse_proof_line(line)
        if parsed:
            parsed['justification'] = normalize_justification(parsed['justification'])
            solution.append(parsed)
    
    if not solution:
        raise ParseError("No valid proof lines found")
    
    return {
        'premises': premises,
        'conclusion': conclusion,
        'solution': solution
    }

# ============================================================================
# LLM CONVERTER (existing code - keep as fallback)
# ============================================================================

def load_conversion_prompt() -> str:
    """Load the ASCII-to-JSON conversion prompt template."""
    possible_paths = [
        Path(__file__).parent.parent / "prompts" / "ascii_to_json_conversion.md",
        Path("prompts/ascii_to_json_conversion.md"),
        Path("./prompts/ascii_to_json_conversion.md"),
    ]
    
    for prompt_path in possible_paths:
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    raise FileNotFoundError(
        f"Could not find ascii_to_json_conversion.md. Tried:\n" + 
        "\n".join(f"  - {p}" for p in possible_paths)
    )


def convert_ascii_to_json_llm(
    ascii_proof: str, 
    premises: list[str], 
    conclusion: str,
    model: str = "gpt-4o-mini"
) -> dict:
    """Convert using LLM (original implementation)."""
    base_prompt = load_conversion_prompt()
    
    full_prompt = f"""{base_prompt}

Now Convert This Proof:

Premises: {', '.join(premises)}
Conclusion: {conclusion}

{ascii_proof}

Return ONLY the JSON object, no additional text."""

    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON if wrapped in markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            json_text = '\n'.join(lines[1:-1])
            if json_text.startswith('json'):
                json_text = '\n'.join(json_text.split('\n')[1:])
        else:
            json_text = response_text
        
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

# ============================================================================
# HYBRID CONVERTER (new main entry point)
# ============================================================================



def convert_ascii_to_json(
    ascii_proof: str,
    premises: List[str],
    conclusion: str,
    model: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    """
    Hybrid converter: Try deterministic parser first, fall back to LLM.
    
    This is the main entry point used by proof_solver.py.
    """
    try:
        # FIX: Normalize premises and conclusion symbols before parsing
        normalized_premises = [normalize_symbols(p) for p in premises]
        normalized_conclusion = normalize_symbols(conclusion)
        
        result = parse_ascii_proof_deterministic(
            ascii_proof, 
            normalized_premises, 
            normalized_conclusion
        )
        print("[ASCII→JSON] ✓ Deterministic parsing succeeded (free)")
        return result
        
    except ParseError as e:
        # Fall back to LLM
        print(f"[ASCII→JSON] ✗ Parse failed: {e}")
        print("[ASCII→JSON] → Using LLM fallback")
        return convert_ascii_to_json_llm(ascii_proof, premises, conclusion, model)



# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test with clean example
    test_ascii = """
1 | (M → N)              Pr
2 | (M ↔ A)              Pr
  |------------------------
3 |  | (M ∧ N)           Hyp
  |  |--------------------
4 |  | M                 ∧E 3
5 |  | A                 ↔E 2, 4
  |
6 |  | A                 Hyp
  |  |--------------------
7 |  | M                 ↔E 2, 6
8 |  | N                 →E 1, 7
9 |  | (M ∧ N)           ∧I 7, 8
  |
10| ((M ∧ N) ↔ A)        ↔I 3-5, 6-9
"""
    
    result = convert_ascii_to_json(
        ascii_proof=test_ascii,
        premises=["(M → N)", "(M ↔ A)"],
        conclusion="((M ∧ N) ↔ A)"
    )
    
    print("\n✓ Conversion successful!")
    print(json.dumps(result, indent=2, ensure_ascii=False))