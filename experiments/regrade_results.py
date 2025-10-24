"""
Regrade Experiment Results

Re-validates proofs that failed due to pipeline issues but look correct.
Fixes the results CSV with proper validation.
"""

import sys
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# FIX: Add parent directory to path so we can import from src/
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ascii_to_json import convert_ascii_to_json
from src.proof_checker import check_proof



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
            return code_blocks[-1]  # Return the last code block
        return None
    except Exception as e:
        print(f"Error reading {conversation_file}: {e}")
        return None

def regrade_single_proof(problem_id: str, condition: str, premises: List[str], conclusion: str, conversation_file: str) -> Dict[str, Any]:
    """Regrade a single proof attempt."""
    print(f"Regrading {problem_id} - {condition}...")
    
    # Extract ASCII proof from conversation
    ascii_proof = extract_ascii_proof_from_conversation(conversation_file)
    
    if not ascii_proof:
        return {
            'problem_id': problem_id,
            'condition': condition,
            'regraded_solved': False,
            'regraded_error': 'Could not extract ASCII proof from conversation',
            'ascii_proof': None
        }
    
    try:
        # Convert ASCII to JSON
        json_proof = convert_ascii_to_json(
            ascii_proof=ascii_proof,
            premises=premises,
            conclusion=conclusion,
            model="deepseek/deepseek-chat"  # Use same model for consistency
        )
        
        # DEBUG: Print JSON proof structure
        print(f"  JSON proof has {len(json_proof.get('solution', []))} steps")
        
        # Validate proof
        validation = check_proof(json_proof)
        
        # DEBUG: Print validation result
        print(f"  Validation result: {validation}")
        
        return {
            'problem_id': problem_id,
            'condition': condition,
            'regraded_solved': validation['valid'],
            'regraded_error': None,
            'validation_issues': validation.get('issues', []),
            'ascii_proof': ascii_proof,
            'json_proof': json_proof
        }
        
    except Exception as e:
        print(f"  💥 Exception during regrading: {e}")
        return {
            'problem_id': problem_id,
            'condition': condition,
            'regraded_solved': False,
            'regraded_error': f'Regrading failed: {e}',
            'ascii_proof': ascii_proof
        }

def regrade_experiment_results(experiment_dir: str, problems_file: str):
    """Regrade all results in an experiment directory."""
    
    # Load problems
    with open(problems_file, 'r', encoding='utf-8') as f:
        problems = json.load(f)
    
    problem_lookup = {p['id']: p for p in problems}
    
    # Load results
    results_csv = Path(experiment_dir) / "results.csv"
    if not results_csv.exists():
        print(f"❌ Results CSV not found: {results_csv}")
        return
    
    df = pd.read_csv(results_csv)
    
    # Find failed proofs that might be fixable
    failed_proofs = df[df['solved'] == False]
    print(f"Found {len(failed_proofs)} failed proofs to potentially regrade")
    
    # NEW: Skip proofs that failed due to parsing/conversion issues
    skip_patterns = [
        'ASCII→JSON conversion failed',
        'ParseError',
        'JSONDecodeError',
        'conversion failed',
        'parse failed'
    ]
    
    fixable_failures = failed_proofs[
        ~failed_proofs['error'].str.contains('|'.join(skip_patterns), na=False)
    ]
    
    print(f"Skipping {len(failed_proofs) - len(fixable_failures)} proofs with parsing/conversion errors")
    print(f"Attempting to regrade {len(fixable_failures)} potentially fixable proofs")
    
    regraded_results = []
    
    for _, row in fixable_failures.iterrows():
        problem_id = row['problem_id']
        condition = row['condition']
        
        # Get problem details
        problem = problem_lookup.get(problem_id)
        if not problem:
            print(f"⚠️  Problem {problem_id} not found in problems file")
            continue
        
        # Check if conversation file exists
        conv_file = Path(experiment_dir) / "conversations" / f"{problem_id}_{condition}_conv.txt"
        if not conv_file.exists():
            print(f"⚠️  Conversation file not found: {conv_file}")
            continue
        
        # Regrade this proof
        regraded = regrade_single_proof(
            problem_id=problem_id,
            condition=condition,
            premises=problem['premises'],
            conclusion=problem['conclusion'],
            conversation_file=str(conv_file)
        )
        
        regraded_results.append(regraded)
        
        # Print result
        status = "✅ SOLVED" if regraded['regraded_solved'] else "❌ STILL FAILED"
        print(f"  {status}: {regraded.get('regraded_error', 'Validated successfully')}")
    
    
    # Create regraded results DataFrame
    if regraded_results:
        regraded_df = pd.DataFrame(regraded_results)
        
        # Merge with original results
        for _, regraded in regraded_df.iterrows():
            mask = (df['problem_id'] == regraded['problem_id']) & (df['condition'] == regraded['condition'])
            if regraded['regraded_solved']:
                df.loc[mask, 'solved'] = True
                df.loc[mask, 'error'] = ''
                df.loc[mask, 'validation_issues'] = '[]'
                if 'ascii_proof' in regraded and regraded['ascii_proof']:
                    df.loc[mask, 'ascii_proof'] = regraded['ascii_proof']
        
        # Save updated results
        regraded_csv = Path(experiment_dir) / "results_regraded.csv"
        df.to_csv(regraded_csv, index=False)
        
        # Print summary
        fixed_count = regraded_df['regraded_solved'].sum()
        print(f"\n🎉 REGRADING SUMMARY")
        print(f"Total regraded: {len(regraded_results)}")
        print(f"Fixed: {fixed_count}")
        print(f"Still failed: {len(regraded_results) - fixed_count}")
        print(f"Updated results saved to: {regraded_csv}")
        
        return df
    else:
        print("❌ No proofs were regraded")
        return None

