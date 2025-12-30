# Profile Agent (Step 0) – DeepEval Arena Evaluation Spec

**Status:** Draft  
**Last Updated:** 2025-12-14

---

## 1. Overview

This spec defines how we will evaluate the **Profile Agent (Step 0)** using **DeepEval Arena evaluation** (pairwise comparison).

The Profile Agent builds a reusable `profile_index` from public profile sources:

- LinkedIn (or any public page text) fetched via Exa (`fetch_public_page_text`)
- GitHub repositories fetched via PyGithub (`fetch_github_repos`)

The resulting `profile_index` is consumed downstream by Agents 1–4 as additional evidence context. Therefore, the evaluation focuses on:

- **Truthfulness / grounding** (no fabricated claims)
- **Schema correctness** (strict JSON output)
- **Usefulness** for downstream resume optimization (signal-to-noise)

---

## 2. In-scope / Out-of-scope

### 2.1 In scope

- Arena evaluation of **ProfileAgent output quality** (`profile_index`) given identical evidence inputs.
- Comparing variants:
  - **Model A vs Model B** (same prompt)
  - **Prompt v1 vs Prompt v2** (same model)
- Using existing data from the local SQLite database (`profiles` table) as evaluation inputs.

### 2.2 Out of scope

- End-to-end resume quality evals (covered by later agent specs).
- Implementing DeepEval harness code in the backend (this spec describes the plan).
- Production monitoring and dashboards (optional future work).

---

## 3. Current system behavior (authoritative)

### 3.1 Agent code and prompt

- Agent: `backend/src/agents/profile_agent.py`
- System prompt: `backend/prompts/profile_agent.md`

The system prompt requires **strict JSON output** matching this schema:

- `summary`
- `skills_taxonomy` (languages/frameworks/cloud/databases/tools/domains)
- `roles` (title/company/date_range/highlights)
- `projects` (name/url/context/tech/bullets)
- `claims_ledger` (claim/evidence_excerpt/confidence/recency)
- `snippet_pack` (topic/bullets)
- `notes_for_editors`

### 3.2 Evidence inputs

The Profile Agent is run in `backend/server.py` when either `linkedin_url` or `github_username` is provided.

Evidence sources:

- `profile_text`: fetched from Exa and truncated in-agent to 20k chars
- `profile_repos`: GitHub repos list (JSON-serialized) and truncated in-agent to 12k chars

The agent receives a user prompt wrapped with:

- `<profile_text> ... </profile_text>`
- optional `<repos_json> ... </repos_json>`

### 3.3 Persistence

The output is persisted in SQLite:

- DB path: `DATABASE_PATH` (default `./data/applications.db`)
- Table: `profiles` (see `backend/src/database/db.py`)
- Columns:
  - `sources` (JSON list)
  - `profile_text` (combined evidence text)
  - `profile_index` (agent output)

**Note:** the current pipeline does not validate that `profile_index` is valid JSON before persisting or using it.

---

## 4. Evaluation goals

### 4.1 Primary goal

Select the better Profile Agent variant for production use by comparing outputs on the **same evidence**, with strong preference for:

- **No hallucinations** / no unsupported claims
- **Valid JSON** and schema compliance
- **Useful, resume-relevant index** with conservative phrasing

### 4.2 What “better” means (scoring priorities)

- **Priority 0 (automatic loss):** invalid JSON, broken schema, or clear fabricated claims.
- **Priority 1:** better grounding quality (claims ledger and excerpts clearly supported by evidence).
- **Priority 2:** usefulness for downstream agents (skills/projects/snippet_pack provide actionable resume material).
- **Priority 3:** conciseness and low redundancy.

---

## 5. Dataset strategy (no goldens required)

Arena evaluation does not require an `expected_output`, but it does require stable **inputs**.

### 5.1 Primary dataset source: existing `profiles` rows

We will build evaluation cases from existing DB snapshots:

- Evidence: `profiles.profile_text`
- Optional: parse `profiles.sources` for metadata (linkedin/github)

This provides realistic, user-derived evidence and helps evaluate grounding.

### 5.2 Dataset sizing

- Iteration loop: 3–5 cases (fast)
- Baseline suite: 10–20 cases
- Regression suite: 30–100 cases (optional, later)

### 5.3 Case selection rules

Prefer diversity:

