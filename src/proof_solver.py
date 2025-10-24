"""
LLM Proof Solver

Generates Fitch-style proofs using LLMs in three experimental conditions:
1. Baseline: One-shot "prove this"
2. Multi-shot Generic: Multiple turns with generic "step by step" prompting
3. Full Protocol: Staged Fitch protocol with ASCII skeletons
"""

import time
from pathlib import Path
import litellm
from typing import Dict, List, Any
from src.ascii_to_json import convert_ascii_to_json
from src.proof_checker import check_proof
from litellm import completion
#itellm.set_verbose = True

# Model configuration
DEFAULT_PROOF_MODEL = "deepseek/deepseek-chat"
CONVERSION_MODEL ="deepseek/deepseek-chat"

def last_proof_has_ellipses(response_text: str) -> bool:
    """Check if the LAST proof in the response has ellipses."""
    import re
    code_blocks = re.findall(r'```(?:.*?)\n(.*?)```', response_text, re.DOTALL)
    
    if not code_blocks:
        return '...' in response_text
    
    return '...' in code_blocks[-1]

def load_fitch_rules() -> str:
    """Load universal Fitch notation rules (used in all conditions)."""
    rules_path = Path(__file__).parent.parent / "prompts" / "fitch_rules_prompt.md"
    
    if not rules_path.exists():
        raise FileNotFoundError(f"Fitch rules not found at: {rules_path}")
    
    with open(rules_path, 'r', encoding='utf-8') as f:
        return f.read()


def load_protocol_instructions() -> str:
    """Load staged protocol instructions (used only in protocol condition)."""
    protocol_path = Path(__file__).parent.parent / "prompts" / "protocol_instructions.md"
    
    if not protocol_path.exists():
        raise FileNotFoundError(f"Protocol instructions not found at: {protocol_path}")
    
    with open(protocol_path, 'r', encoding='utf-8') as f:
        return f.read()
    
def solve_baseline(premises: List[str], conclusion: str, model: str, timeout: int = 60) -> Dict[str, Any]:
    """
    Baseline condition: Single prompt asking for complete proof.
    Uses Fitch notation rules but no staged protocol.
    """
    premises_str = ", ".join(premises)
    fitch_rules = load_fitch_rules()
    
    prompt = f"""{fitch_rules}

Prove the following argument using Fitch-style natural deduction.

Premises: {premises_str}
Conclusion: {conclusion}

Provide the complete proof in ASCII notation."""

    start_time = time.time()
    
    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            timeout=timeout
        )
        
        ascii_proof = response.choices[0].message.content
        elapsed = time.time() - start_time
        
        return {
            'success': True,
            'ascii_proof': ascii_proof,
            'conversation': [
                {'role': 'user', 'content': prompt},
                {'role': 'assistant', 'content': ascii_proof}
            ],
            'time_seconds': elapsed,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'ascii_proof': None,
            'conversation': [],
            'time_seconds': time.time() - start_time,
            'error': str(e)
        }

def solve_multi_shot(premises, conclusion, model, max_turns=5, timeout=120):
    """Multi-shot generic condition."""
    # ... existing code ...
    
    for turn in range(max_turns):
        response = completion(
            model=model,
            messages=conversation,
            temperature=0.7,
            timeout=timeout
        )
        
        assistant_msg = response.choices[0].message.content
        conversation.append({'role': 'assistant', 'content': assistant_msg})
        
        # IMPROVED: Better completion detection
        completion_signals = [
            "proof is complete" in assistant_msg.lower(),
            "proof is finished" in assistant_msg.lower(), 
            "no next step" in assistant_msg.lower(),
            "no further step" in assistant_msg.lower(),
            "qed" in assistant_msg.lower(),
            "done" in assistant_msg.lower() and len(assistant_msg) < 500,
            # NEW: Look for explicit completion markers
            "this completes the proof" in assistant_msg.lower(),
            "the proof is done" in assistant_msg.lower(),
            "we have reached the conclusion" in assistant_msg.lower(),
            # NEW: Check if last code block looks complete (has conclusion)
            conclusion in assistant_msg and any(line.strip().endswith(conclusion) for line in assistant_msg.split('\n') if '|' in line),
            # NEW: Check for final line with conclusion
            any(f"| {conclusion}" in line for line in assistant_msg.split('\n'))
        ]

        # NEW: Also check if the proof looks structurally complete
        if looks_like_complete_proof(assistant_msg, conclusion):
            completion_signals.append(True)

        if any(completion_signals):
            # Only ask for final formatting if proof isn't already clean
            if not has_clean_ascii_proof(assistant_msg):
                conversation.append({
                    'role': 'user',
                    'content': 'Please provide the complete proof in clean ASCII Fitch notation.'
                })
                
                response = completion(
                    model=model,
                    messages=conversation,
                    temperature=0.7,
                    timeout=timeout
                )
                
                ascii_proof = response.choices[0].message.content
                conversation.append({'role': 'assistant', 'content': ascii_proof})
            else:
                # Extract the clean proof directly
                ascii_proof = extract_clean_proof(assistant_msg)
            
            return {
                'success': True,
                'ascii_proof': ascii_proof,
                'conversation': conversation,
                'time_seconds': time.time() - start_time,
                'error': None
            }
        
        # Continue prompting
        conversation.append({
            'role': 'user',
            'content': 'Continue. What\'s the next step?'
        })

