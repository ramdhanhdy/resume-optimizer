# Minimum Viable Provenance Plan — Resume Optimizer

> **For Hermes:** Use this as the implementation handoff before making schema/backend/frontend changes. Preserve the newly merged conversational UI and avoid destructive migrations.

**Date:** 2026-05-05  
**Status:** Draft plan, repo-backed inspection  
**Project path:** `/mnt/e/resume-optimizer`  
**Related docs:**

- `docs/specs/product_positioning_2026-05-05.md`

Older schema-review and README-revamp notes were removed during documentation pruning. This plan is the canonical durable schema/provenance handoff.

## Goal

Make Resume Optimizer credible as an **AI pipeline / data product for individual job seekers** by adding the smallest practical provenance layer around the current Supabase schema.

The plan should preserve the new conversational UI while making it possible to answer:

> What did the system know, where did it come from, what model/prompt/version transformed it, what evidence supported the output, and what final artifact was shown/exported?

## PM decision

Do **not** do a full schema rewrite now.

The next phase should be an additive **minimum viable provenance** pass:

1. Keep `applications` as the user-visible workflow/job target container.
2. Keep existing API response shapes and frontend flow stable.
3. Add run/step/artifact/evidence tables around current tables.
4. Continue writing legacy columns as compatibility summaries until the new read paths are verified.
5. Restore GitHub as a first-class profile evidence source in the conversational UI and backend provenance model.

## Current repo-backed findings

### 1. Current schema already has useful foundations

Inspected:

- `backend/migrations/001_supabase_schema.sql`
- `backend/migrations/002_user_preferences_and_resumes.sql`
- `backend/migrations/003_application_reviews.sql`
- `backend/src/database/supabase_db.py`
- `backend/src/database/db.py`
- `backend/server.py`

Important current tables:

- `applications`
- `agent_outputs`
- `validation_scores`
- `profiles`
- `saved_resumes`
- `user_preferences`
- `pipeline_runs`
- `run_events`
- `recovery_sessions`
- `agent_checkpoints`
- `application_reviews`
- usage/subscription/aggregate tables

This is enough to support an MVP, but not enough to support strong auditability/versioning.

### 2. `applications` is overloaded

Current location:

- `backend/migrations/001_supabase_schema.sql:22-55`
- `backend/src/database/supabase_db.py:149-181`
- `backend/src/database/db.py:557-599`

Current role:

- Job source: `company_name`, `job_title`, `job_url`, `job_posting_text`
- Resume source: `original_resume_text`
- Derived output: `optimized_resume_text`
- Summary metrics: `overall_score`, token/cost totals
- Status: `pending/processing/completed/failed/cancelled`
- Version-ish field: `pipeline_version`

Problem:

- Source truth, derived output, run state, and summary analytics are coupled in one row.
- Refinement or rerun history cannot be reconstructed cleanly.

Decision:

- Keep `applications` as the compatibility/workflow table.
- Add provenance tables that can later become canonical.

### 3. `agent_outputs` overwrites run history in Supabase

Current location:

- Schema: `backend/migrations/001_supabase_schema.sql:67-104`
- Supabase write path: `backend/src/database/supabase_db.py:211-254`
- SQLite write path: `backend/src/database/db.py:630-673`

Current Supabase behavior:

- Unique constraint: `unique(application_id, agent_number)`.
- `SupabaseDatabase.save_agent_output()` uses `upsert(..., on_conflict="application_id,agent_number")`.

Problem:

- Reruns, retries, model comparisons, and refinements overwrite prior state.
- `pipeline_runs.job_id` is not linked to each agent output.
- Prompt file/version and model parameters are not captured consistently.

Decision:

- Add `agent_steps` as the immutable execution-step table.
- Keep `agent_outputs` as compatibility summary until migrated.

### 4. `pipeline_runs` and `run_events` support streaming, but not enough audit lineage

Current location:

- `pipeline_runs`: `backend/migrations/001_supabase_schema.sql:242-277`
- `run_events`: `backend/migrations/001_supabase_schema.sql:289-305`

Current role:

- Runtime job state, SSE replay, progress and reconnect behavior.

