# Fitch-Style Natural Deduction Rules

## Notation Format

Use ASCII "sideways T" notation for all proofs:

```
line_num | formula              justification

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
```

**Key notation elements:**
- Vertical bars (|) mark scope depth
- Horizontal bars (|----) mark assumption boundaries
- Indentation shows nesting level
- Each line: `line_num | formula    justification`

## Premises and Assumptions

**Premise (Pr):**
- Given facts at the start of the proof
- Written at main proof level (no indentation)
- Justification: `Pr`

Example:
```
1 | (P → Q)              Pr
2 | P                    Pr
```

**Assumption (Hyp):**
- Opens a new subproof
- Must eventually be discharged by an introduction rule
- Justification: `Hyp`
- Marked with horizontal bar below

Example:
```
3 |  | A                 Hyp
  |  |--------------------
```

## Logical Rules

### → (Conditional/Implication)

**→ Elimination (→E) / Modus Ponens:**
From `A → B` and `A`, infer `B`

Example:
```
1 | (P → Q)              Pr
2 | P                    Pr
3 | Q                    →E 1, 2
```

**→ Introduction (→I):**
To prove `A → B`:
1. Assume `A` (open subproof)
2. Derive `B` within that subproof
3. Close subproof and conclude `A → B`

Justification cites the subproof range: `→I start-end`

Example:
```
1 | P                    Pr
  |------------------------
2 |  | Q                 Hyp
  |  |--------------------
3 |  | P                 R 1
  |
4 | (Q → P)              →I 2-3
```

### ∧ (Conjunction/And)

**∧ Elimination (∧E):**
From `A ∧ B`, infer either `A` or `B`

Example:
```
1 | (P ∧ Q)              Pr
2 | P                    ∧E 1
3 | Q                    ∧E 1
```

**∧ Introduction (∧I):**
From `A` and `B`, infer `A ∧ B`

Example:
```
1 | P                    Pr
2 | Q                    Pr
3 | (P ∧ Q)              ∧I 1, 2
```

### ∨ (Disjunction/Or)

**∨ Introduction (∨I):**
From `A`, infer `A ∨ B` (for any `B`)
From `B`, infer `A ∨ B` (for any `A`)

Example:
```
1 | P                    Pr
2 | (P ∨ Q)              ∨I 1
3 | (Q ∨ P)              ∨I 1
```

**∨ Elimination (∨E) / Proof by Cases:**
To use `A ∨ B` to prove `C`:
1. Have `A ∨ B` available
2. Open subproof assuming `A`, derive `C`
3. Open another subproof assuming `B`, derive `C`
4. Conclude `C` at main level

Justification: `∨E disjunction_line, case1_range, case2_range`

Example:
```
1 | (P ∨ Q)              Pr
2 | (P → R)              Pr
3 | (Q → R)              Pr
  |------------------------
4 |  | P                 Hyp
  |  |--------------------
5 |  | R                 →E 2, 4
  |
6 |  | Q                 Hyp
  |  |--------------------
7 |  | R                 →E 3, 6
  |
8 | R                    ∨E 1, 4-5, 6-7
```

### ↔ (Biconditional/If and only if)

**↔ Elimination (↔E):**
From `A ↔ B` and `A`, infer `B`
From `A ↔ B` and `B`, infer `A`

Works in both directions (no need to first derive the conditionals).

Example:
```
1 | (P ↔ Q)              Pr
2 | P                    Pr
3 | Q                    ↔E 1, 2

4 | (P ↔ Q)              Pr
5 | Q                    Pr
6 | P                    ↔E 4, 5
```

**↔ Introduction (↔I):**
To prove `A ↔ B`:
1. Open subproof assuming `A`, derive `B` (proves A → B)
2. Open subproof assuming `B`, derive `A` (proves B → A)
3. Conclude `A ↔ B`

**CRITICAL:** Cite the TWO SUBPROOF RANGES directly.
**DO NOT** cite intermediate conditional lines.

Justification: `↔I range1, range2`

Example:
```
1 | P                    Pr
  |------------------------
2 |  | Q                 Hyp
  |  |--------------------
3 |  | P                 R 1
  |
4 |  | P                 Hyp
  |  |--------------------
5 |  | Q                 [derived somehow]
  |
6 | (P ↔ Q)              ↔I 2-3, 4-5    ← Cites subproofs, NOT any → lines
```

**WRONG:**
```
6 | (Q → P)              →I 2-3
7 | (P → Q)              →I 4-5
8 | (P ↔ Q)              ↔I 6, 7    ← DON'T DO THIS
```

### ¬ (Negation/Not)

**¬ Elimination (¬E) / Contradiction:**
From `A` and `¬A`, infer `⊥` (contradiction)

