# Fitch Proof Student Quiz System Guide

## Overview

This system automatically generates, validates, and serves Fitch-style natural deduction proof problems for student practice. The system consists of:

1. **Problem Generation Pipeline** - Automated creation of valid proof problems
2. **Problem Bank** - Central repository of solved, validated problems  
3. **Quiz Systems** - Multiple interfaces for student practice
4. **Web Interface** - Planned static website for student access

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUICK HARVEST WORKFLOW                       │
├─────────────────────────────────────────────────────────────────┤
│  experiments/quick_harvest.py                                   │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│  │ Problem         │    │ LLM Proof        │    │ Validation  │ │
│  │ Generation      │───▶│ Generation       │───▶│ & Storage   │ │
│  │                 │    │                  │    │             │ │
│  └─────────────────┘    └──────────────────┘    └─────────────┘ │
│         │                       │                       │       │
│  depends on:            depends on:                    depends on:│
│  • entailment_finder   • src/proof_solver.py          • add_to_ │
│  • generate_formula    • prompts/fitch_rules_prompt.md│ problem_ │
│  • check_entailment   • prompts/protocol_instructions │ bank()  │
│  • check_contradiction│ • src/ascii_to_json.py        │         │
│                       │ • src/proof_checker.py        │         │
│                       │ • test_checker.php            │         │
└─────────────────────────────────────────────────────────────────┘
```

## Key File Locations

### 📍 Problem Bank (MAIN DATABASE)
- **Primary Location**: `data/problems/fitch_problem_bank.jsonl`
- **Format**: JSONL (one JSON object per line)
- **Purpose**: Central repository of ALL solved, validated problems

### 🔧 Core Components
- `experiments/quick_harvest.py` - Main problem generation pipeline
- `src/quiz_sampler.py` - Current command-line quiz interface
- `entailment_finder_interactive.py` - SAT-based problem generation
- `src/proof_solver.py` - LLM proof generation in 3 conditions
- `test_checker.php` - PHP-based proof validation

## Problem Bank Structure

The `fitch_problem_bank.jsonl` contains **SOLVED problems** with complete metadata. Each entry includes:

```json
{
  "id": "quick_1737830400_001",
  "premises": ["(P → Q)", "P"],
  "conclusion": "Q",
  "ascii_solution": "Full ASCII proof...",
  "json_solution": {"structured proof data..."},
  "metadata": {
    "line_count": 5,
    "rules_used": ["→E", "→I"],
    "subproof_depth": 0,
    "total_steps": 3
  },
  "validation_result": {"valid": true, ...},
  "solved_at": "2025-01-26T05:00:00",
  "model_used": "deepseek/deepseek-chat",
  "condition_used": "baseline"
}
```

### Key Metadata Fields
- `rules_used`: List of inference rules required for the proof
- `line_count`: Number of lines in the proof (complexity indicator)
- `validation_result`: PHP checker validation results

## Growing the Problem Bank

### Quick Harvest Workflow

**Command to Add Problems:**
```bash
cd experiments
python quick_harvest.py --batch-size 10 --bundle 2
```

**What Happens:**
1. **Generates** 10 new problems using SAT solver
2. **Tests** each with baseline LLM condition (token-efficient)
3. **Validates** proofs using PHP checker
4. **Appends** successful problems to `data/problems/fitch_problem_bank.jsonl`
5. **Success Rate**: ~70% (7-8 problems per 10-minute run)

**Available Bundles:**
- `--bundle 1`: Basic rules only (&, →)
- `--bundle 2`: Positive logic (&, |, →, ↔) 
- `--bundle 3`: Full logic including negation (~)

### ID System
Problems use timestamp-based IDs: `quick_{unix_timestamp}_{sequence}`
- Prevents ID conflicts across multiple runs
- Easy to track when problems were generated

## Current Quiz Systems

### Command-Line Quiz (`src/quiz_sampler.py`)

**Features:**
- Progressive difficulty by rule sets
- Filtering by rules learned each week
- Solutions with standardized symbols

**Usage:**
```bash
python src/quiz_sampler.py
```

**Rule Progression:**
1. **Week 1**: Basic rules (∧I, ∧E, →I, →E)
2. **Week 2**: + Disjunction & Biconditional (∨I, ∨E, ↔I, ↔E)  
3. **Week 3**: + Negation (¬I, ¬E, ⊥I, ⊥E)
4. **All Rules**: No filtering

## Web Quiz Implementation Plan

### Static Website Approach

**Why Static?**
- No backend maintenance required
- Free hosting (GitHub Pages, Netlify)
- Easy updates - just regenerate JSON file
- Perfect for hobby project scale

**Implementation Steps:**
1. **Export**: Convert JSONL → JSON array for web loading
2. **Filtering**: JavaScript selects problems by rule usage
3. **Deployment**: Host on free static hosting

### Smart Problem Selection

For each week, select problems that:
1. **Only use rules learned up to that week**
2. **Use at least one "new" rule from that week** (for weeks 2+)

**Example JavaScript Filter:**
```javascript
// For Week 2: Must use at least one of ["∨I", "∨E", "↔I", "↔E"]
const week2Problems = problems.filter(p => 
  usesOnlyWeek2Rules(p) && usesAtLeastOneNewWeek2Rule(p)
);
```

### File Structure for Web Quiz
```
web_quiz/
├── index.html          # Week selection
├── quiz.html           # Problem display  
├── style.css           # Basic styling
├── app.js              # Quiz logic
└── data/
    └── problem_bank.json  # Exported from JSONL
```

## Maintenance Guide

### Adding More Problems

**Regular Updates:**
```bash
# Add 20 problems with full logic
python experiments/quick_harvest.py --batch-size 20 --bundle 3

# Check current bank size
wc -l data/problems/fitch_problem_bank.jsonl
```

**Target Sizes:**
- Current: ~72 problems
- Short-term: 100-300 problems  
- Long-term: Up to 1000 problems (sufficient for student practice)

### Updating Web Quiz

1. **Export** updated problem bank:
   ```bash
   # Convert JSONL to single JSON array
   python scripts/export_for_web.py
   ```

2. **Redeploy** to hosting service
3. **No backend changes** needed!

### Key Things to Remember

- ✅ **Problem bank grows via appending** - multiple runs add to existing bank
- ✅ **IDs are timestamp-based** - prevents conflicts across runs  
- ✅ **All problems are validated** - only correct proofs are stored
- ✅ **Rule usage metadata enables** smart progressive difficulty
- ✅ **Web quiz uses static files** - no backend maintenance required

## Troubleshooting

### Common Issues

**Problem Bank Not Growing:**
- Check that quick harvest is using append mode (`'a'`)
- Verify IDs are timestamp-based to avoid conflicts
- Ensure PHP checker dependencies are installed

**Web Quiz Problems Missing:**
- Verify problem bank export includes all entries
- Check JavaScript filtering logic for rule requirements
- Ensure week 2+ problems actually use new rules

**Symbol Display Issues:**
- All problems use standardized symbols (∨, ∧, →, ↔, ¬)
- Command-line quiz handles Windows encoding automatically

## Future Enhancements

1. **Typesetting Integration** - Open Logic Project HTML or LaTeX
2. **Student Progress Tracking** - Difficulty ratings and analytics  
3. **Mobile Interface** - Responsive design for phones/tablets
4. **Export Features** - Printable worksheets, solution keys

---

*Last Updated: January 2025*  
*System Maintainer: [Your Name]*