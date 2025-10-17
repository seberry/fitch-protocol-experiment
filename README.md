# Fitch Protocol Experiment

**Goal:** Test whether structured visual notation scaffolds LLM reasoning on complex formal logic proofs.

## The Core Idea

When humans do long division, the visual structure (the notation itself) helps us not lose our place. This project explores whether the same principle applies to LLMs doing formal proofs: does a disciplined, staged notation system help LLMs succeed at multi-step proofs that would otherwise be too complex?

### The Hypothesis

A "skeleton-first" Fitch protocol—where you map proof structure before filling details—will improve LLM success rates on challenging TFL/FOL proofs compared to unstructured attempts.

**Why this might work:**
- Separates structure mapping from detail work
- Creates visual checkpoints (each stage is a complete snapshot)
- Mirrors good human proof-planning habits  
- Provides explicit scope markers (vertical bars = "you're inside this assumption")
- Breaks overwhelming complexity into manageable chunks

## The Protocol (Quick Version)

**Stage 1 - Skeleton Planning:**
- Copy premises, draw outer proof bar
- For each connective needing subproofs (→I, ↔I, ∨E, ¬I, etc.):
  - Open a subproof skeleton with assumption, ellipsis (\...\), and target conclusion
  - Label with placeholder rules (→I ?, ?)
- Nothing is proved yet—only structure is mapped

**Stage 2-N - Fill Top-to-Bottom:**
- Locate the topmost unfinished subproof
- Replace its ellipsis with concrete steps
- Keep deeper subproofs skeletal
- Optional: create sub-skeletons for complex cases (planning-only stages are valid)

**Final Stage - Closure:**
- Confirm every assumption discharged
- Replace all \?\ placeholders with actual line ranges
- Verify final line matches conclusion

**Key notation:** ASCII "Sideways T" convention
- Horizontal bar marks assumption start
- Vertical bar shows scope of that assumption
- Indentation = nesting depth

[See \prompts/staged_protocol.txt\ for full protocol details]

## What We're Building (MVP)

An experimental system to test this hypothesis:

### Three Conditions to Compare
1. **Baseline** - Zero-shot: "Prove this problem"
2. **Partial Protocol** - Give notation guide, but no staged enforcement
3. **Full Protocol** - Actual stage-by-stage prompting with the skeleton→fill→verify workflow

*Note: We're open to exploring other experimental contrasts as we learn more.*

### Architecture

\\\
fitch-protocol-experiment/
├── data/
│   ├── problems/          # Generated TFL problems (git-tracked)
│   └── results/           # Experimental CSVs (gitignored)
├── src/
│   ├── problem_generator.py   # Creates random TFL problems
│   ├── proof_solver.py         # LLM wrapper for 3 conditions
│   ├── ascii_to_json.py        # Parser: ASCII Fitch → JSON
│   ├── proof_checker.py        # Validates proofs via existing checker
│   └── protocol.py             # Loads prompt templates
├── experiments/
│   ├── run_experiment.py       # Main experimental loop
│   └── analyze_results.py      # Statistical analysis
├── prompts/
│   └── staged_protocol.txt     # The full protocol document
└── tests/                      # Validation tests
\\\

### Tech Stack
- **Python 3.10+** for everything
- **LiteLLM** - Unified API for OpenAI/Anthropic/others
- **pandas** - Data analysis
- **Jupyter** - Interactive exploration
- **pytest** - Testing (optional for MVP)

### Metrics We'll Track

For each proof attempt, log:
- \problem_id\: Unique identifier
- \condition\: baseline / partial_protocol / full_protocol  
- \difficulty_depth\: Max subproof nesting
- \difficulty_length\: Number of connectives
- \solved\: True/False (valid proof produced?)
- \steps_used\: Number of LLM calls
- \error_type\: syntax / rule_misuse / timeout / none
- \	ime_sec\: Duration

