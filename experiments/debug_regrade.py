import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

# Fix import path - add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now import from src
from src.ascii_to_json import convert_ascii_to_json
from src.proof_checker import check_proof


def debug_single_proof(problem_id: str, premises: List[str], conclusion: str, ascii_proof: str):
    """Debug a single proof to see exactly what's happening in validation."""
    
    print(f"\n🔍 DEBUGGING {problem_id}")
    print("ASCII Proof:")
    print(ascii_proof)
    print("\n" + "="*50)
    
    try:
        # Step 1: ASCII to JSON conversion
        json_proof = convert_ascii_to_json(ascii_proof, premises, conclusion)
        print("✅ ASCII→JSON conversion succeeded")
        print(f"JSON structure: {len(json_proof.get('solution', []))} steps")
        
        # Step 2: Save to temp file and call PHP checker directly
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(json_proof, f, ensure_ascii=False)
            temp_path = f.name
        
        # Step 3: Call PHP checker directly
        php_script = Path("test_checker.php")
        result = subprocess.run(
            ['php', str(php_script), temp_path],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        print(f"PHP Checker Output:")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Return code:", result.returncode)
        
        # Clean up
        Path(temp_path).unlink(missing_ok=True)
        
        # Step 4: Analyze the output
        if "✓ VALID" in result.stdout:
            print("🎉 PROOF IS ACTUALLY VALID!")
            return True
        elif "INVALID" in result.stdout:
            print("❌ PROOF IS INVALID")
            # Extract the specific issues
            if "Issues found:" in result.stdout:
                issues_start = result.stdout.find("Issues found:")
                print("Validation issues:", result.stdout[issues_start:])
            return False
        else:
            print("⚠️  UNKNOWN CHECKER RESPONSE")
            return False
            
    except Exception as e:
        print(f"💥 DEBUGGING FAILED: {e}")
        return False

def debug_failed_proofs(experiment_dir: str, problems_file: str):
    """Debug all failed proofs to understand the validation issues."""
    
    with open(problems_file, 'r', encoding='utf-8') as f:
        problems = json.load(f)
    problem_lookup = {p['id']: p for p in problems}
    
    # Get list of conversation files for failed proofs
    conversations_dir = Path(experiment_dir) / "conversations"
    failed_conversations = []
    
    for conv_file in conversations_dir.glob("*_conv.txt"):
        # Extract problem_id and condition from filename
        parts = conv_file.stem.split('_')
        problem_id = '_'.join(parts[:-2])  # Handle IDs like "entailment_001"
        condition = parts[-2]
        
        # Read the proof from conversation
        ascii_proof = extract_ascii_proof_from_conversation(str(conv_file))
        if ascii_proof:
            problem = problem_lookup.get(problem_id)
            if problem:
                failed_conversations.append({
                    'problem_id': problem_id,
                    'condition': condition,
                    'premises': problem['premises'],
                    'conclusion': problem['conclusion'],
                    'ascii_proof': ascii_proof,
                    'conv_file': conv_file
                })
    
    print(f"Found {len(failed_conversations)} failed proofs to debug")
    
    valid_count = 0
    for proof_data in failed_conversations[:10]:  # Debug first 10
        is_valid = debug_single_proof(
            problem_id=proof_data['problem_id'],
            premises=proof_data['premises'],
            conclusion=proof_data['conclusion'],
            ascii_proof=proof_data['ascii_proof']
        )
        if is_valid:
            valid_count += 1
    
    print(f"\n📊 DEBUG SUMMARY: {valid_count}/{len(failed_conversations[:10])} proofs are actually valid")

def extract_ascii_proof_from_conversation(conversation_file: str) -> Optional[str]:
    """Extract the final ASCII proof from a conversation file."""
    try:
        with open(conversation_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the final proof (last code block)
        code_blocks = []
        in_code_block = False
        current_block = []
        
        for line in content.split('\n'):
            if line.strip().startswith('```') and not in_code_block:
                in_code_block = True
                current_block = []
            elif line.strip().startswith('```') and in_code_block:
                in_code_block = False
                code_blocks.append('\n'.join(current_block))
            elif in_code_block:
                current_block.append(line)
        
        if code_blocks:
            return code_blocks[-1]
        return None
    except Exception as e:
        print(f"Error reading {conversation_file}: {e}")
        return None

if __name__ == "__main__":
    experiment_dir = "data/results/medium_50_2025-10-23_191912"
    problems_file = "data/problems/50_medium_problems.json"
    debug_failed_proofs(experiment_dir, problems_file)