- LinkedIn only
- GitHub only
- Both LinkedIn + GitHub
- Short evidence vs long evidence
- Different candidate profiles / domains

### 5.4 Privacy

If any DB snapshots contain personal data, cases used for sharing/debugging must be anonymized. For local evaluation, raw text can remain local.

---

## 6. Variants (contestants)

### 6.1 Model comparison

- Contestant A: `PROFILE_MODEL=<current>`
- Contestant B: `PROFILE_MODEL=<candidate>`

Keep prompt fixed (`prompts/profile_agent.md`).

### 6.2 Prompt comparison

- Contestant A: `prompts/profile_agent.md` (v1)
- Contestant B: a new prompt file (v2), with an explicit version label in the file header.

Keep model fixed (`PROFILE_MODEL`).

**Rule:** only change one factor per experiment.

---

## 7. Metrics and checks

### 7.1 Deterministic prechecks (recommended)

Before running LLM judging, we should run deterministic checks per output:

- JSON parseability
- Required keys present
- Value types are correct (e.g., `skills_taxonomy.languages` is a list)
- Basic length caps (avoid runaway outputs)
- Numeric hallucination heuristic (flag new `%` / `$` / large numbers not present in evidence)

These do not replace judging but reduce wasted Arena calls.

### 7.2 Arena judge metric: ArenaGEval

Use a single ArenaGEval metric that encodes both grounding and usefulness.

#### Judge inputs

For each test case, include evidence as `context`:

- `<profile_text> ... </profile_text>`
- `<repos_json> ... </repos_json>` (when present)

This is critical for hallucination detection.

#### Evaluation steps (recommended)

The Arena judge should follow steps similar to:

1. Validate output is **valid JSON** and top-level keys match the required schema.
   - If invalid JSON or missing required keys → contestant loses.
2. Check for **fabricated claims** (employers, titles, dates, metrics, projects) not supported by evidence.
   - Any clear fabrication → contestant loses.
3. Check **grounding quality**:
   - `claims_ledger[].evidence_excerpt` should be plausibly found in evidence and match the claim.
   - Confidence levels should be conservative when evidence is weak.
4. Check **usefulness** for downstream resume optimization:
   - `skills_taxonomy` is meaningful and not noisy.
   - `projects` are relevant and grounded (esp. when repos_json is present).
   - `snippet_pack` bullets are resume-ready and conservative.
5. Decide winner:
   - Prefer grounding > usefulness > conciseness.
   - Allow tie if materially equivalent.

---

## 8. Execution plan

### 8.1 Local run loop (manual)

1. Choose experiment type (model vs prompt).
2. Select 3–5 recent `profiles` rows from `applications.db`.
3. For each row:
   - Generate output for Contestant A using the same evidence.
   - Generate output for Contestant B using the same evidence.
   - Run Arena judge and record winner + reasoning.
4. Iterate on evaluation steps until results are stable.

### 8.2 Caching

To reduce cost:

- Cache contestant outputs per case so we can re-run the judge without regenerating outputs.

### 8.3 Reproducibility

- Fix sampling settings where possible (low temperature).
- Record:
  - model name(s)
  - prompt version(s)
  - temperature/max_tokens
  - DeepEval judge model
  - run timestamp

---

## 9. Acceptance criteria (adoption decision)

### 9.1 Suggested decision rule

Adopt Contestant B if, on the baseline suite:

- B wins **>= 65%** of cases
- B loses **<= 20%** of cases
- and there are **0 critical grounding violations** (fabrication / invalid JSON)

### 9.2 Failure policy

Any of the following should block adoption regardless of win-rate:

- frequent invalid JSON outputs
- recurring fabricated employers/titles/dates/metrics
- evidence excerpts that do not appear in evidence (obvious mismatch)

---

## 10. Reporting format

For each case, store:

- `case_id` (profiles.id)
- sources
- evidence length
- contestant A model/prompt
- contestant B model/prompt
- winner (A/B/Tie)
- judge reasoning (short)
- any deterministic check failures

Aggregate report:

- win/loss/tie counts
- top recurring failure patterns

---

## 11. Future extensions

- Add component-level tracing once DeepEval is integrated into the runtime pipeline.
- Add a small curated anonymized dataset for CI gating.
- Add “downstream utility” eval: does the presence of profile_index improve Agent 1/2 outputs (Arena on downstream agents).