Problem:

- `run_events.job_id` has no explicit FK to `pipeline_runs(job_id)`.
- Events are high-volume and not the right canonical store for agent provenance.
- Important run milestones should be summarized in `agent_steps`, `model_invocations`, and `run_artifacts` instead of relying on replay logs.

Decision:

- Use `pipeline_runs` as the parent execution record.
- Add explicit FK/indexes and link new provenance tables to `pipeline_runs.id` and/or `job_id`.

### 5. Profile/GitHub capability exists in backend, but the new conversational UI hides it

Backend evidence:

- `backend/server.py:1715-1896` builds an optional Step 0 profile index from resume, additional text, LinkedIn, and GitHub.
- `backend/server.py:1806-1829` fetches GitHub repos via `fetch_github_repos`.
- `backend/src/agents/profile_agent.py` builds an evidence-aware `profile_index` using `<profile_text>` and optional `<repos_json>`.
- `backend/prompts/profile_agent.md` requires conservative, evidence-backed JSON with `claims_ledger`.
- `backend/src/agents/github_projects_agent.py` can fetch repositories and curate project bullets.
- `backend/prompts/agent_github_projects_curator.md` explicitly requires repo-grounded bullets.
- `backend/src/database/supabase_db.py:45-132` persists and retrieves `profiles` by LinkedIn/GitHub.

Frontend evidence:

- `frontend/src/conversation/types.ts` has `linkedinUrl`, `githubUsername`, and `forceRefreshProfile` fields.
- `frontend/src/lib/api.ts:88-119` sends `linkedin_url`, `github_username`, `force_refresh_profile` to `/api/pipeline/start`.
- `frontend/src/conversation/ProcessingStream.tsx:102-112` passes those fields to `startPipeline()`.
- `frontend/src/shell/drawers/PreferencesDrawer.tsx:18-60` stores LinkedIn and GitHub defaults.
- But `frontend/src/conversation/script.ts:108-149` only asks for generic additional context; it does not ask for GitHub username or LinkedIn URL as first-class conversational inputs.

Problem:

- The backend can use GitHub as profile evidence, but the new UI does not foreground it.
- GitHub appears as either a settings default or manually pasted summary, not as a clear evidence source in the main job-application flow.

Decision:

- Restore GitHub as first-class evidence input in the conversational script before processing.
- Preserve settings defaults, but make the pipeline visibly evidence-aware.

### 6. `profiles` is useful but mixes sources, raw text, derived index, and cache identity

Current location:

- `backend/migrations/001_supabase_schema.sql:143-164`
- `backend/src/database/supabase_db.py:45-132`
- `backend/src/database/db.py:456-535`

Current fields:

- `linkedin_url`
- `github_username`
- `sources`
- `profile_text`
- `profile_index`
- `is_active`
- `version`

Problem:

- Raw external source snapshots and model-derived profile index are stored together.
- `sources` is a JSON list, not first-class evidence rows.
- Cache lookup by LinkedIn/GitHub is useful, but source-level provenance is weak.

Decision:

- Keep `profiles` as compatibility/cache.
- Add `profile_snapshots` and `evidence_items` for versioned evidence.

## Minimum viable schema direction

### Existing tables to keep

Keep these tables for compatibility:

- `applications`
- `agent_outputs`
- `validation_scores`
- `profiles`
- `application_reviews`
- `pipeline_runs`
- `run_events`
- `saved_resumes`
- `user_preferences`

### Additive tables to introduce

#### 1. `profile_snapshots`

Purpose:

- Immutable-ish profile index versions generated from resume/additional text/LinkedIn/GitHub.
- Gives profile evidence an explicit lifecycle instead of hiding it inside `profiles.profile_index`.

Suggested fields:

```sql
create table if not exists public.profile_snapshots (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  legacy_profile_id bigint references public.profiles(id) on delete set null,
  application_id bigint references public.applications(id) on delete set null,
  pipeline_run_id bigint references public.pipeline_runs(id) on delete set null,
  source_fingerprint text,
  profile_index jsonb not null,
  profile_text_hash text,
  builder_model text,
  prompt_name text default 'profile_agent.md',
  prompt_hash text,
  created_at timestamptz not null default now()
);
```

