"""
Rescue and regrade experiment results that were lost due to the csv_path bug.
Merges error results from the original output file with successful results from timestamped directory.
"""

import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

def rescue_experiment_results(experiment_dir: str, original_output: str):
    """Rescue results from the bug where error results were saved to wrong location."""
    
    timestamped_csv = Path(experiment_dir) / "results.csv"
    original_csv = Path(original_output)
    
    # Load both CSV files if they exist
    dfs = []
    
    if timestamped_csv.exists():
        df1 = pd.read_csv(timestamped_csv)
        print(f"Loaded {len(df1)} results from timestamped CSV")
        dfs.append(df1)
    
    if original_csv.exists():
        df2 = pd.read_csv(original_csv)
        # Filter for error results (the ones that were mis-saved)
        error_results = df2[df2['error'].str.contains('Exception', na=False)]
        print(f"Found {len(error_results)} error results in original CSV")
        dfs.append(error_results)
    
    if dfs:
        # Merge all results
        merged_df = pd.concat(dfs, ignore_index=True)
        
        # Save rescued results
        rescued_csv = Path(experiment_dir) / "results_rescued.csv"
        merged_df.to_csv(rescued_csv, index=False)
        print(f"✅ Saved {len(merged_df)} rescued results to: {rescued_csv}")
        
        return merged_df
    else:
        print("❌ No results found to rescue")
        return None

def analyze_rescued_results(rescued_df: pd.DataFrame):
    """Analyze the rescued results to understand performance."""
    
    print("\n📊 RESCUED RESULTS ANALYSIS")
    print("=" * 50)
    
    # Overall success rate
    total = len(rescued_df)
    solved = rescued_df['solved'].sum()
    print(f"Total attempts: {total}")
    print(f"Solved: {solved} ({solved/total*100:.1f}%)")
    print(f"Failed: {total - solved} ({(total-solved)/total*100:.1f}%)")
    
    # By condition
    print("\nBy condition:")
    for condition in rescued_df['condition'].unique():
        cond_df = rescued_df[rescued_df['condition'] == condition]
        cond_solved = cond_df['solved'].sum()
        print(f"  {condition}: {cond_solved}/{len(cond_df)} ({cond_solved/len(cond_df)*100:.1f}%)")
    
    # Error analysis
    errors = rescued_df[rescued_df['error'].notna() & (rescued_df['error'] != '')]
    if len(errors) > 0:
        print(f"\nError types:")
        for error_type in errors['error'].value_counts().head(5):
            print(f"  {error_type}")

if __name__ == "__main__":
    # Use your specific paths
    experiment_dir = "data/results/medium_50_2025-10-23_191912"
    original_output = "data/results/medium_50.csv"
    
    rescued_df = rescue_experiment_results(experiment_dir, original_output)
    
    if rescued_df is not None:
        analyze_rescued_results(rescued_df)