**Success threshold:** Full protocol shows meaningful improvement over baseline on medium+ difficulty problems.

## Current Status

- [x] Protocol designed and manually tested on hard problems
- [x] Have existing problem generator (random TFL)
- [x] Have existing proof checker (JSON-based, open source)
- [x] Project structure created
- [ ] ASCII→JSON parser implementation
- [ ] LLM solver wrapper for 3 conditions
- [ ] Experimental runner
- [ ] Statistical analysis script
- [ ] Run pilot experiment (20 problems × 3 conditions)

## Quick Start

\\\powershell
# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Set up API keys (if not already in environment)
copy .env.example .env
# Edit .env with your keys

# Test basic setup
python -c "import litellm; print('Setup OK!')"
\\\

## Technical Challenges & Solutions

### Challenge 1: LLM Output is Messy
**Problem:** Mid-stage responses include metacommentary, not just pure Fitch notation.

**Solution for MVP:** Final extraction step
- Let LLM think freely during stages
- Add final call: "Convert this completed proof to JSON"
- Only validate the extracted JSON

### Challenge 2: ASCII → JSON Translation  
**Problem:** Need to convert visual ASCII to JSON for existing proof checker.

**Implementation:** Hand-written parser
- Count \|\ characters for scope depth
- Parse line structure with regex
- Handle both en-dash (–) and hyphen (-) in ranges
- Skip skeleton lines with \...\

### Challenge 3: Validation at Scale
**Problem:** Hundreds of LLM calls = slow + expensive.

**Mitigation:**
- Start small (20 problems × 3 conditions = 60 calls)
- Use cheaper models for pilots (GPT-4o-mini, Claude Haiku)
- Pre-generate problem bank (cache problems)
- Implement timeouts (max 5 stages or 2 minutes per proof)

## Future Enhancements (Beyond MVP)

These are on the horizon but not blocking the core experiment:

1. **SAT Solver Integration:** Check if skeleton subproofs are viable before filling
2. **Automatic Notation Linter:** Enforce notation conventions, catch careless errors
3. **Proof Checker Integration:** Validate partial proofs after each stage
4. **RAG-based Subproof Minimization:** Hide completed subproofs to reduce context clutter
5. **UI Prettification:** Collapse closed subproofs in display (show only assumption + conclusion)

## The Big Picture Dream

If this works, we can:
- Establish that visual notation structure helps LLMs with complex reasoning
- Create a reusable protocol for other formal systems (FOL, sequent calculus, etc.)
- Build tools that let humans and LLMs collaborate on proofs more effectively
- Explore whether this generalizes beyond logic (e.g., mathematical proofs, program verification)

The protocol might not just help LLMs—it might help humans too. By externalizing structure visually, we reduce cognitive load for everyone.

## Development Phases

### Phase 1: MVP Experiment (Current)
**Goal:** Clean proof-of-concept with reliable data

1. ✅ Setup project structure
2. Build solver wrapper for 3 conditions  
3. Build ASCII→JSON parser
4. Run pilot (20 problems)
5. Analyze: is there a signal?

### Phase 2: Scale & Refine (If promising)
**Goal:** Robust validation and publication

1. Expand to 100+ problems across difficulties
2. Test multiple models (GPT-4, Claude, etc.)
3. Statistical significance testing
4. Write up results

### Phase 3: Enhancement (If successful)
**Goal:** Make it actually useful

1. Add SAT solver pre-checking
2. Build notation linter
3. Integrate real-time proof validation
4. Create UI/CLI tool for human use

## Contributing

This is early-stage research. Ideas welcome! Open an issue if you have:
- Suggestions for experimental design
- Alternative proof systems to test
- Implementation improvements
- Ideas for applications

## References & Related Work

- **forall x** textbook: Standard intro logic text using Fitch notation
- Existing JSON proof checker: [Link to be added]
- Related: Visual scaffolding in math education, analogical reasoning in AI

## License

MIT