#### 2. `evidence_items`

Purpose:

- First-class source evidence from resume, additional text, LinkedIn, GitHub repo metadata/README excerpts, and job posting snapshots.
- Lets validation and generated bullets cite structured evidence.

Suggested fields:

```sql
create table if not exists public.evidence_items (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  application_id bigint references public.applications(id) on delete cascade,
  profile_snapshot_id bigint references public.profile_snapshots(id) on delete set null,
  source_type text not null check (source_type in (
    'resume_upload',
    'additional_profile_text',
    'linkedin_profile',
    'github_repo',
    'github_readme',
    'job_posting',
    'manual_note'
  )),
  source_uri text,
  source_label text,
  content_excerpt text,
  content_hash text,
  metadata jsonb default '{}'::jsonb,
  captured_at timestamptz not null default now()
);
```

#### 3. `agent_steps`

Purpose:

- Immutable execution records for each agent step/attempt.
- The key replacement for mutable/upserted `agent_outputs` over time.

Suggested fields:

```sql
create table if not exists public.agent_steps (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  application_id bigint not null references public.applications(id) on delete cascade,
  pipeline_run_id bigint references public.pipeline_runs(id) on delete set null,
  job_id uuid,
  agent_number int not null,
  agent_name text not null,
  attempt_number int not null default 1,
  status text not null default 'completed' check (status in ('queued','running','completed','failed','cancelled')),
  input_hash text,
  output_hash text,
  input_data jsonb,
  output_data jsonb,
  model_provider text,
  model_name text,
  prompt_name text,
  prompt_hash text,
  params jsonb default '{}'::jsonb,
  input_tokens int default 0,
  output_tokens int default 0,
  cost_usd numeric(10,6) default 0,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now()
);
```

#### 4. `resume_artifacts`

Purpose:

- Immutable generated or edited resume/review artifacts.
- Stops `application_reviews` and `applications.optimized_resume_text` from being the only source of final output truth.

Suggested fields:

```sql
create table if not exists public.resume_artifacts (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  application_id bigint not null references public.applications(id) on delete cascade,
  pipeline_run_id bigint references public.pipeline_runs(id) on delete set null,
  agent_step_id bigint references public.agent_steps(id) on delete set null,
  parent_artifact_id bigint references public.resume_artifacts(id) on delete set null,
  artifact_type text not null check (artifact_type in ('optimized_resume','final_review','refinement','export')),
  plain_text text,
  markdown text,
  html text,
  content_hash text not null,
  filename text,
  summary_points jsonb default '[]'::jsonb,
  is_current boolean not null default true,
  created_at timestamptz not null default now()
);
```

#### 5. `validation_findings`

Purpose:

- First-class validation results that can cite evidence and generated artifacts.

Suggested fields:

```sql
create table if not exists public.validation_findings (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  application_id bigint not null references public.applications(id) on delete cascade,
  agent_step_id bigint references public.agent_steps(id) on delete set null,
  resume_artifact_id bigint references public.resume_artifacts(id) on delete set null,
  evidence_item_id bigint references public.evidence_items(id) on delete set null,
  finding_type text not null check (finding_type in ('red_flag','recommendation','strength','claim_check','ats_check')),
  claim text,
  verdict text check (verdict in ('pass','fail','warning','unknown')),
  confidence numeric(5,2),
  explanation text,
  created_at timestamptz not null default now()
);
```

#### 6. `model_invocations`

Purpose:

- Request-level model/cost records that can reconcile provider usage, cost, latency, and failures.

Suggested fields:

```sql
create table if not exists public.model_invocations (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  application_id bigint references public.applications(id) on delete cascade,
  pipeline_run_id bigint references public.pipeline_runs(id) on delete set null,
  agent_step_id bigint references public.agent_steps(id) on delete set null,
  provider text not null,
  model_name text not null,
  prompt_name text,
  prompt_hash text,
  params jsonb default '{}'::jsonb,
  input_tokens int default 0,
  output_tokens int default 0,
  cost_usd numeric(10,6) default 0,
  pricing_version text,
  latency_ms int,
  status text not null default 'success' check (status in ('success','error','cancelled')),
  error_message text,
  created_at timestamptz not null default now()
);
```

