"""
Convert entailment_finder.py output to experimental problem format.

Parses the console output and creates structured JSON problems.
"""

import json
import re
from pathlib import Path


def parse_entailment_output(text: str) -> list:
    """
    Parse entailment_finder console output into problem list.
    
    Expected format:
    --- Found Entailment #1 (on attempt 123) ---
    Premises:
      1: (P → Q)
      2: Q
    Conclusion:
      |= R
    """
    problems = []
    
    # Split by entailment blocks
    blocks = re.split(r'--- Found Entailment #(\d+)', text)
    
    for i in range(1, len(blocks), 2):
        entailment_num = blocks[i]
        content = blocks[i + 1]
        
        # Extract premises
        premises = []
        premise_section = re.search(r'Premises:(.*?)Conclusion:', content, re.DOTALL)
        if premise_section:
            premise_lines = premise_section.group(1).strip().split('\n')
            for line in premise_lines:
                # Match format: "  1: (formula)"
                match = re.search(r'\d+:\s*(.+)', line.strip())
                if match:
                    premises.append(match.group(1).strip())
        
        # Extract conclusion - look for |= or ⊢
        conclusion = None
        conclusion_match = re.search(r'\|=\s*(.+)', content)
        if not conclusion_match:
            conclusion_match = re.search(r'⊢\s*(.+)', content)
        if conclusion_match:
            conclusion = conclusion_match.group(1).strip()
        
        if premises and conclusion:
            problems.append({
                'id': f'entailment_{entailment_num.zfill(3)}',
                'premises': premises,
                'conclusion': conclusion,
                'difficulty': {
                    'depth': len(premises),  # Rough proxy
                    'length': len(premises) + 1
                }
            })
    
    return problems


def main():
    """
    Two modes:
    1. Pipe entailment_finder output: python entailment_finder.py | python convert_entailments.py
    2. Or paste output interactively
    """
    import sys
    
    if not sys.stdin.isatty():
        # Reading from pipe
        text = sys.stdin.read()
    else:
        print("Paste entailment_finder.py output (Ctrl+Z then Enter on Windows when done):")
        print()
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        text = '\n'.join(lines)
    
    problems = parse_entailment_output(text)
    
    if not problems:
        print("Error: No entailments found in input")
        sys.exit(1)
    
    # Save to file
    output_file = "data/problems/generated_problems.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(problems, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created {len(problems)} problems in {output_file}")
    print(f"\nTo run experiment:")
    print(f"  python experiments/run_experiment.py --problems {output_file} --output data/results/generated_results.csv")


if __name__ == "__main__":
    main()