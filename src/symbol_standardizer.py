# Add symbol mapping to src/symbol_standardizer.py
SYMBOL_MAP = {
    '|': 'v',  # Use 'v' instead of '∨' for Windows compatibility
    '&': '&', 
    '->': '->',
    '<->': '<->',
    '~': '~'
}

def standardize_symbols(formula: str) -> str:
    """Convert internal symbols to student-friendly symbols"""
    for internal, student_friendly in SYMBOL_MAP.items():
        formula = formula.replace(internal, student_friendly)
    return formula

def restore_internal_symbols(formula: str) -> str:
    """Convert student symbols back to internal format for processing"""
    reverse_map = {v: k for k, v in SYMBOL_MAP.items()}
    for student_friendly, internal in reverse_map.items():
        formula = formula.replace(student_friendly, internal)
    return formula