## Compatibility changes to existing tables

Add nullable references/indexes first:

```sql
alter table public.agent_outputs
  add column if not exists pipeline_run_id bigint references public.pipeline_runs(id) on delete set null,
  add column if not exists job_id uuid,
  add column if not exists agent_step_id bigint references public.agent_steps(id) on delete set null,
  add column if not exists prompt_name text,
  add column if not exists prompt_hash text,
  add column if not exists params jsonb default '{}'::jsonb;

alter table public.validation_scores
  add column if not exists pipeline_run_id bigint references public.pipeline_runs(id) on delete set null,
  add column if not exists agent_step_id bigint references public.agent_steps(id) on delete set null;

alter table public.application_reviews
  add column if not exists current_artifact_id bigint references public.resume_artifacts(id) on delete set null;

alter table public.run_events
  add constraint run_events_job_id_fkey
  foreign key (job_id) references public.pipeline_runs(job_id) on delete cascade;
```

Add indexes:

```sql
create index if not exists idx_agent_steps_app_created on public.agent_steps(application_id, created_at desc);
create index if not exists idx_agent_steps_run_agent on public.agent_steps(pipeline_run_id, agent_number, attempt_number);
create index if not exists idx_evidence_items_app_type on public.evidence_items(application_id, source_type);
create index if not exists idx_profile_snapshots_user_created on public.profile_snapshots(user_id, created_at desc);
create index if not exists idx_resume_artifacts_app_current on public.resume_artifacts(application_id, is_current, created_at desc);
create index if not exists idx_validation_findings_app_type on public.validation_findings(application_id, finding_type);
create index if not exists idx_model_invocations_step on public.model_invocations(agent_step_id);
create index if not exists idx_pipeline_runs_application on public.pipeline_runs(application_id);
create index if not exists idx_application_reviews_user_updated on public.application_reviews(user_id, updated_at desc);
```

## Implementation plan

### Phase 0 — Safety baseline

**Objective:** Confirm the current merged state and avoid accidental frontend destabilization.

**Rules:**

- Do not remove `node_modules`.
- Do not run `npm install` or `npm ci` without explicit approval.
- Do not make destructive DB migrations.
- Treat Supabase/Postgres as production-canonical; SQLite remains compatibility/dev fallback unless explicitly retired.

**Verification:**

```bash
git status --short
git log -1 --oneline
```

### Phase 1 — Add schema migration for provenance tables

**Objective:** Add tables/indexes without changing current runtime behavior.

**Files:**

- Create: `backend/migrations/004_minimum_viable_provenance.sql`
- Maybe mirror later: `backend/src/database/migrations/007_minimum_viable_provenance.sql` if SQLite compatibility is required.

**Steps:**

1. Create the new Supabase migration with:
   - `profile_snapshots`
   - `evidence_items`
   - `agent_steps`
   - `resume_artifacts`
   - `validation_findings`
   - `model_invocations`
   - compatibility columns/indexes
2. Enable RLS for all new user-data tables.
3. Add policies scoped by `auth.uid() = user_id`.
4. Keep all new foreign keys nullable where needed for safe backfill.
5. Do not remove/rename old columns.

**Acceptance criteria:**

- Migration is additive.
- Existing tables remain readable/writable by current code.
- New tables all include `user_id`.
- New tables have RLS policies.

### Phase 2 — Add backend write helpers

**Objective:** Let backend write new provenance records while preserving old writes.

**Files:**

- Modify: `backend/src/database/supabase_db.py`
- Modify: `backend/src/database/db.py` only if local SQLite parity is required immediately.
- Add tests under `backend/tests/`.

**New helper methods:**

- `create_profile_snapshot(...)`
- `save_evidence_item(...)`
- `save_agent_step(...)`
- `save_resume_artifact(...)`
- `save_validation_finding(...)`
- `save_model_invocation(...)`

**Compatibility rule:**

