# experiments/extract_conversation_solutions.py
"""
Extract successful protocol solutions from conversation files and validate them.
"""
import json
import re
from pathlib import Path
from datetime import datetime

def extract_proof_from_conversation(conv_file: str):
    """Extract the final proof from a conversation file"""
    with open(conv_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for the final proof in the last assistant turn
    turns = content.split('============================================================\n')
    for turn in reversed(turns):
        if turn.startswith('Turn') and 'assistant' in turn:
            # Extract proof between triple backticks
            proof_match = re.search(r'```(?:\w+)?\n(.*?)\n```', turn, re.DOTALL)
            if proof_match:
                return proof_match.group(1).strip()
    return None

def extract_conversation_solutions(experiment_dir: str, output_file: str):
    """Extract and validate solutions from conversation files"""
    conv_dir = Path(experiment_dir) / "conversations"
    protocol_files = list(conv_dir.glob("*_protocol_conv.txt"))
    
    harvested_problems = []
    
    for conv_file in protocol_files:
        problem_id = conv_file.name.split('_')[1]  # Extract entailment_001, etc.
        
        # Get the original problem from the 50_medium_problems.json
        original_problem = get_original_problem(problem_id)
        if not original_problem:
            continue
            
        # Extract proof from conversation
        ascii_proof = extract_proof_from_conversation(str(conv_file))
        if not ascii_proof:
            continue
            
        # Validate the proof
        validation_result = validate_proof(original_problem, ascii_proof)
        if validation_result.get('valid'):
            # Create bank entry
            bank_entry = create_bank_entry(original_problem, ascii_proof, validation_result)
            harvested_problems.append(bank_entry)
    
    # Append to problem bank
    if harvested_problems:
        with open(output_file, 'a', encoding='utf-8') as f:
            for entry in harvested_problems:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    return len(harvested_problems)