# Evaluation Suite

A research-grade evaluation framework for comparing LLM configurations across the resume optimizer pipeline stages.

## Overview

This evaluation suite implements a **within-subject, repeated-measures** design for comparing multiple LLM candidates at each pipeline stage. Key features:

- **Live evaluation**: Collect data from real usage, no static test set required
- **Blind comparison**: Candidates are randomized and labeled A/B/C to reduce bias
- **Statistical analysis**: Win rates, pairwise preferences, Bradley-Terry ranking
- **Flexible criteria**: Stage-specific evaluation criteria with optional scoring

## Directory Structure

```
evals/
├── framework/           # Core evaluation framework (generic)
│   ├── __init__.py
│   ├── schemas.py       # Dataclasses: Scenario, StageEval, CandidateOutput, Judgment
│   ├── config.py        # Base configuration
│   ├── config_resume.py # Resume-specific criteria, stages, models
│   ├── runner.py        # Orchestrates multi-candidate runs
│   ├── collector.py     # Records human judgments
│   └── analyzer.py      # Statistical analysis (win rates, Bradley-Terry)
├── db/                  # Database layer
│   ├── __init__.py
│   └── eval_db.py       # SQLite schema and queries
├── ui/                  # Streamlit UI
│   ├── __init__.py
│   ├── judge_ui.py      # Blind comparison interface
│   └── app.py           # Main Streamlit app
├── scripts/             # CLI tools
│   ├── __init__.py
│   ├── run_eval.py      # Run evaluations
│   └── analyze_results.py # Analyze and report
├── tests/               # Test suite
│   ├── __init__.py
│   ├── test_eval_db.py
│   ├── test_runner.py
│   └── test_analyzer.py
├── docs/                # Documentation
│   ├── methodology.md   # Full methodology document
│   └── research_design.md
├── notebooks/           # Jupyter notebooks
│   └── explore_eval_results.ipynb
└── results/             # Output directory for reports
```

## Quick Start

### 1. Generate Candidate Outputs

First, create an evaluation scenario by running multiple models on the same input:

```bash
# From evals/ directory

# List available models
uv run python scripts/run_eval.py --list-models

# Quick test with inline text
uv run python scripts/run_eval.py \
    --stage optimizer \
    --models "anthropic/claude-sonnet-4-20250514" "google/gemini-2.0-flash-001" \
    --profile "Software engineer with 5 years Python, built REST APIs and ML pipelines" \
    --job "Senior Backend Engineer: Python, FastAPI, AWS experience required"

# Or use files
uv run python scripts/run_eval.py \
    --stage optimizer \
    --models "model/a" "model/b" "model/c" \
    --profile-file data/sample_profile.txt \
    --job-file data/sample_job.txt
```

This creates a **scenario** in the database with candidate outputs ready for judgment.

### 2. Judge Candidates (UI)

```bash
uv run streamlit run ui/app.py
```

Navigate to **"Pending Queue"** to see evaluations waiting for your judgment.
- Compare outputs side-by-side (model identities hidden)
- Select the best one
- Optionally add scores, tags, comments

### 3. Repeat

Run more scenarios with different inputs to build up your evaluation dataset.

### 4. Analyze Results

```bash
# Text report
uv run python scripts/analyze_results.py --stage optimizer

# JSON export
uv run python scripts/analyze_results.py --stage optimizer --format json --export results.json

# Pairwise comparison
python -m evals.scripts.analyze_results --stage optimizer \
    --pairwise "anthropic/claude-sonnet-4-20250514" "google/gemini-2.0-flash-001"
```

## Key Concepts

### Scenario
A (profile, job_posting) pair representing a single evaluation instance.

### Stage Evaluation
Running multiple model candidates on the same scenario for a specific pipeline stage.

### Candidate Output
The output from a single model, with latency and token metrics.

### Judgment
Human evaluation recording the winner, optional ranking, scores, and tags.

## Metrics

### Win Rate
```
WinRate(m, s) = Wins(m, s) / Appearances(m, s)
```

### Pairwise Preference
```
P(A > B) = Wins(A over B) / Total(A vs B comparisons)
```
With 95% confidence intervals and significance testing.

### Bradley-Terry Ranking
Fits a latent strength model to produce a global ranking from pairwise comparisons.

## Configuration

### Adding New Models

Edit `evals/framework/config_resume.py`:

```python
CANDIDATE_MODELS.append(
    ModelConfig(
        model_id="provider/new-model",
        display_name="New Model",
        provider="openrouter",
    )
)
```

### Adding New Criteria

Edit `evals/framework/config_resume.py`:

```python
RESUME_STAGES["optimizer"].criteria.append("new_criterion")
CRITERIA_DESCRIPTIONS["new_criterion"] = "Description of the criterion"
```

## Running Tests

```bash
# Run all eval tests
pytest evals/tests/ -v

# Run specific test file
pytest evals/tests/test_analyzer.py -v

# Run with coverage
pytest evals/tests/ --cov=evals --cov-report=html
```

## Integration with Pipeline

To enable eval mode in the main pipeline:

```python
from evals.framework.runner import EvalRunner
from evals.framework.schemas import CandidateConfig
from evals.db.eval_db import EvalDatabase

# Initialize
db = EvalDatabase("./data/evals.db")
runner = EvalRunner(db)

# Create scenario
scenario = runner.create_scenario(
    user_profile=profile_text,
    job_posting=job_text,
)

# Run with multiple candidates
stage_eval = runner.run_stage_eval_sync(
    scenario_id=scenario.scenario_id,
    stage_id="optimizer",
    context={"profile": profile_text, "job_posting": job_text},
    candidates=[
        CandidateConfig(model_id="model/a"),
        CandidateConfig(model_id="model/b"),
    ],
    runner_fn=your_model_runner_function,
)

# Present to human for judgment via UI
```

## Documentation

- [Methodology](docs/methodology.md) - Full evaluation methodology
- [Research Design](docs/research_design.md) - Research questions and hypotheses