- Existing methods like `save_agent_output()`, `save_validation_scores()`, and `save_application_review()` must continue to work.
- New helpers should be optional and called alongside legacy methods.

**Acceptance criteria:**

- Unit tests prove user scoping for every new helper.
- New helpers return inserted row IDs.
- Legacy tests still pass.

### Phase 3 — Wire Step 0 profile/GitHub provenance

**Objective:** Make LinkedIn/GitHub/profile index evidence traceable.

**Files:**

- Modify: `backend/server.py`, especially current Step 0 block around `1715-1896`.
- Modify: `backend/src/database/supabase_db.py` helper usage.

**Backend behavior:**

1. When resume text is included in profile building, create an `evidence_items` row with `source_type='resume_upload'`.
2. When additional profile text is included, create `source_type='additional_profile_text'`.
3. When LinkedIn is fetched, create `source_type='linkedin_profile'` with `source_uri=linkedin_url` and hash/excerpt.
4. When GitHub repos are fetched, create one evidence row per selected/fetched repo:
   - `source_type='github_repo'` or `github_readme`
   - `source_uri=repo.url`
   - metadata: name, topics, primary language, stars, last push age
5. After `ProfileAgent.index_profile(...)` returns, write `profile_snapshots` with model/prompt metadata and links to application/run where available.
6. Continue writing `profiles` for cache compatibility.

**Important caveat:**

- Current Step 0 runs before `create_application()` in `backend/server.py`, so it does not yet have `application_id`.
- Minimum fix: write profile/evidence records with `pipeline_run_id`/`job_id` first, then update with `application_id` after app creation.
- Simpler alternative: move `create_application()` earlier once job text is resolved, before Step 0. This is cleaner but touches flow ordering; do only after tests.

**Acceptance criteria:**

- A run with GitHub username produces persisted GitHub evidence rows.
- A profile index can be tied to a pipeline run and application.
- Legacy `profiles` cache still works.

### Phase 4 — Wire agent steps and model invocation summaries

**Objective:** Preserve per-agent attempts without replacing existing UI reads.

**Files:**

- Modify: `backend/server.py` agent save points around:
  - Agent 1: `1958-1967`
  - Agent 2: `2020+`
  - Agent 3: `2086+`
  - Agent 4: `2184+`
  - Agent 5: `2266+`
- Modify: `backend/src/database/supabase_db.py`

**Behavior:**

- For every agent completion:
  1. Insert `agent_steps` row.
  2. Insert `model_invocations` row using metadata from `run_agent_with_chunk_emission` where available.
  3. Continue calling `save_agent_output()` for old history/UI/API compatibility.
  4. Store the created `agent_step_id` back on `agent_outputs` if possible.

**Acceptance criteria:**

- Rerunning the same application/agent creates new `agent_steps` rows instead of overwriting history.
- `agent_outputs` remains one-row-per-agent summary.
- Cost/tokens can be aggregated from `model_invocations` or `agent_steps`.

### Phase 5 — Add artifact versioning without changing final review UI

**Objective:** Keep final review behavior stable while recording immutable artifact history.

**Files:**

- Modify: `backend/src/database/supabase_db.py`
- Modify: `backend/src/database/db.py` if local parity needed.
- Modify final review write path in `backend/server.py` around `2258-2265`.

**Behavior:**

- When final review is produced:
  1. Compute `content_hash` over plain text + markdown/html.
  2. Insert `resume_artifacts(artifact_type='final_review')`.
  3. Mark previous `is_current=false` for same application/artifact type.
  4. Continue upserting `application_reviews` for current UI.
  5. Store `current_artifact_id` on `application_reviews`.

**Acceptance criteria:**

- Current frontend review still loads from `/api/applications/{id}/review`.
- Multiple final/refined artifacts can exist historically.
- Exported content can be reconciled against a content hash.

### Phase 6 — Restore first-class GitHub input in conversational UI

**Objective:** Bring the old GitHub profile capability back into the new conversational paradigm.

**Files:**

- Modify: `frontend/src/conversation/script.ts`
- Modify: `frontend/src/conversation/types.ts` only if new fields are needed.
- Maybe modify: `frontend/src/shell/drawers/PreferencesDrawer.tsx` copy.

