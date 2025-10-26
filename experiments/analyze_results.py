"""
Analyze experimental results from CSV.

Provides summary statistics and visualizations.
"""

import pandas as pd
import sys
import io
from pathlib import Path
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def analyze_results(csv_file: str):
    """Analyze and summarize experimental results."""
    
    df = pd.read_csv(csv_file)
    
    print("="*60)
    print("EXPERIMENT RESULTS SUMMARY")
    print("="*60)
    
    # Overall stats
    print(f"\nTotal runs: {len(df)}")
    print(f"Unique problems: {df['problem_id'].nunique()}")
    print(f"Conditions tested: {', '.join(df['condition'].unique())}")
    print(f"Model: {df['model'].iloc[0]}")
    
    # Success rates by condition
    print("\n" + "="*60)
    print("SUCCESS RATES BY CONDITION")
    print("="*60)
    
    by_condition = df.groupby('condition').agg({
        'solved': ['sum', 'count', 'mean'],
        'time_seconds': 'mean',
        'conversation_turns': 'mean'
    }).round(2)
    
    for condition in df['condition'].unique():
        condition_data = df[df['condition'] == condition]
        solved = condition_data['solved'].sum()
        total = len(condition_data)
        success_rate = (solved / total) * 100
        avg_time = condition_data['time_seconds'].mean()
        avg_turns = condition_data['conversation_turns'].mean()
        
        print(f"\n{condition.upper()}:")
        print(f"  Success: {solved}/{total} ({success_rate:.1f}%)")
        print(f"  Avg time: {avg_time:.2f}s")
        print(f"  Avg turns: {avg_turns:.1f}")
    
    # Problem-by-problem breakdown
    print("\n" + "="*60)
    print("PROBLEM-BY-PROBLEM BREAKDOWN")
    print("="*60)
    
    for problem_id in sorted(df['problem_id'].unique()):
        problem_data = df[df['problem_id'] == problem_id]
        print(f"\n{problem_id}:")
        
        for condition in ['baseline', 'multi_shot', 'protocol']:
            row = problem_data[problem_data['condition'] == condition]
            if len(row) > 0:
                solved = "✓" if row['solved'].iloc[0] else "✗"
                time = row['time_seconds'].iloc[0]
                print(f"  {condition:12s}: {solved} ({time:.2f}s)")
    
    # Failures analysis
    failures = df[df['solved'] == False]
    if len(failures) > 0:
        print("\n" + "="*60)
        print(f"FAILURES ({len(failures)} total)")
        print("="*60)
        
        for _, failure in failures.iterrows():
            print(f"\n{failure['problem_id']} - {failure['condition']}:")
            print(f"  Time: {failure['time_seconds']:.2f}s")
            if failure['error']:
                print(f"  Error: {failure['error']}")
    
    # Comparative statistics
    print("\n" + "="*60)
    print("COMPARATIVE ANALYSIS")
    print("="*60)
    
    baseline = df[df['condition'] == 'baseline']
    protocol = df[df['condition'] == 'protocol']
    
    if len(baseline) > 0 and len(protocol) > 0:
        baseline_rate = baseline['solved'].mean() * 100
        protocol_rate = protocol['solved'].mean() * 100
        improvement = protocol_rate - baseline_rate
        
        print(f"\nProtocol vs Baseline:")
        print(f"  Success rate difference: {improvement:+.1f} percentage points")
        
        if baseline['solved'].sum() > 0:
            baseline_time = baseline[baseline['solved'] == True]['time_seconds'].mean()
            protocol_time = protocol[protocol['solved'] == True]['time_seconds'].mean()
            time_diff = protocol_time - baseline_time
            print(f"  Time difference (solved only): {time_diff:+.2f}s")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze experiment results')
    parser.add_argument('--results', type=str, required=True,
                       help='Path to results CSV file')
    
    args = parser.parse_args()
    
    if not Path(args.results).exists():
        print(f"Error: {args.results} not found")
        sys.exit(1)
    
    analyze_results(args.results)