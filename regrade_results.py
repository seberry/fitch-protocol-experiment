"""
Re-grade experimental results with fixed checker.
Reads the CSV, re-converts ASCII proofs to JSON, re-validates with fixed checker.
"""
import pandas as pd
import json
import subprocess
import tempfile
from pathlib import Path
import sys

# Import your existing modules
sys.path.insert(0, str(Path(__file__).parent))
from src.ascii_to_json import convert_ascii_to_json
from src.proof_checker import check_proof

def regrade_csv(input_csv='data/results/student_results.csv', 
                output_csv='data/results/student_results_regraded.csv'):
    """
    Load previous results, re-validate all proofs using fixed checker, save new results.
    """
    print(f"Loading results from: {input_csv}")
    df = pd.read_csv(input_csv)
    
    print(f"\nFound {len(df)} proof attempts to re-grade")
    print(f"Breakdown by condition:")
    print(df['condition'].value_counts())
    print(f"\nOriginal results: {df['solved'].sum()} solved out of {len(df)}")
    print("\n" + "="*60)
    
    # Add new columns for regraded results
    df['solved_regraded'] = False
    df['validation_issues_regraded'] = ''
    df['regrade_error'] = ''
    
    # Re-grade each proof
    for idx, row in df.iterrows():
        print(f"\n[{idx+1}/{len(df)}] {row['problem_id']} ({row['condition']})...", end=' ')
        
        # Skip if no ASCII proof
        if pd.isna(row.get('ascii_proof')) or row['ascii_proof'] == '':
            print("❌ No ASCII proof")
            df.at[idx, 'regrade_error'] = 'No ASCII proof available'
            continue
        
        try:
            # Parse premises from string representation
            premises = json.loads(row['premises'].replace('\\u2192', '→')
                                                  .replace('\\u2194', '↔')
                                                  .replace('\\u2227', '∧')
                                                  .replace('\\u2228', '∨')
                                                  .replace('\\u00ac', '¬')
                                                  .replace('\\u22a5', '⊥'))
            
            conclusion = row['conclusion']
            ascii_proof = row['ascii_proof']
            
            # Step 1: Convert ASCII to JSON (LLM-based)
            print("converting...", end=' ')
            json_proof = convert_ascii_to_json(ascii_proof, premises, conclusion)
            
            # Step 2: Validate with FIXED checker
            print("validating...", end=' ')
            validation_result = check_proof(json_proof, premises, conclusion)
            
            # Store results
            is_valid = validation_result['valid']
            df.at[idx, 'solved_regraded'] = is_valid
            df.at[idx, 'validation_issues_regraded'] = json.dumps(validation_result.get('issues', []))
            
            if is_valid:
                print("✓ VALID")
            else:
                print(f"✗ INVALID ({len(validation_result.get('issues', []))} issues)")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            df.at[idx, 'regrade_error'] = str(e)
            continue
    
    # Summary statistics
    print("\n" + "="*60)
    print("REGRADING COMPLETE")
    print("="*60)
    print(f"Original:  {df['solved'].sum()}/{len(df)} solved ({df['solved'].mean()*100:.1f}%)")
    print(f"Regraded:  {df['solved_regraded'].sum()}/{len(df)} solved ({df['solved_regraded'].mean()*100:.1f}%)")
    
    # Show changes by condition
    print(f"\nBreakdown by condition:")
    for condition in df['condition'].unique():
        subset = df[df['condition'] == condition]
        orig = subset['solved'].sum()
        new = subset['solved_regraded'].sum()
        total = len(subset)
        print(f"  {condition:15s}: {orig}/{total} → {new}/{total}")
    
    # Save results
    print(f"\nSaving regraded results to: {output_csv}")
    df.to_csv(output_csv, index=False)
    print("Done!")

if __name__ == "__main__":
    regrade_csv()