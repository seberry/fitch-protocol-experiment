"""
Proof Checker Wrapper

Validates Fitch proofs by calling the PHP checker.
Takes flat JSON format (with assumeno) and validates it.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any

def check_proof(proof_json: dict) -> dict:
    """
    Validates a proof using the PHP checker.
    
    Args:
        proof_json: Flat format with assumeno, e.g.:
            {
                "premises": ["(A → B)", "A"],
                "conclusion": "B", 
                "solution": [
                    {"formula": "(A → B)", "justification": "Pr", "assumeno": 0},
                    ...
                ]
            }
    
    Returns:
        {
            'valid': True/False,
            'issues': [...],  # List of error messages (empty if valid)
            'concReached': True/False,
            'raw_output': '...'  # Full PHP output for debugging
        }
    """
    # Save proof to temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(proof_json, f, ensure_ascii=False)
        temp_path = f.name
    
    try:
        # Call the PHP checker
        php_script = Path(__file__).parent.parent / "test_checker.php"
        
        # Modify the PHP script call to use our temp file
        result = subprocess.run(
            ['php', str(php_script), temp_path],  # Pass temp_path as argument
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        output = result.stdout
        
        # DEBUG: Print raw PHP output
        print(f"  PHP Checker Raw Output: {output}")
        
        # Parse the output
        # Check for INVALID first (more specific)
        if "INVALID" in output or "? INVALID" in output:
            # Extract issues from output
            issues = []
            if "Issues found:" in output:
                issues_section = output.split("Issues found:")[1]
                # Try to parse issues (this is rough, PHP prints arrays)
                issues = [issues_section.strip()]
            
            conc_reached = "Conclusion reached: yes" in output
            
            return {
                'valid': False,
                'issues': issues,
                'concReached': conc_reached,
                'raw_output': output
            }
        elif "✓ VALID" in output or "? VALID" in output:
            return {
                'valid': True,
                'issues': [],
                'concReached': True,
                'raw_output': output
            }
        else:
            # DEBUG: More detailed unknown output handling
            print(f"  ⚠️ Unknown PHP output format")
            return {
                'valid': False,
                'issues': [f'Could not parse checker output: {output[:200]}...'],
                'concReached': False,
                'raw_output': output
            }
    
    except Exception as e:
        print(f"  💥 Exception in check_proof: {e}")
        return {
            'valid': False,
            'issues': [f'Checker exception: {e}'],
            'concReached': False,
            'raw_output': str(e)
        }
    
    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)



if __name__ == "__main__":
    # Test with a simple valid proof
    test_proof = {
        "premises": ["(A → B)", "A"],
        "conclusion": "B",
        "solution": [
            {"formula": "(A → B)", "justification": "Pr", "assumeno": 0},
            {"formula": "A", "justification": "Pr", "assumeno": 0},
            {"formula": "B", "justification": "→E 1, 2", "assumeno": 0}
        ]
    }
    
    print("Testing proof checker...")
    result = check_proof(test_proof)
    
    if result['valid']:
        print("✓ Proof is VALID!")
    else:
        print("✗ Proof is INVALID")
        print("Issues:", result['issues'])
    
    print("\nRaw output:")
    print(result['raw_output'])