# NEW: Helper functions for better completion detection
def looks_like_complete_proof(text: str, conclusion: str) -> bool:
    """Check if the text contains a proof that looks structurally complete."""
    lines = text.split('\n')
    proof_lines = [line for line in lines if '|' in line and line.strip()]
    
    if len(proof_lines) < 2:
        return False
    
    # Check if last proof line contains the conclusion
    last_proof_line = proof_lines[-1]
    return conclusion in last_proof_line and 'Pr' not in last_proof_line

def has_clean_ascii_proof(text: str) -> bool:
    """Check if text already contains a clean ASCII proof."""
    # Look for well-formatted proof with proper structure
    lines = text.split('\n')
    has_premises = any('Pr' in line for line in lines)
    has_bars = any('---' in line for line in lines)
    has_numbered_lines = sum(1 for line in lines if re.match(r'^\d+\s*\|', line)) >= 3
    
    return has_premises and has_bars and has_numbered_lines

def extract_clean_proof(text: str) -> str:
    """Extract the clean proof from assistant response."""
    # Try to get the last code block
    code_blocks = re.findall(r'```(?:.*?)\n(.*?)```', text, re.DOTALL)
    if code_blocks:
        return code_blocks[-1]
    
    # If no code blocks, try to extract proof lines
    lines = text.split('\n')
    proof_lines = []
    in_proof = False
    
    for line in lines:
        if re.match(r'^\d+\s*\|', line) or '---' in line:
            in_proof = True
            proof_lines.append(line)
        elif in_proof and line.strip() == '':
            proof_lines.append(line)
        elif in_proof and not re.match(r'^\d+\s*\|', line) and '---' not in line:
            break
    
    return '\n'.join(proof_lines) if proof_lines else text
      
def solve_protocol(premises: List[str], conclusion: str, model: str, max_stages: int = 10, timeout: int = 180) -> Dict[str, Any]:
    # ... existing code ...
    
    # IMPROVED: Check if proof is already complete (better detection)
    if proof_looks_complete(assistant_msg, conclusion):
        # Skip staging, go straight to final clean extraction
        if not has_clean_ascii_proof(assistant_msg):
            final_prompt = """Please provide the complete proof in clean ASCII notation."""
            conversation.append({'role': 'user', 'content': final_prompt})
            
            response = completion(
                model=model,
                messages=conversation,
                temperature=0.7,
                timeout=timeout
            )
            
            ascii_proof = response.choices[0].message.content
            conversation.append({'role': 'assistant', 'content': ascii_proof})
        else:
            ascii_proof = extract_clean_proof(assistant_msg)
        
        return {
            'success': True,
            'ascii_proof': ascii_proof,
            'conversation': conversation,
            'time_seconds': time.time() - start_time,
            'error': None
        }
    
    # Stage 2+: Fill subproofs
    for stage in range(2, max_stages):
        fill_prompt = f"""STAGE {stage} - Fill the next unfinished subproof.

Work top-to-bottom. Find the uppermost skeleton with ellipses (...) and fill it with concrete proof steps.
Keep deeper subproofs skeletal for now.

If all subproofs are complete, just say "All complete - proof is finished." """

        conversation.append({'role': 'user', 'content': fill_prompt})
        
        response = completion(
            model=model,
            messages=conversation,
            temperature=0.7,
            timeout=timeout
        )
        
        assistant_msg = response.choices[0].message.content
        conversation.append({'role': 'assistant', 'content': assistant_msg})
        
        # IMPROVED: Check if done after this stage (better detection)
        if proof_looks_complete(assistant_msg, conclusion):
            break

