# Skeleton-First Fitch Proof Protocol

## Why This Notation?

When proving complex arguments, natural language reasoning uses many words to track what would be captured efficiently in a few lines of structured notation. The sideways-T Fitch notation shows subproof structure visually through bars and indentation, making scope immediately obvious and preventing confusion about what's available to cite.

Think of this like the difference between describing algebra in words versus using symbolic notation—the symbols let you track more complexity in less space with less confusion.

## The Staged Protocol

Instead of trying to fill in a complete proof all at once, build it in stages:

### Stage 1: Plan Your Approach

You have flexibility in how to approach the proof:

**Option A: Solve it directly** 
If you can see the full proof path, just write it out completely.

**Option B: Sketch a partial solution with goals**
Write down the structure, marking what you still need to fill in:

- Mark gaps with `...` where you haven't worked out the steps yet
- Write your goal formulas at the line numbers where you'll prove them
- Use placeholder line numbers (n, m, p) - you'll fix them when filling in the steps
- Optionally add brief inline notes next to ellipses:
  - Restate the goal: `[Need: Q]`
  - Strategy hint: `[try →E with 1,3]`
  - Or both: `[Goal: derive B, use ∧E then →E]`
  - Whatever helps you think clearly

**For subproofs:**
When your target requires →I, ↔I, ¬I, ∨E, or IP, set up the subproof skeleton:
- Show the assumption line
- Mark the middle with `...` (optionally with goal/strategy notes)
- Write the target conclusion with placeholder line number
- Note which introduction rule you'll use

Example:
```
  |------------------------
k |  | A                 Hyp
  |  |--------------------
  |  | ...               [Goal: B, maybe use premise 2]
n |  | B
  |
p | (A → B)              →I k-n
```

**Key principle:** Keep your working visible - structure, goals, and any strategic ideas should be in the proof itself, not just in your head.

### Stage 2+: Fill OR Plan

Now work top-to-bottom through your proof. For each stage, look at the topmpost `...` gap you encounter and:

**Option A: Fill it** (if it looks straightforward)
- Replace the `...` with concrete proof steps
- Use working backward/forward strategies
- Update placeholder line numbers to actual numbers

**Option B: Add more planning** (if it looks complex)
- Instead of filling, add MORE structure
- Break it into smaller goals with more `...` markers
- If needed, create sub-subproofs with their own skeletons
- Add strategy notes to guide your future self
- This counts as progress! You're refining your strategy

**Critical insight:** Planning stages are VALID progress. If filling a gap looks hard, don't force it—just sketch what subgoals you'd need and come back later.


### Final Stage: Complete and Verify

- Replace all `...` with actual proof steps
- Replace placeholder line numbers with real ones
- Verify all assumptions are discharged
- Check that the final line is your target conclusion

## Working Backward and Forward Strategies

If stuck when filling in a `...', consier using standard strategies:

**Work Backward from your goal:**
- Goal is `A ∧ B`? Set up subgoals for `A` and `B`, plan to use ∧I
- Goal is `A → B`? Open subproof with `A`, aim for `B`, then use →I
- Goal is `A ↔ B`? Open TWO subproofs (A→B and B→A), then use ↔I
- Goal is `¬A`? Open subproof with `A`, aim for `⊥`, then use ¬I
- Goal is `A ∨ B`? Try to derive either `A` or `B`, then use ∨I

**Work Forward from what you have:**
- Have `A ∧ B`? Extract `A` or `B` using ∧E
- Have `A → B` and `A`? Get `B` using →E
- Have `A ↔ B` and `A`? Get `B` using ↔E (works both directions!)
- Have `A ∨ B`? Set up proof-by-cases using ∨E (two subproofs, both proving the same goal)
- Have `¬A` and `A`? Get `⊥` using ¬E


**If stuck:** Try indirect proof (IP) as a last resort—assume the negation of your goal and derive `⊥`.



## Escape Hatches

If you're stuck on a subproof:
- Write a note like "STUCK: need to derive X from Y, not seeing how"
- Move to the next subproof or add more planning structure
- Come back to stuck parts later
- Sometimes filling OTHER subproofs reveals new approaches

## Visual Discipline

The bars make scope OBVIOUS:
- Count the vertical bars to know your depth
- You can ONLY cite lines that are:
  - At your current level, OR
  - At an outer (less indented) level
- You CANNOT cite lines from closed or sibling subproofs

## Example: Complete Protocol Walkthrough

**Problem:** Prove `(P ∨ Q), (P → R), (Q → (R ∧ S)) ⊢ R`

**Stage 1 - Initial Skeleton:**
```
1 | (P ∨ Q)              Pr
2 | (P → R)              Pr
3 | (Q → (R ∧ S))        Pr
  |------------------------
4 |  | P                 Hyp
  |  |--------------------
  |  | ...
  |  | R
  |
  |  | Q                 Hyp
  |  |--------------------
  |  | ...
  |  | R
  |
10| R                    ∨E 1, ?, ?
```

We identified that to use the disjunction (line 1) and prove R, we need ∨E with two cases.

**Stage 2 - Fill first ellipsis:**
```
1 | (P ∨ Q)              Pr
2 | (P → R)              Pr
3 | (Q → (R  ∧ S))        Pr
  |------------------------
4 |  | P                 Hyp
  |  |--------------------
5 |  | R                 →E 2, 4
  |
6 |  | Q                 Hyp
  |  |--------------------
  |  | ...
  |  | R
  |
9 | R                    ∨E 1, 4-5, ?
```

First case was easy: we have P→R and P, so we get R by →E.

**Stage 3 - Fill second ellipsis:**
```
1 | (P ∨ Q)              Pr
2 | (P → R)              Pr
3 | (Q → (R  ∧ S))        Pr
  |------------------------
4 |  | P                 Hyp
  |  |--------------------
5 |  | R                 →E 2, 4
  |
6 |  | Q                 Hyp
  |  |--------------------
7 |  | R  ∧ S              →E 3, 6
8 |  | R                   ∧E 7
  |
8 | R                    ∨E 1, 4-5, 6-7
```

Done! Both cases prove R, so we conclude R by ∨E.

## Key Principles

1. **Notation is efficient** - Visual structure beats verbal description
2. **Skeletons first** - Map before filling
3. **Planning counts** - Adding structure without content is progress
4. **Top-to-bottom** - Fill outer subproofs before inner ones
5. **Ellipses are friends** - Mark "work to be done later"
6. **Scope is visual** - The bars show what you can cite
7. **Stuck is OK** - Note it and move on, come back later

## Common Mistakes to Avoid

- Trying to fill everything at once (use stages!)
- Citing lines from closed subproofs (check the bars!)
- Forgetting to discharge assumptions (every assumption needs an introduction rule)
- Random jumping (maintain top-to-bottom discipline)
- For ↔I: Citing intermediate conditionals instead of the subproof ranges directly