Example:
```
1 | P                    Pr
2 | ¬P                   Pr
3 | ⊥                    ¬E 1, 2
```

**¬ Introduction (¬I) / Proof by Contradiction:**
To prove `¬A`:
1. Assume `A` (open subproof)
2. Derive `⊥` (contradiction) within that subproof
3. Close subproof and conclude `¬A`

Justification: `¬I range`

Example:
```
1 | (P → Q)              Pr
2 | ¬Q                   Pr
  |------------------------
3 |  | P                 Hyp
  |  |--------------------
4 |  | Q                 →E 1, 3
5 |  | ⊥                 ¬E 4, 2
  |
6 | ¬P                   ¬I 3-5
```

### ⊥ (Contradiction/Falsum)

**⊥ Introduction (⊥I):**
From `A` and `¬A`, infer `⊥`
(Same as ¬E)

Example:
```
1 | P                    Pr
2 | ¬P                   Pr
3 | ⊥                    ⊥I 1, 2
```

**⊥ Elimination (⊥E) / Explosion / Ex Falso Quodlibet:**
From `⊥`, infer anything

Example:
```
1 | ⊥                    [derived somehow]
2 | Q                    ⊥E 1    ← Can conclude ANY formula
```

### Other Rules



**Indirect Proof (IP):**
To prove `A`:
1. Assume `¬A` (open subproof)
2. Derive `⊥` (contradiction) within that subproof
3. Close subproof and conclude `A`

Justification: `IP range`

Example:
```
  |------------------------
1 |  | ¬P                Hyp
  |  |--------------------
2 |  | [derivation]
3 |  | ⊥                 [contradiction reached]
  |
4 | P                    IP 1-3
```

**Law of Excluded Middle (LEM) / Tertium Non Datur (TND):**
For any formula `A`, you can assert `A ∨ ¬A`

Example:
```
1 | (P ∨ ¬P)             LEM
```

**Double Negation Elimination (DNE):**
From `¬¬A`, infer `A`

Example:
```
1 | ¬¬P                  Pr
2 | P                    DNE 1
```

**De Morgan's Laws (DeM):**
- From `¬(A ∧ B)`, infer `(¬A ∨ ¬B)`
- From `¬(A ∨ B)`, infer `(¬A ∧ ¬B)`
- From `(¬A ∨ ¬B)`, infer `¬(A ∧ B)`
- From `(¬A ∧ ¬B)`, infer `¬(A ∨ B)`

Example:
```
1 | ¬(P ∧ Q)             Pr
2 | (¬P ∨ ¬Q)            DeM 1
```

**Modus Tollens (MT):**
From `A → B` and `¬B`, infer `¬A`

Example:
```
1 | (P → Q)              Pr
2 | ¬Q                   Pr
3 | ¬P                   MT 1, 2
```

**Disjunctive Syllogism (DS):**
From `A ∨ B` and `¬A`, infer `B`
From `A ∨ B` and `¬B`, infer `A`

Example:
```
1 | (P ∨ Q)              Pr
2 | ¬P                   Pr
3 | Q                    DS 1, 2
```

## Citation Format

**Single lines:** Cite by number
- `∧E 1`
- `→E 1, 2`

**Subproof ranges:** Use hyphen (not en-dash or em-dash)
- `→I 3-6` (lines 3 through 6)
- `¬I 4-10`

**Multiple ranges:** Use comma-separated list
- `∨E 1, 4-5, 6-7` (line 1, range 4-5, range 6-7)
- `↔I 3-6, 7-9` (range 3-6, range 7-9)

## Scope Rules

**Critical:** You can only cite lines that are:
1. At the current scope level, OR
2. At any outer (less indented) scope level

**You CANNOT cite:**
- Lines from a closed subproof (once you've exited it)
- Lines from a sibling subproof
- Lines from inner (more indented) subproofs

Example of scope violation:
```
1 | P                    Pr
  |------------------------
2 |  | Q                 Hyp
  |  |--------------------
3 |  | R                 [something]
  |
4 |  | S                 Hyp
  |  |--------------------
5 |  | T                 R 3    ← ILLEGAL! Line 3 is in closed sibling subproof
```

## Summary of Common Patterns

**To prove A → B:** Assume A, derive B, then →I
**To prove A ∧ B:** Derive A and B separately, then ∧I
**To prove A ∨ B:** Derive either A or B, then ∨I
**To prove A ↔ B:** Prove A→B in one subproof, B→A in another, then ↔I (cite subproofs)
**To prove ¬A:** Assume A, derive ⊥, then ¬I
**To use A ∨ B:** Do proof by cases with ∨E
**To use A → B:** If you have A, apply →E to get B
**To use A ↔ B:** If you have A, apply ↔E to get B (or vice versa)
