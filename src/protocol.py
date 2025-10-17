"""Protocol template loader and utilities"""

from pathlib import Path


def load_protocol_template(stage: str = 'full') -> str:
    '''Load the Fitch protocol prompt template.'''
    prompts_dir = Path(__file__).parent.parent / 'prompts'
    
    if stage == 'baseline':
        template_file = prompts_dir / 'baseline.txt'
    elif stage == 'partial':
        template_file = prompts_dir / 'partial_protocol.txt'
    else:  # full
        template_file = prompts_dir / 'staged_protocol.txt'
    
    if not template_file.exists():
        raise FileNotFoundError(f'Protocol template not found: {template_file}')
    
    return template_file.read_text()
