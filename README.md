# Fitch Protocol Experiment

An experimental system testing whether structured visual notation (staged Fitch protocol) improves LLM performance on multi-step formal logic proofs.

## Core Hypothesis

LLMs perform better at formal proofs when guided through a disciplined "skeleton-first" workflow rather than attempting proofs in one shot.

## Quick Start

\\\ash
# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Set up API keys
copy .env.example .env
# Edit .env with your API keys

# Run a pilot experiment
python experiments/run_experiment.py --problems 20 --output pilot_001
\\\

## Project Structure

\\\
fitch-protocol-experiment/
├── data/
│   ├── problems/          # Generated TFL problems (committed)
│   └── results/           # Experimental CSVs (gitignored)
├── src/                   # Core implementation
├── experiments/           # Experimental scripts
├── notebooks/             # Jupyter exploration
├── prompts/              # Protocol templates
└── tests/                # pytest validation
\\\

## Three Experimental Conditions

1. **Baseline**: Zero-shot "prove this problem"
2. **Partial Protocol**: Notation guide provided, no staged enforcement
3. **Full Protocol**: Stage-by-stage prompting (skeleton → fill → verify)

## Status

- [x] Protocol design and manual validation
- [x] Problem generator (random TFL)
- [x] Proof checker (JSON-based)
- [ ] ASCII→JSON parser
- [ ] Experimental infrastructure
- [ ] Statistical validation

## License

MIT
