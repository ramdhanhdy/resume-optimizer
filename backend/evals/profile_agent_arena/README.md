# Profile Agent Arena Evaluation Harness

This harness compares two ProfileAgent variants on the same evidence using **DeepEval Arena**.

## Location
- `backend/evals/profile_agent_arena/run_profile_agent_arena.py`
- Outputs JSON to `backend/evals/profile_agent_arena/results/`

## Prerequisites
- Python deps: install backend requirements **plus** DeepEval
  ```bash
  pip install -r requirements.txt
  pip install deepeval
  ```
- API keys for the chosen contestants (same as normal runtime env).
- SQLite DB with `profiles` table (default `./data/applications.db`).
- Contestant models **must exist** in `src.api.model_registry.MODEL_REGISTRY`.

## Usage
From `backend/`:
```bash
python -m evals.profile_agent_arena.run_profile_agent_arena \
  --db-path ./data/applications.db \
  --models "openrouter::qwen/qwen3-max" "openrouter::anthropic/claude-sonnet-4.5" \
  --limit 5 \
  --offset 0 \
  --judge-model "gpt-5.1" \
  --temperature 0.1 \
  --max-tokens 3500
```

## What it does
1. Loads `limit` rows from `profiles` (ordered by `created_at` desc).
2. Runs ProfileAgent twice per case (contestant A/B) on identical evidence.
3. Deterministic prechecks: JSON parseability + required keys.
4. If both are valid JSON, runs **ArenaGEval** with grounding-focused evaluation steps.
5. Writes a single JSON result file under `results/` with per-case winners and aggregates.

## Result file
Example structure:
```json
{
  "run_id": "profile-arena-<uuid>",
  "timestamp": "2025-12-14T12:00:00Z",
  "db_path": "./data/applications.db",
  "models": {"contestant_a": "...", "contestant_b": "..."},
  "judge_model": "gpt-5.1",
  "cases": [
    {
      "case_id": 123,
      "sources": ["linkedin:..."],
      "evidence_chars": 12000,
      "outputs": {
        "contestant_a": {"length": 5400, "valid_json": true, "missing_keys": []},
        "contestant_b": {"length": 5300, "valid_json": true, "missing_keys": []}
      },
      "winner": "Contestant B",
      "winner_reason": "grounding better ..."
    }
  ],
  "aggregate": {"Contestant A": 2, "Contestant B": 3, "Tie": 0, "error": 0}
}
```

## Notes / limits
- Arena judge requires `deepeval` installed.
- Judge model is user-specified; not restricted to `model_registry`.
- No database writes; outputs only to JSON in `results/`.
- Evidence currently uses only `profile_text` (repos_json was already embedded during profile creation).
- For visualization, open `view_results.ipynb` in this folder and run the cells to see aggregates and per-case tables.
- Interactive UI: `streamlit run evals/profile_agent_arena/streamlit_app.py` to pick models, fetch fresh LinkedIn/GitHub/manual evidence, sample DB rows, run an Arena eval, and view/save the JSON result.
