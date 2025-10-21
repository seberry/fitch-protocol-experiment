"""
Test that solve_multi_shot handles errors gracefully without returning None.

We'll mock the completion() function to simulate various failure modes.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent))

from src.proof_solver import solve_multi_shot


def test_case(name, premises, conclusion, mock_behavior):
    """Run a test case with mocked API calls."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    
    with patch('src.proof_solver.completion') as mock_completion:
        # Configure the mock
        mock_behavior(mock_completion)
        
        try:
            result = solve_multi_shot(
                premises=premises,
                conclusion=conclusion,
                model="test-model"
            )
            
            # Check result
            if result is None:
                print("❌ FAIL: Function returned None")
                return False
            elif not isinstance(result, dict):
                print(f"❌ FAIL: Function returned {type(result)}, not dict")
                return False
            else:
                print(f"✓ PASS: Returned a dict")
                
                # Check required keys
                required_keys = ['success', 'ascii_proof', 'conversation', 'time_seconds', 'error']
                missing_keys = [k for k in required_keys if k not in result]
                
                if missing_keys:
                    print(f"❌ FAIL: Missing keys: {missing_keys}")
                    return False
                else:
                    print(f"✓ PASS: All required keys present")
                    print(f"  success: {result['success']}")
                    print(f"  error: {result['error']}")
                    return True
                    
        except Exception as e:
            print(f"❌ FAIL: Uncaught exception: {type(e).__name__}: {e}")
            return False


# Test 1: API throws an exception immediately
def test_immediate_api_failure():
    def mock_behavior(mock_completion):
        mock_completion.side_effect = Exception("API connection failed")
    
    return test_case(
        "API throws exception on first call",
        premises=["P", "Q"],
        conclusion="(P & Q)",
        mock_behavior=mock_behavior
    )


# Test 2: Invalid premises (e.g., None in list)
def test_invalid_premises():
    def mock_behavior(mock_completion):
        # Won't even get here if premises_str fails
        pass
    
    return test_case(
        "Invalid premises (None in list)",
        premises=["P", None, "Q"],  # This should cause ", ".join() to fail
        conclusion="R",
        mock_behavior=mock_behavior
    )


# Test 3: API returns unexpected structure
def test_malformed_api_response():
    def mock_behavior(mock_completion):
        mock_response = MagicMock()
        mock_response.choices = []  # Empty choices list
        mock_completion.return_value = mock_response
    
    return test_case(
        "API returns empty choices list",
        premises=["P"],
        conclusion="Q",
        mock_behavior=mock_behavior
    )


# Test 4: load_fitch_rules() fails
def test_load_rules_failure():
    with patch('src.proof_solver.load_fitch_rules') as mock_load:
        mock_load.side_effect = FileNotFoundError("Rules file not found")
        
        return test_case(
            "load_fitch_rules() throws exception",
            premises=["P"],
            conclusion="Q",
            mock_behavior=lambda mock: None  # Won't get to completion()
        )


if __name__ == "__main__":
    print("Testing solve_multi_shot error handling...")
    print("This verifies the function never returns None\n")
    
    tests = [
        ("Immediate API failure", test_immediate_api_failure),
        ("Invalid premises", test_invalid_premises),
        ("Malformed API response", test_malformed_api_response),
        ("load_fitch_rules failure", test_load_rules_failure),
    ]
    
    results = []
    for test_name, test_func in tests:
        passed = test_func()
        results.append((test_name, passed))
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Function handles errors gracefully.")
    else:
        print("\n⚠️  Some tests failed. Function may still return None in edge cases.")