# NEW: Improved completion detection function
def proof_looks_complete(text: str, conclusion: str) -> bool:
    """Check if proof appears complete using multiple signals."""
    # Check for explicit completion statements
    completion_phrases = [
        "proof is complete",
        "proof is finished", 
        "all complete",
        "no further steps",
        "qed",
        "done",
        "this completes the proof",
        "the proof is done",
        "we have reached the conclusion"
    ]
    
    if any(phrase in text.lower() for phrase in completion_phrases):
        return True
    
    # Check structural completeness
    if not last_proof_has_ellipses(text) and looks_like_complete_proof(text, conclusion):
        return True
    
    return False

# Keep the existing function but improve it
def last_proof_has_ellipses(response_text: str) -> bool:
    """Check if the LAST proof in the response has ellipses."""
    import re
    code_blocks = re.findall(r'```(?:.*?)\n(.*?)```', response_text, re.DOTALL)
    
    if not code_blocks:
        return '...' in response_text
    
    last_block = code_blocks[-1]
    return '...' in last_block

def solve_proof(
    premises: List[str],
    conclusion: str,
    condition: str,
    model: str = DEFAULT_PROOF_MODEL
) -> Dict[str, Any]:
    """
    Main entry point for proof solving.
    
    Args:
        premises: List of premise formulas
        conclusion: Target conclusion formula
        condition: 'baseline', 'multi_shot', or 'protocol'
        model: LLM model to use
    
    Returns:
        Dict with keys: condition, model, premises, conclusion, solved, 
        ascii_proof, json_proof, validation, time_seconds, 
        conversation_turns, conversation_history, error
    """
    # Generate proof based on condition
    if condition == 'baseline':
        result = solve_baseline(premises, conclusion, model)
    elif condition == 'multi_shot':
        result = solve_multi_shot(premises, conclusion, model)
    elif condition == 'protocol':
        result = solve_protocol(premises, conclusion, model)
    else:
        raise ValueError(f"Unknown condition: {condition}")
    
    # Early exit if proof generation failed
    if not result['success']:
        return {
            'condition': condition,
            'model': model,
            'premises': premises,
            'conclusion': conclusion,
            'solved': False,
            'ascii_proof': result.get('ascii_proof'),
            'json_proof': None,
            'validation': None,
            'time_seconds': result['time_seconds'],
            'conversation_turns': len(result['conversation']) // 2,
            'conversation_history': result['conversation'],
            'error': result['error']
        }
    
    # Convert ASCII to JSON
    try:
        json_proof = convert_ascii_to_json(
            ascii_proof=result['ascii_proof'],
            premises=premises,
            conclusion=conclusion,
            model=CONVERSION_MODEL
        )
    except Exception as e:
        return {
            'condition': condition,
            'model': model,
            'premises': premises,
            'conclusion': conclusion,
            'solved': False,
            'ascii_proof': result['ascii_proof'],
            'json_proof': None,
            'validation': None,
            'time_seconds': result['time_seconds'],
            'conversation_turns': len(result['conversation']) // 2,
            'conversation_history': result['conversation'],
            'error': f'ASCII→JSON conversion failed: {e}'
        }
    
    # Validate proof
    try:
        validation = check_proof(json_proof)
    except Exception as e:
        return {
            'condition': condition,
            'model': model,
            'premises': premises,
            'conclusion': conclusion,
            'solved': False,
            'ascii_proof': result['ascii_proof'],
            'json_proof': json_proof,
            'validation': None,
            'time_seconds': result['time_seconds'],
            'conversation_turns': len(result['conversation']) // 2,
            'conversation_history': result['conversation'],
            'error': f'Validation failed: {e}'
        }
    
    # Success! Return everything
    return {
        'condition': condition,
        'model': model,
        'premises': premises,
        'conclusion': conclusion,
        'solved': validation['valid'],
        'ascii_proof': result['ascii_proof'],
        'json_proof': json_proof,
        'validation': validation,
        'time_seconds': result['time_seconds'],
        'conversation_turns': len(result['conversation']) // 2,
        'conversation_history': result['conversation'],
        'error': None
    }

if __name__ == "__main__":
    # Test with simple example
    print("Testing proof solver (baseline condition)...")
    result = solve_proof(
        premises=["(A → B)", "A"],
        conclusion="B",
        condition="baseline",
        model="deepseek/deepseek-chat" 
    )
    
    print(f"\nSolved: {result['solved']}")
    print(f"Time: {result['time_seconds']:.2f}s")
    if result['solved']:
        print("✓ Proof validated successfully!")
    else:
        print(f"✗ Error: {result['error']}")