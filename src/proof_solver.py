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


def load_protocol_prompt() -> str:
    """Load the full staged Fitch protocol from prompts/"""
    # For now, we'll embed it. Later we can load from file.
    return """You are a formal logic proof assistant using Fitch-style natural deduction.

IMPORTANT: Use this ASCII notation for all proofs:
- Vertical bars (|) mark scope
- Horizontal bars (|----) mark assumption boundaries
- Format: line_num | formula    justification

Example:
1 | (A → B)              Premise
2 | A                    Premise
  |------------------------
3 |  | P                 Assumption
  |  |--------------------
4 |  | (A → B)           R 1
5 |  | B                 →E 1, 2
  |
6 | (P → B)              →I 3-5

STAGED PROTOCOL:
Stage 1 - Skeleton: Map the proof structure with assumptions and intended conclusions
Stage 2+ - Fill one subproof at a time, top to bottom
Final - Verify all assumptions discharged and conclusion reached

Use standard rules: →I, →E, ∧I, ∧E, ∨I, ∨E, ↔I, ↔E, ¬I, ¬E, ⊥I, ⊥E, R, IP, LEM, etc.
"""


def solve_baseline(premises: List[str], conclusion: str, model: str, timeout: int = 60) -> Dict[str, Any]:
    """
    Baseline condition: Single prompt asking for complete proof.
    """
    premises_str = ", ".join(premises)
    
    prompt = f"""Prove the following argument using Fitch-style natural deduction.

Premises: {premises_str}
Conclusion: {conclusion}

Provide the complete proof in ASCII notation using this format:
1 | formula              justification
2 | formula              justification
  |------------------------
3 |  | formula           justification  (for subproofs)

Use proper Fitch notation with vertical bars for scope and horizontal bars for assumptions."""

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


def solve_multi_shot(premises: List[str], conclusion: str, model: str, max_turns: int = 5, timeout: int = 120) -> Dict[str, Any]:
    """
    Multi-shot generic condition: Multiple turns with "work step by step" but no protocol.
    """
    premises_str = ", ".join(premises)
    
    conversation = []
    start_time = time.time()
    
    # Initial prompt
    initial_prompt = f"""Let's prove this argument step by step using Fitch-style natural deduction.

Premises: {premises_str}
Conclusion: {conclusion}

Start by identifying what proof strategy might work. Then build the proof incrementally."""

    conversation.append({'role': 'user', 'content': initial_prompt})
    
    try:
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
        return {
            'success': False,
            'ascii_proof': None,
            'conversation': conversation,
            'time_seconds': time.time() - start_time,
            'error': str(e)
        }


def solve_protocol(premises: List[str], conclusion: str, model: str, max_stages: int = 10, timeout: int = 180) -> Dict[str, Any]:
    """
    Full protocol condition: Staged approach with skeleton → fill → verify.
    """
    premises_str = ", ".join(premises)
    protocol_instructions = load_protocol_prompt()
    
    conversation = []
    start_time = time.time()
    
    # Stage 1: Skeleton planning
    stage1_prompt = f"""{protocol_instructions}

Now prove this argument using the staged protocol:

Premises: {premises_str}
Conclusion: {conclusion}

STAGE 1 - Create the proof skeleton:
- Write out all premises
- Map the structure showing which subproofs you'll need
- Use ellipses (...) for steps you haven't filled yet
- Show assumptions and intended conclusions"""

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
        
        # Stage 2+: Fill subproofs
        for stage in range(2, max_stages):
            fill_prompt = f"""STAGE {stage} - Fill the next unfinished subproof.

Work top-to-bottom. Find the uppermost skeleton with ellipses (...) and fill it with concrete proof steps.
Keep deeper subproofs skeletal for now."""

            conversation.append({'role': 'user', 'content': fill_prompt})
            
            response = completion(
                model=model,
                messages=conversation,
                temperature=0.7,
                timeout=timeout
            )
            
            assistant_msg = response.choices[0].message.content
            conversation.append({'role': 'assistant', 'content': assistant_msg})
            
            # Check if complete (heuristic: no more ellipses)
            if '...' not in assistant_msg and conclusion in assistant_msg:
                break
        
        # Final stage: Get clean proof
        final_prompt = """FINAL STAGE - Provide the complete, clean proof with all line numbers and justifications finalized.
No ellipses, no placeholders, just the finished Fitch proof in ASCII notation."""

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


def solve_proof(premises: List[str], conclusion: str, condition: str, model: str = "gpt-4") -> Dict[str, Any]:
    """
    Main entry point: Generate and validate a proof.
    
    Args:
        premises: List of premise formulas
        conclusion: Target conclusion
        condition: One of ['baseline', 'multi_shot', 'protocol']
        model: LiteLLM model identifier
    
    Returns:
        {
            'condition': str,
            'model': str,
            'premises': [...],
            'conclusion': str,
            'solved': bool,
            'ascii_proof': str or None,
            'json_proof': dict or None,
            'validation': dict or None,
            'time_seconds': float,
            'conversation_turns': int,
            'error': str or None
        }
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
    
    if not result['success']:
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
            'error': result['error']
        }
    
    # Convert ASCII to JSON
    try:
        json_proof = convert_ascii_to_json(
            ascii_proof=result['ascii_proof'],
            premises=premises,
            conclusion=conclusion,
            model=model
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
            'error': f'Validation failed: {e}'
        }
    
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