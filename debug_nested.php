<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

require 'vendor/fitch-checker/syntax.php'; 
require 'vendor/fitch-checker/proofs.php';

function buildNestedProof($flat_solution) {
    $main_proof = [];
    $stack = [&$main_proof];
    $previous_depth = 0;

    echo "=== CONVERSION DEBUG ===\n";
    
    foreach ($flat_solution as $index => $line) {
        $current_depth = $line->assumeno;
        $line_object = (object)['wffstr' => $line->formula, 'jstr' => $line->justification];

        echo sprintf("\n[Line %d] depth=%d, formula='%s', just='%s'\n", 
            $index + 1, $current_depth, $line->formula, $line->justification);
        echo "  Stack size before: " . count($stack) . "\n";

        // CASE 1: Going shallower
        if ($current_depth < $previous_depth) {
            $levels_to_pop = $previous_depth - $current_depth;
            echo "  ACTION: Going shallower (pop $levels_to_pop levels)\n";
            for ($i = 0; $i < $levels_to_pop; $i++) {
                array_pop($stack);
            }
        }
        
        // CASE 2: Sibling subproof at same depth
        elseif ($current_depth == $previous_depth && 
                $current_depth > 0 && 
                $line->justification == 'Hyp') {
            echo "  ACTION: Sibling subproof detected (pop to parent)\n";
            array_pop($stack);
        }

        // Get current level
        $current_proof_level =& $stack[count($stack) - 1];

        // CASE 3: Starting new subproof
        if ($current_depth > $previous_depth ||
            ($current_depth == $previous_depth && 
             $current_depth > 0 && 
             $line->justification == 'Hyp')) {
            
            echo "  ACTION: Creating new subproof\n";
            $new_subproof = [];
            $current_proof_level[] = $new_subproof;
            $stack[] =& $current_proof_level[count($current_proof_level) - 1];
            $current_proof_level =& $stack[count($stack) - 1];
        }

        // Add line
        $current_proof_level[] = $line_object;
        echo "  Stack size after: " . count($stack) . "\n";
        
        $previous_depth = $current_depth;
    }

    echo "\n=== FINAL NESTED STRUCTURE ===\n";
    print_r($main_proof);
    echo "\n";

    return $main_proof;
}

// Get filename from command line or use default
$filename = $argc > 1 ? $argv[1] : 'test_disjunction.json';

echo "Reading file: $filename\n\n";

// Load JSON
$json_string = file_get_contents($filename);
$json_string = preg_replace('/^\xEF\xBB\xBF/', '', $json_string);

if ($json_string === false) {
    die("ERROR: Could not read $filename\n");
}

$proof_data = json_decode($json_string);
if ($proof_data === null) {
    die("ERROR: Could not parse JSON. Error: " . json_last_error_msg() . "\n");
}

echo "=== INPUT FLAT PROOF ===\n";
foreach ($proof_data->solution as $i => $line) {
    echo sprintf("Line %d: assumeno=%d, formula='%s', just='%s'\n",
        $i + 1, $line->assumeno, $line->formula, $line->justification);
}
echo "\n";

// Convert to nested format
$nested_proof = buildNestedProof($proof_data->solution);

// Now try to validate
echo "=== RUNNING CHECKER ===\n";
echo "Premises: " . implode(', ', $proof_data->premises) . "\n";
echo "Conclusion: " . $proof_data->conclusion . "\n\n";

$result = check_proof($nested_proof, count($proof_data->premises), $proof_data->conclusion);

echo "=== CHECKER RESULT ===\n";
if (empty($result->issues) && $result->concReached) {
    echo "✓ VALID\n";
    exit(0);
} else {
    echo "✗ INVALID\n";
    if (!empty($result->issues)) {
        echo "Issues:\n";
        print_r($result->issues);
    }
    echo "Conclusion reached: " . ($result->concReached ? "yes" : "no") . "\n";
    exit(1);
}
?>