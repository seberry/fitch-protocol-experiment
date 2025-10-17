# Fitch Checker Vendor Code

This directory contains unmodified source code from the `fitch-checker` project, used for proof validation.

- **Original Author**: Kevin C. Klement
- **Source Repository**: https://github.com/OpenLogicProject/fitch-checker
- **License**: GPL-3.0


# Notes on the fitch-checker Design

This note explains what I (seberry) take to be the core design of the fitch-checker code for a non-technical audience, focusing on how it represents and validates logical proofs. It was written by gemini.

## System Architecture

This checker uses a client-server model. The visual interface that a user sees in their web browser is built with JavaScript (syntax.js, proofs.js). When the "check proof" button is clicked, all the proof data is sent to a PHP script running on a server (proofs.php). This PHP script contains the "engine" that performs the actual logical validation.

## How a Proof is Represented

The system uses a clever method to handle the complex structure of Fitch-style proofs, especially the scope of subproofs.

### 1. The Nested Proof (Initial Structure)

Initially, the proof is represented as a nested array, where the structure of the arrays mimics the visual indentation of the proof. Each line is a basic object containing the formula string and justification string. A subproof is simply another array placed inside its parent array.

### 2. The Flattened Proof and Location Coordinates

To check the rules, the system first "flattens" this nested structure into a simple, single list of all the proof lines. However, it doesn't lose the depth information. As it flattens the proof, it assigns each line a location coordinate.

This coordinate is an array of numbers that acts like a precise address for that line within the original nested structure.

A line with location [3] is the 4th line in the main proof.

A line with location [4, 0] is the 1st line inside the subproof that begins at the 5th position of the main proof.

A line with location [4, 2, 0] is the 1st line of a subproof inside the subproof at [4].

This coordinate system is the key to how the checker handles all of its scope rules. It's more powerful than a simple depth number because it knows not just how deep a line is, but also which subproof branch it belongs to.

### 3. The Parsed Formula

A formula string like (P ∧ Q) is not useful for logical analysis. The parser (syntax.php) converts each string into a structured "logic tree" object. This allows the checker to see the formula's structure—for example, to identify that its main connective is ∧ and that its two parts are P and Q.

## The Validation Process

The main check_proof function in proofs.php executes in a clear sequence of steps:

1. Flatten and Assign Coordinates: It takes the nested proof and flattens it, assigning a unique $location coordinate to every line.

2. Parse Everything: It converts all formula strings and justification strings into the structured objects described above.

3. Check Scope and Availability: It loops through every line and uses the $location coordinates to ensure that any cited lines are in an open and accessible scope. This is where it rejects attempts to cite lines from closed subproofs.

4. Check Rules: Only after confirming that a line is well-formed and its citations are valid does it check if the rule of inference itself (e.g., Modus Ponens, Conjunction Introduction) was applied correctly.

By using the location coordinate system to verify scope before checking the logical rules, the system can robustly validate complex Fitch-style proofs.
