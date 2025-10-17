# Usage Guide for Proof Validation

This section explains how to use the fitch-checker code to validate proofs programmatically.

## Input Format

The checker expects proofs in a **flat format with depth tracking**:
```json
{
  "premises": ["(A → B)", "A"],
  "conclusion": "B",
  "solution": [
    {"formula": "(A → B)", "justification": "Pr", "assumeno": 0},
    {"formula": "A", "justification": "Pr", "assumeno": 0},
    {"formula": "B", "justification": "→E 1, 2", "assumeno": 0}
  ]
}
```

### Field Specifications

- **`formula`**: Logical formula as string using symbols `→`, `∧`, `∨`, `↔`, `¬`, `⊥`
- **`justification`**: Rule abbreviation + citations (e.g., `"Pr"`, `"Hyp"`, `"→E 1, 2"`, `"→I 3-6"`)
- **`assumeno`**: Integer indicating subproof depth (0 = main proof, 1 = first subproof level, 2 = nested subproof, etc.)

### Valid Rule Abbreviations

- `Pr` - Premise
- `Hyp` - Assumption (hypothesis)
- `→I`, `→E` - Conditional introduction/elimination
- `∧I`, `∧E` - Conjunction introduction/elimination
- `∨I`, `∨E` - Disjunction introduction/elimination
- `↔I`, `↔E` - Biconditional introduction/elimination
- `¬I`, `¬E` - Negation introduction/elimination
- `⊥I`, `⊥E` - Contradiction introduction/elimination
- `R` - Reiteration
- `IP` - Indirect proof
- `LEM`/`TND` - Law of excluded middle
- `DNE` - Double negation elimination
- `DeM` - De Morgan's laws
- `MT` - Modus tollens
- `DS` - Disjunctive syllogism

## Using the Checker

### Step 1: Convert Flat Format to Nested Arrays

The checker's `check_proof()` function expects nested arrays, not the flat `assumeno` format. Use this conversion function:
```php
function buildNestedProof($flat_solution) {
    $main_proof = [];
    $stack = [&$main_proof];
    $previous_depth = 0;

    foreach ($flat_solution as $line) {
        $current_depth = $line->assumeno;
        $line_object = (object)['wffstr' => $line->formula, 'jstr' => $line->justification];

        // Exit subproofs if depth decreased
        if ($current_depth < $previous_depth) {
            for ($i = 0; $i < ($previous_depth - $current_depth); $i++) {
                array_pop($stack);
            }
        }

        // Handle consecutive subproofs at same depth
        if ($current_depth == $previous_depth && $current_depth > 0 && $line->justification == 'Hyp') {
            array_pop($stack);
        }

        $current_proof_level =& $stack[count($stack) - 1];

        // Enter new subproof if depth increased
        if ($current_depth > $previous_depth) {
            $new_subproof = []; 
            $current_proof_level[] = &$new_subproof; 
            $stack[] = &$new_subproof;
            $current_proof_level =& $stack[count($stack) - 1];
        }

        $current_proof_level[] = $line_object;
        $previous_depth = $current_depth;
    }

    return $main_proof;
}
```

### Step 2: Validate the Proof
```php
<?php
require 'vendor/fitch-checker/syntax.php'; 
require 'vendor/fitch-checker/proofs.php';

// Load proof data
$json_string = file_get_contents('proof.json');
$proof_data = json_decode($json_string);

// Convert to nested format
$nested_proof = buildNestedProof($proof_data->solution);

// Validate
$result = check_proof(
    $nested_proof, 
    count($proof_data->premises), 
    $proof_data->conclusion
);

// Check results
if (empty($result->issues) && $result->concReached) {
    echo "VALID\n";
    exit(0);
} else {
    echo "INVALID\n";
    print_r($result->issues);
    exit(1);
}
?>
```

## Complete Example

**Input file: `simple_proof.json`**
```json
{
  "premises": ["(A → B)"],
  "conclusion": "(A → (A → B))",
  "solution": [
    {"formula": "(A → B)", "justification": "Pr", "assumeno": 0},
    {"formula": "A", "justification": "Hyp", "assumeno": 1},
    {"formula": "(A → B)", "justification": "R 1", "assumeno": 1},
    {"formula": "(A → (A → B))", "justification": "→I 2-3", "assumeno": 0}
  ]
}
```

**Validation script: `validate.php`**
```php
<?php
require 'vendor/fitch-checker/syntax.php'; 
require 'vendor/fitch-checker/proofs.php';

function buildNestedProof($flat_solution) {
    // ... (function from above)
}

$json_string = file_get_contents('simple_proof.json');
$proof_data = json_decode($json_string);
$nested_proof = buildNestedProof($proof_data->solution);
$result = check_proof($nested_proof, count($proof_data->premises), $proof_data->conclusion);

if (empty($result->issues) && $result->concReached) {
    echo "✓ VALID\n";
} else {
    echo "✗ INVALID\n";
    print_r($result->issues);
}
?>
```

**Run:**
```bash
php validate.php
# Output: ✓ VALID
```

## Return Value Structure

The `check_proof()` function returns an object with:
```php
$result = (object)[
    'issues' => [],           // Array of error messages (empty if valid)
    'concReached' => true     // Whether the conclusion was reached
];
```

A proof is valid if and only if: `empty($result->issues) && $result->concReached`

## Common Errors

- **"Not well-formed"**: Formula syntax error (check symbols and parentheses)
- **"Cites unavailable line"**: Attempting to cite a line from a closed subproof
- **"Not a proper application of the rule"**: Rule misapplied for cited lines
- **"Cites too few/many line numbers"**: Wrong number of citations for the rule

## Technical Note

The checker internally converts the nested array structure to a flattened representation with location coordinates (e.g., `[3]`, `[4, 0]`, `[4, 2, 0]`). This coordinate system enables precise scope checking. However, users don't need to construct these coordinates manually—the `buildNestedProof()` function handles the conversion from the simpler `assumeno` format.