**Current gap:**

- The data types and API call already support `githubUsername` and `linkedinUrl`, but the script does not ask for them directly.

**Low-risk UX change:**

Add a conversation step after `ask_job` and before `ask_additional_context_choice`:

- Message: `Want me to use profile evidence too? Add a LinkedIn URL or GitHub username, or skip.`
- UI: text/freeform or a small structured module if available.
- Parser: accept lines like:
  - `linkedin: https://linkedin.com/in/...`
  - `github: username`
  - `skip`
- Store to `linkedinUrl` and `githubUsername`.
- Keep Settings defaults as fallback.

**Acceptance criteria:**

- Main flow visibly supports GitHub username.
- `ProcessingStream` receives `state.data.githubUsername`.
- Backend Step 0 emits GitHub/profile insight events when provided.

### Phase 7 — Validation findings

**Objective:** Make anti-fabrication/validation a queryable proof point.

**Files:**

- Modify validator result parsing in `backend/server.py` around validation save path.
- Possibly modify `backend/src/app/services/validation_parser.py`.

**Behavior:**

- Continue writing `validation_scores`.
- Also write `validation_findings` rows for:
  - red flags
  - strengths
  - recommendations
  - claim checks when parser can identify them
- Link to `agent_step_id`, `resume_artifact_id`, and `evidence_item_id` where possible.

**Acceptance criteria:**

- Product can answer: “Which claims were flagged and why?”
- Portfolio narrative can truthfully claim first-class validation findings.

## What not to do yet

Do not do these until the provenance layer is working:

- Do not rewrite the entire schema around `documents`, `job_postings`, and `candidate_profiles`.
- Do not remove `applications.optimized_resume_text` or `application_reviews`.
- Do not replace the frontend review API.
- Do not add dbt/analytics dashboards before source events are reliable.
- Do not polish README as if provenance is complete before implementation exists.

## Suggested GitHub issues

### Issue 1 — Add additive Supabase provenance migration

**Priority:** P0  
**Type:** database/schema  
**Acceptance:** migration creates new tables, indexes, and RLS policies without breaking old reads/writes.

### Issue 2 — Add Supabase backend helper methods for provenance writes

**Priority:** P0  
**Type:** backend  
**Acceptance:** helper tests pass and legacy DB tests still pass.

### Issue 3 — Persist profile/GitHub evidence items and profile snapshots

**Priority:** P1  
**Type:** backend/product data  
**Acceptance:** run with GitHub username stores evidence rows and a linked profile snapshot.

### Issue 4 — Persist agent_steps/model_invocations alongside agent_outputs

**Priority:** P1  
**Type:** backend/provenance  
**Acceptance:** reruns preserve history; old `agent_outputs` summary still works.

### Issue 5 — Store final reviews as resume_artifacts

**Priority:** P1  
**Type:** backend/output versioning  
**Acceptance:** current review endpoint works and artifact history is queryable.

### Issue 6 — Restore GitHub/LinkedIn as first-class conversational inputs

**Priority:** P1  
**Type:** frontend UX  
**Acceptance:** new conversation flow asks for profile evidence; GitHub username reaches `/api/pipeline/start`.

### Issue 7 — Persist validation_findings from validator output

**Priority:** P2  
**Type:** backend/validation  
**Acceptance:** validation red flags/recommendations are queryable as rows.

## Definition of done

This provenance phase is done when:

1. A completed run has a `pipeline_runs` parent, `agent_steps`, model/cost records, and final artifact rows.
2. GitHub evidence is captured as structured evidence, not just pasted text or hidden cache data.
3. Profile index snapshots are linked to sources and the run/application that consumed them.
4. The new conversational UI remains functional.
5. Existing APIs still return the same response shapes.
6. README/case study can honestly say the app has auditable multi-agent execution and evidence-backed validation.

## PM recommendation

The next concrete implementation task should be **Issue 1: Add additive Supabase provenance migration**.

Reason:

- It is the safest laptop task.
- It unlocks all downstream backend work.
- It does not touch frontend runtime behavior.
- It turns the current schema critique into real product architecture.