def analyze_fixable_failures(experiment_dir: str):
    """Analyze which failures might be fixable by looking at conversation files."""
    
    results_csv = Path(experiment_dir) / "results.csv"
    df = pd.read_csv(results_csv)
    
    failed_proofs = df[df['solved'] == False]
    print(f"Analyzing {len(failed_proofs)} failed proofs...")
    
    potentially_fixable = []
    
    for _, row in failed_proofs.iterrows():
        problem_id = row['problem_id']
        condition = row['condition']
        
        conv_file = Path(experiment_dir) / "conversations" / f"{problem_id}_{condition}_conv.txt"
        if conv_file.exists():
            # Quick check: see if there's a proof in the conversation
            ascii_proof = extract_ascii_proof_from_conversation(str(conv_file))
            if ascii_proof and 'Pr' in ascii_proof and any(line.strip() for line in ascii_proof.split('\n') if '|' in line):
                potentially_fixable.append({
                    'problem_id': problem_id,
                    'condition': condition,
                    'has_proof': True,
                    'proof_length': len(ascii_proof)
                })
            else:
                potentially_fixable.append({
                    'problem_id': problem_id,
                    'condition': condition,
                    'has_proof': False
                })
        else:
            potentially_fixable.append({
                'problem_id': problem_id,
                'condition': condition,
                'has_proof': False,
                'reason': 'No conversation file'
            })
    
    fixable_df = pd.DataFrame(potentially_fixable)
    fixable_count = fixable_df['has_proof'].sum()
    
    print(f"\n🔍 FIXABILITY ANALYSIS")
    print(f"Total failed: {len(failed_proofs)}")
    print(f"Potentially fixable (have proofs): {fixable_count}")
    print(f"Not fixable (no proofs): {len(failed_proofs) - fixable_count}")
    
    if fixable_count > 0:
        print(f"\nPotentially fixable proofs:")
        for _, row in fixable_df[fixable_df['has_proof'] == True].iterrows():
            print(f"  {row['problem_id']} - {row['condition']}")
    
    return fixable_df

if __name__ == "__main__":
    experiment_dir = "data/results/medium_50_2025-10-23_191912"
    problems_file = "data/problems/50_medium_problems.json"
    
    # First analyze what's fixable
    print("🔍 Analyzing fixable failures...")
    fixable_df = analyze_fixable_failures(experiment_dir)
    
    if fixable_df['has_proof'].sum() > 0:
        print(f"\n🔄 Starting regrading...")
        regrade_experiment_results(experiment_dir, problems_file)
    else:
        print("❌ No fixable failures found")