<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

require 'vendor/fitch-checker/syntax.php'; 
require 'vendor/fitch-checker/proofs.php';

function buildNestedProof($flat_solution) {
    $main_proof = [];
    $stack = [&$main_proof];
    $previous_depth = 0;

    foreach ($flat_solution as $line) {
        $current_depth = $line->assumeno;
        $line_object = (object)['wffstr' => $line->formula, 'jstr' => $line->justification];

        if ($current_depth < $previous_depth) {
            for ($i = 0; $i < ($previous_depth - $current_depth); $i++) {
                array_pop($stack);
            }
        }

        if ($current_depth == $previous_depth && $current_depth > 0 && $line->justification == 'Hyp') {
            array_pop($stack);
        }

        $current_proof_level =& $stack[count($stack) - 1];

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

// Load and parse JSON
$json_string = file_get_contents('test_simple.json');

// Remove BOM if present
$json_string = preg_replace('/^\xEF\xBB\xBF/', '', $json_string);

if ($json_string === false) {
    die("ERROR: Could not read test_simple.json\n");
}

$proof_data = json_decode($json_string);
if ($proof_data === null) {
    die("ERROR: Could not parse JSON. Error: " . json_last_error_msg() . "\n");
}

echo "Testing proof checker...\n";
echo "Premises: " . implode(', ', $proof_data->premises) . "\n";
echo "Conclusion: " . $proof_data->conclusion . "\n\n";

$nested_proof = buildNestedProof($proof_data->solution);

echo "Nested proof structure:\n";
print_r($nested_proof);
echo "\n";

$result = check_proof($nested_proof, count($proof_data->premises), $proof_data->conclusion);

if (empty($result->issues) && $result->concReached) {
    echo "? VALID - Proof checker accepts this format!\n";
    exit(0);
} else {
    echo "? INVALID - Issues found:\n";
    print_r($result->issues);
    echo "\nConclusion reached: " . ($result->concReached ? "yes" : "no") . "\n";
    exit(1);
}
?>
