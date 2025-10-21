"""
LLM Proof Solver

Generates Fitch-style proofs using LLMs in three experimental conditions:
1. Baseline: One-shot "prove this"
2. Multi-shot Generic: Multiple turns with generic "step by step" prompting
3. Full Protocol: Staged Fitch protocol with ASCII skeletons
"""

import time
from pathlib import Path
from litellm import completion
from typing import Dict, List, Any
from src.ascii_to_json import convert_ascii_to_json
from src.proof_checker import check_proof

# Model configuration
DEFAULT_PROOF_MODEL = "gpt-4"
CONVERSION_MODEL = "gpt-4o-mini"

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
    # Initialize these FIRST so they exist for the except handler
    conversation = []
    start_time = time.time()
    
    try:
        premises_str = ", ".join(premises)
        fitch_rules = load_fitch_rules()
        
        initial_prompt = f"""{fitch_rules}

Let's prove this argument step by step using Fitch-style natural deduction.

Premises: {premises_str}
Conclusion: {conclusion}

Start by identifying what proof strategy might work. Then build the proof incrementally."""

        conversation.append({'role': 'user', 'content': initial_prompt})
        
        for turn in range(max_turns):
            response = completion(
                model=model,
                messages=conversation,
                temperature=0.7,
                timeout=timeout
            )
            
            assistant_msg = response.choices[0].message.content
            conversation.append({'role': 'assistant', 'content': assistant_msg})
            
            # Check if proof looks complete
            if "therefore" in assistant_msg.lower() or conclusion in assistant_msg:
                # Ask for final formatted proof
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
        
        # Ran out of turns
        return {
            'success': False,
            'ascii_proof': None,
            'conversation': conversation,
            'time_seconds': time.time() - start_time,
            'error': 'Max turns reached without completing proof'
        }
        
    except Exception as e:
        # CRITICAL: Always return a properly structured dict, even on error
        # conversation and start_time are guaranteed to exist now
        return {
            'success': False,
            'ascii_proof': None,
            'conversation': conversation,
            'time_seconds': time.time() - start_time,
            'error': f'Exception in solve_multi_shot: {type(e).__name__}: {str(e)}'
        }
       
def solve_protocol(premises: List[str], conclusion: str, model: str, max_stages: int = 10, timeout: int = 180) -> Dict[str, Any]:
    """
    Full protocol condition: Staged approach with skeleton → fill → verify.
    Uses both Fitch rules AND staged protocol instructions.
    """
    premises_str = ", ".join(premises)
    fitch_rules = load_fitch_rules()
    protocol_instructions = load_protocol_instructions()
    
    conversation = []
    start_time = time.time()
    
    # Stage 1: Skeleton planning
    stage1_prompt = f"""{fitch_rules}

{protocol_instructions}

Now prove this argument using the staged protocol:

Premises: {premises_str}
Conclusion: {conclusion}

STAGE 1 - Create the proof skeleton (or complete proof if simple):

First assess: Is this proof straightforward enough to complete in one step?
- If YES: Provide the complete proof directly in ASCII notation
- If NO: Create a skeleton with ellipses (...) for unfinished parts

If creating a skeleton:
- Write all premises
- Map subproof structure needed for the conclusion
- Use ellipses (...) for steps you haven't filled yet
- Show assumptions and intended conclusions

IMPORTANT: Provide EITHER skeleton OR complete proof, not both."""

    conversation.append({'role': 'user', 'content': stage1_prompt})
    
    try:
        response = completion(
            model=model,
            messages=conversation,
            temperature=0.7,
            timeout=timeout
        )
        
        assistant_msg = response.choices[0].message.content
        conversation.append({'role': 'assistant', 'content': assistant_msg})
        
        # Check if proof is already complete
        if not last_proof_has_ellipses(assistant_msg):
            # Skip staging, go straight to final clean extraction
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
            
            # Check if done after this stage
            if not last_proof_has_ellipses(assistant_msg):
                break
        
        # Final stage: Get clean proof
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
        
        return {
            'success': True,
            'ascii_proof': ascii_proof,
            'conversation': conversation,
            'time_seconds': time.time() - start_time,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'ascii_proof': None,
            'conversation': conversation,
            'time_seconds': time.time() - start_time,
            'error': str(e)
        }

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
        model="gpt-4"
    )
    
    print(f"\nSolved: {result['solved']}")
    print(f"Time: {result['time_seconds']:.2f}s")
    if result['solved']:
        print("✓ Proof validated successfully!")
    else:
        print(f"✗ Error: {result['error']}")