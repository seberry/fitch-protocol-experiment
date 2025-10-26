# Experiment to Problem Bank Workflow

## 1. Generate Problems
```bash
python entailment_finder_interactive.py
# Choose bundle 2 (positive logic) for beginner problems
# Save output to data/problems/new_problems.json
```

# Generate problems and save with timestamp automatically
python entailment_finder_interactive.py > "data/problems/problems_$(date +%Y%m%d_%H%M%S).json"

# Or if you want to specify the bundle and see progress:
python entailment_finder_interactive.py | tee "data/problems/problems_$(date +%Y%m%d_%H%M%S).json"

## 2. Run Experiment
```bash
python experiments/run_experiment.py --problems data/problems/new_problems.json --output data/results/experiment_$(date +%Y%m%d)/
```

## 3. Harvest Protocol Solutions for Reuse in Student Quiz Banks
```bash
python experiments/harvest_experiment_solutions.py --experiment data/results/experiment_YYYYMMDD/ --output data/problems/fitch_problem_bank.jsonl
```

## 4. Test Quiz
```bash
python src/quiz_sampler.py
```

## Key Points:  
- Problems are now generated with proper symbols (∨, ∧, →, ↔, ¬)
- Only successful protocol solutions are added to the bank
- Quiz displays standardized symbols regardless of source
```

### Phase 4: Robust Harvest Script

Improve the harvest script to handle symbol standardization:

```python experiments/harvest_experiment_solutions.py
from src.symbol_standardizer import standardize_symbols, restore_internal_symbols

def process_problem_for_bank(problem_data, ascii_proof):
    """Prepare a problem for the bank with standardized symbols"""
    # Standardize premises and conclusion for display
    standardized_premises = [standardize_symbols(p) for p in problem_data['premises']]
    standardized_conclusion = standardize_symbols(problem_data['conclusion'])
    standardized_proof = standardize_symbols(ascii_proof)
    
    # But keep internal format for validation
    internal_premises = [restore_internal_symbols(p) for p in problem_data['premises']]
    internal_conclusion = restore_internal_symbols(problem_data['conclusion'])
    
    # Validate with internal symbols, store with standardized symbols
    return {
        'premises': standardized_premises,  # Display version
        'conclusion': standardized_conclusion,  # Display version  
        'ascii_solution': standardized_proof,  # Display version
        # ... other fields
    }