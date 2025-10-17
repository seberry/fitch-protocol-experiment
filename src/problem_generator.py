"""Random TFL problem generator (TODO: integrate your existing code)"""

import random
from dataclasses import dataclass


@dataclass
class TFLProblem:
    '''A TFL logic problem'''
    problem_id: str
    premises: list[str]
    conclusion: str
    difficulty_depth: int
    difficulty_length: int


def generate_problem(difficulty: str = 'medium') -> TFLProblem:
    '''Generate a random TFL problem (placeholder).'''
    # TODO: Replace with your actual generator
    premises = ['Q', 'P → Q']
    conclusion = 'P → Q'
    
    return TFLProblem(
        problem_id=f'prob_{random.randint(1000, 9999)}',
        premises=premises,
        conclusion=conclusion,
        difficulty_depth=1,
        difficulty_length=2
    )
