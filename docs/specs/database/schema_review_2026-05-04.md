# Database Schema Review

**Date:** 2026-05-04  
**Scope:** Existing repository schema and database-facing implementation.  
**Status:** Review only. No schema changes were made.

## Executive Summary

The schema is usable for an MVP resume-optimization pipeline, but it is not yet a strong audit/provenance schema for an LLM product. The main data model is `applications` plus per-agent `agent_outputs`, with supporting validation, review, streaming, recovery, profile, usage, and preferences tables.

The biggest risk is that one `applications` row mixes source data, current derived resume text, status, summary metrics, and final output state. Generated outputs are often overwritten or upserted instead of versioned. Prompt versions, model parameters, retrieved evidence, validation lineage, and cost provenance are not captured consistently.

The schema does have useful foundations: user scoping in Supabase, RLS for many tables, per-agent output rows, event replay, recovery checkpoints, and a separate evaluation suite. The recommendation is not to rewrite everything immediately, but to add versioned execution and artifact tables around the current model, then gradually migrate reads and writes.

Primary evidence reviewed:

- `backend/migrations/001_supabase_schema.sql`
- `backend/migrations/002_user_preferences_and_resumes.sql`
- `backend/migrations/003_application_reviews.sql`
- `backend/src/database/db.py`
- `backend/src/database/supabase_db.py`
- `backend/src/database/migrations/*.sql`
- `backend/server.py`
- `backend/scripts/migrate_sqlite_to_supabase.py`
- `evals/db/eval_db.py`
- `docs/specs/database/supabase_schema_v2.md`
- `docs/specs/llm-provider-parameters/cost-tracking-spec.md`

## Current Schema Map

### Product Domain

This repository implements a resume optimizer. A user submits a resume and a job posting, then a five-agent pipeline generates:

1. Job analysis
2. Resume optimization strategy
3. Optimized resume implementation
4. Validation and scoring
5. Final polished review/export

The system also supports profile enrichment from LinkedIn/GitHub, saved resumes, streaming pipeline events, recovery checkpoints, usage metering, and an evaluation suite for comparing model outputs.

### Main Application Tables

#### `applications`

Represents a user-facing resume optimization job/application target.

Observed fields include:

- Primary key: `id`
- Ownership: `user_id`
- Job source: `company_name`, `job_title`, `job_url`, `job_posting_text`
- Resume data: `original_resume_text`, `optimized_resume_text`
- Summary metrics: `overall_score`, `total_cost_usd`, `total_input_tokens`, `total_output_tokens`
- Status: `pending`, `processing`, `completed`, `failed`, `cancelled` in Supabase; `in_progress` in SQLite local mode
- Provenance summary: `model_used`, `pipeline_version`
- Timestamps: `created_at`, `updated_at`, `completed_at`
- Soft delete in Supabase: `deleted_at`

This table is currently the central workflow container and also stores raw input, current derived output, and summary metrics.

#### `agent_outputs`

Represents per-agent execution output for an application.

Observed fields include:

- Primary key: `id`
- Foreign key: `application_id`
- Ownership: `user_id` in Supabase
- Agent identity: `agent_name`, `agent_number`
- Model metadata: `model_provider`, `model_name` in Supabase
- Cost/tokens: `input_tokens`, `output_tokens`, generated `total_tokens`, `cost_usd`
- Timing/retry: `execution_time_ms`, `retry_count`
- Data: `input_data`, `output_data`
- Quality: `quality_score`
- Timestamp: `created_at`
- Constraint in Supabase: `unique(application_id, agent_number)`

This table is useful but currently behaves like one output per agent per application, not a complete run/attempt history.

#### `validation_scores`

Represents parsed quality scores and feedback from validation.

Observed fields include:

- Primary key: `id`
- Foreign key: `application_id`
- Ownership: `user_id` in Supabase
- Score dimensions: `requirements_match`, `ats_optimization`, `cultural_fit`, `presentation_quality`, `competitive_positioning`, `overall_score`
- JSON feedback: `red_flags`, `recommendations`, `strengths`
- Model: `model_name`
- Timestamp: `created_at`

This is derived data. It is partially structured but does not model individual validation checks/findings as first-class records.

#### `application_reviews`

Represents the canonical final user-facing review/export document for an application.

Observed fields include:

- Primary key: `application_id`
- Ownership: `user_id`
- Output content: `plain_text`, `markdown`, `filename`
- Summary: `summary_points`
- Timestamps: `created_at`, `updated_at`

This is a user-facing output, but it is mutable and one-per-application.

#### `profiles`

Represents cached profile snapshots from LinkedIn/GitHub/additional profile data.

Observed fields include:

- Primary key: `id`
- Ownership: `user_id` in Supabase
- Source identifiers: `linkedin_url`, `github_username`, `sources`
- Raw/derived data: `profile_text`, `profile_index`
- Version-ish metadata: `is_active`, `version`
- Timestamps: `created_at`, `updated_at`

This table mixes raw aggregated profile text and model-derived profile index.

#### `saved_resumes`

Represents reusable resume text saved by a user.

Observed fields include:

- Primary key: `id`
- Ownership: `user_id`
- Metadata: `label`, `filename`, `content_hash`, `is_default`
- Source text: `resume_text`
- Timestamps: `created_at`, `updated_at`

This is source data, but it has no explicit document version model or parse provenance.

#### `user_preferences`

Represents user defaults.

Observed fields include:

- Primary key: `user_id` in Supabase
- Defaults: `default_linkedin_url`, `default_github_username`, `default_resume_id`
- Timestamps: `created_at`, `updated_at`

#### `pipeline_runs`

Represents streaming pipeline/run state in Supabase.

Observed fields include:

- Primary key: `id`
- Unique job id: `job_id`
- Ownership: `user_id`
- Optional application link: `application_id`
- Client replay state: `client_id`, `last_event_seq`
- Status: `queued`, `pending`, `started`, `running`, `completed`, `failed`, `cancelled`
- Progress: `current_step`, `steps_completed`, `total_steps`, `progress_percent`
- Error fields: `error_type`, `error_message`
- Timing: `started_at`, `completed_at`, `duration_ms`
- Client metadata: `client_ip`, `user_agent`
- Timestamps: `created_at`, `updated_at`

SQLite local mode uses `run_metadata` instead.

#### `run_events`

Represents persisted SSE event replay.

Observed fields include:

- Primary key: `id`
- Event stream key: `job_id`, `seq`
- Ownership: `user_id` in Supabase
- Event type: `event_type` in Supabase, `type` in SQLite
- Payload: `payload`
- Event timestamp: `ts`
- Timestamp: `created_at`
- Constraint: unique `(job_id, seq)`

This is an event log, but in Supabase it lacks a foreign key to `pipeline_runs(job_id)`.

#### `recovery_sessions`

Represents recoverable pipeline/session state.

Observed fields include:

- Primary key: `id`
- Unique session id: `session_id`
- Ownership: `user_id` in Supabase
- Optional application link: `application_id`
- Source state: `form_data`, `file_metadata`
- Status and progress: `status`, `completed_agents`
- Error context: `error_id`, `error_type`, `error_category`, `error_message`
- Retry: `retry_count`, `last_retry_at`
- Client metadata: `ip_address`, `user_agent`
- Expiry: `expires_at`
- Timestamp: `created_at`

SQLite status values differ from Supabase status values.

#### `agent_checkpoints`

Represents recovery snapshots per agent.

Observed fields include:

- Primary key: `id`
- Foreign key: `session_id`
- Ownership: `user_id` in Supabase
- Agent identity: `agent_index`, `agent_name`
- Output: `agent_output`
- Metrics: `execution_time_ms`, `model_used`, `tokens_used`, `cost_usd`
- Timestamp: `created_at`
- Unique checkpoint: `(session_id, agent_index)`

This is useful for recovery, but it is not linked to the canonical agent output/run model.

#### `error_logs`

Represents server/pipeline error telemetry.

Observed fields include:

- Primary key: `id`
- Unique error id: `error_id`
- Context: `user_id`, `session_id`, `application_id`
- Error details: `error_type`, `error_category`, `error_message`, `error_stacktrace`
- Request context: `request_path`, `request_method`, `user_agent`, `ip_address`
- JSON context: `additional_context`
- Timestamp: `created_at`

Supabase does not define foreign keys for `session_id` or `application_id` here.

#### `user_usage`

Represents usage metering.

Observed fields include:

- Primary key: `user_id`
- Period: `period_start`
- Current usage: `generation_count`
- Lifetime usage: `lifetime_generations`, `lifetime_cost_usd`, `lifetime_input_tokens`, `lifetime_output_tokens`
- Timestamps: `created_at`, `updated_at`

The RPC `check_and_increment_usage` increments generation counts but does not reconcile cost/token totals.

#### `subscriptions`

Represents Stripe subscription status.

Observed fields include:

- Primary key: `user_id`
- Stripe identifiers: `stripe_customer_id`, `stripe_subscription_id`
- Plan: `plan_id`, `plan_name`
- Status: `none`, `trialing`, `active`, `past_due`, `canceled`, `unpaid`
- Billing period: `current_period_start`, `current_period_end`, `cancel_at_period_end`
- Timestamps: `created_at`, `updated_at`

#### `daily_stats` and `model_usage_stats`

Represent intended aggregate analytics.

These tables are present in Supabase migration `001_supabase_schema.sql`, but I did not find active application write paths that keep them current.

### Evaluation Suite Tables

The separate eval suite under `evals/` has its own SQLite schema:

- `eval_scenarios`: profile/job posting scenarios
- `eval_stage_runs`: a stage evaluation for a scenario
- `eval_candidates`: candidate model outputs
- `eval_judgments`: human judgments

This schema is conceptually cleaner for model comparisons than the production `agent_outputs` table, but it is separate from production provenance.

## Scorecard

| Criterion | Score 1-5 | Notes |
|---|---:|---|
| Domain correctness | 2 | Core flow is recognizable, but `applications` is overloaded and document/job/profile concepts are underspecified. |
| Source/derived/output separation | 2 | Raw resume, optimized resume, final review, and summaries are mixed or one-row-per-current-state. |
| Traceability/provenance | 2 | Agent outputs help, but prompt versions, model params, run ids, retrieved evidence, validations, and output lineage are incomplete. |
| Query fitness | 3 | Basic user history/latest review/event replay queries are supported; audit and cost queries are awkward. |
| Normalization/denormalization | 2 | Some intentional denormalized totals exist, but core truth is duplicated/overwritten without snapshot semantics. |
| Constraints and invalid states | 2 | Supabase has useful checks/RLS, but many nullable core fields, weak state machines, and missing cross-owner constraints remain. |
| Versioning | 1 | No real versioned documents, prompts, artifacts, runs, exports, or user edits. |
| Performance/indexing | 3 | Common user/status/event indexes exist; missing compound indexes for latest review, run/application joins, and analytics paths. |
| Evolvability | 2 | Multiple models/runs are partially possible, but historical comparison and replay require schema changes. |
| Analytics/observability | 2 | Event logs and aggregate tables exist, but cost/usage/analytics are not fully populated or normalized. |

## Critical Issues

1. `applications` is the overloaded source of truth for too many lifecycle stages.
2. Agent outputs are keyed by `(application_id, agent_number)`, which prevents preserving reruns and comparisons.
3. Generated outputs lack full provenance: prompt file/version, pipeline version per step, parameters, retrieved profile evidence, validation lineage, and request ids.
4. Final user-facing output is one mutable `application_reviews` row, not a versioned artifact/export history.
5. Supabase and SQLite schemas differ materially, increasing migration and behavior drift risk.
6. Cost/usage tracking is present in columns but not reliable end to end. The inspected SQLite DB had 383 of 624 `agent_outputs` rows with zero cost and zero tokens.

## Detailed Findings

### Issue: Overloaded `applications`

- Severity: High
- Location: `applications` in `backend/migrations/001_supabase_schema.sql`, `backend/src/database/db.py`
- Current design: Job posting text, original resume text, latest optimized resume, status, model summary, score, and aggregate costs live in one row.
- Problem: Source truth and derived/current output are coupled.
- Example failure mode: A user refines a generated resume, and the previous final resume cannot be reconstructed.
- Recommended fix: Add `source_documents`/`document_versions`, `job_postings`, `optimization_runs`, `resume_artifacts`, and keep `applications` as a lightweight workflow/container.
- Migration required: Yes, additive first.
- Risk: Medium, because read APIs currently depend on `applications`.

### Issue: Agent reruns overwrite history

- Severity: High
- Location: `agent_outputs.unique_agent_per_app`, `SupabaseDatabase.save_agent_output`
- Current design: One output per application and agent number.
- Problem: Multiple attempts, retries, model comparisons, and refinements cannot be audited.
- Example failure mode: Agent 4 fails, reruns with a different model, and the first output/cost disappears.
- Recommended fix: Introduce `agent_runs` and `agent_steps` with `run_id`, `attempt_number`, `status`, `started_at`, `completed_at`, `model_provider`, `model_name`, params, token/cost details.
- Migration required: Yes.
- Risk: Medium.

### Issue: Weak LLM provenance

- Severity: High
- Location: `agent_outputs`, `pipeline_runs`, `backend/prompts/*.md`
- Current design: Stores agent name/number and JSON input/output, with model fields only in Supabase and not consistently populated from every helper path.
- Problem: Cannot reliably answer which prompt, pipeline code version, model params, retrieved profile context, or validation checks produced an output.
- Example failure mode: A resume claim is challenged and there is no structured evidence trail for why it was generated.
- Recommended fix: Add `prompt_versions`, `model_invocations`, `retrieval_results`/`evidence_items`, and link every generated artifact to `agent_step_id`.
- Migration required: Additive.
- Risk: Low to medium.

### Issue: Final outputs are mutable, not versioned

- Severity: High
- Location: `application_reviews`
- Current design: `application_id` is the primary key; review is upserted.
- Problem: User-facing outputs and exports are not immutable artifacts.
- Example failure mode: Exported DOCX content no longer matches the database after a later polish/refine.
- Recommended fix: Add `resume_artifacts` or `application_review_versions` and `exports`, with immutable content hash, parent artifact, generation step, and user edit metadata.
- Migration required: Yes.
- Risk: Medium.

### Issue: Source documents are not modeled

- Severity: High
- Location: `saved_resumes`, `applications.original_resume_text`, upload routes in `backend/server.py`
- Current design: Resume text is stored directly in saved resumes and copied into applications; file metadata is limited.
- Problem: No raw upload, parsed representation, parser version, content hash/version lifecycle, or reusable document version.
- Example failure mode: A PDF parser bug is fixed, but existing generated resumes cannot be tied to parser version or reprocessed cleanly.
- Recommended fix: Add `documents`, `document_versions`, `document_parse_results`, and optional `document_chunks`.
- Migration required: Additive.
- Risk: Medium.

### Issue: Job posting source and parsed requirements are under-modeled

- Severity: Medium
- Location: `applications.job_url`, `applications.job_posting_text`, `agent_outputs` for Job Analyzer
- Current design: Job URL and job text are stored on `applications`; requirements are embedded in agent output text/JSON.
- Problem: The source job posting, fetched snapshot, scraper metadata, and parsed requirements are not separate artifacts.
- Example failure mode: A job URL changes after generation and the app cannot prove which posting version was analyzed.
- Recommended fix: Add `job_postings` and `job_posting_snapshots`; add `job_requirements` or `extracted_facts` for structured requirements.
- Migration required: Additive.
- Risk: Low.

### Issue: Validation findings are not first-class

- Severity: Medium
- Location: `validation_scores`
- Current design: Score dimensions plus arrays of `red_flags`, `recommendations`, and `strengths`.
- Problem: Individual checks, evidence, confidence, and pass/fail state are not queryable.
- Example failure mode: "Which validation checks fail most often?" requires parsing arbitrary JSON arrays or raw validator text.
- Recommended fix: Add `validation_runs`, `validation_checks`, and `validation_findings` linked to `agent_step_id` and relevant evidence/artifacts.
- Migration required: Additive.
- Risk: Low.

### Issue: Cost and usage tracking is incomplete

- Severity: Medium
- Location: `agent_outputs`, `user_usage`, `daily_stats`, `model_usage_stats`
- Current design: Per-agent cost/tokens plus aggregate columns exist, but no durable per-request cost events.
- Problem: Aggregates cannot be reconciled, pricing versions are absent, and actual vs estimated tokens are not distinguished.
- Example failure mode: Monthly bill does not match app totals and there is no request-level audit trail.
- Recommended fix: Add `model_invocations` or `cost_events` with request id, provider, model, pricing version, token source, input/output cost, success/error, latency, user/run/step ids.
- Migration required: Additive.
- Risk: Low.

### Issue: State machines allow invalid combinations

- Severity: Medium
- Location: `applications.status`, `pipeline_runs.status`, `recovery_sessions.status`
- Current design: Status checks exist in Supabase, but no constraints tying `completed_at`, `error_message`, `started_at`, and outputs to status.
- Problem: Rows can be `completed` without a review, `failed` without error context, or `processing` forever.
- Example failure mode: History UI shows a completed application with no final review.
- Recommended fix: Add lifecycle rules in app code first; later add check constraints where stable.
- Migration required: Mostly application logic, optional constraints.
- Risk: Low to medium.

### Issue: Schema drift between SQLite, Supabase, and evals

- Severity: Medium
- Location: `backend/src/database/db.py`, `backend/src/database/supabase_db.py`, `backend/data/applications.db`, `evals/db/eval_db.py`
- Current design: SQLite local schema differs from Supabase: profile ownership, model fields, status names, soft delete, application totals, analytics/evaluation tables.
- Problem: Local behavior can pass tests while production behavior differs.
- Example failure mode: A query works in SQLite but fails or returns different records in Supabase.
- Recommended fix: Pick Supabase/Postgres as canonical, generate a schema contract, and keep SQLite as explicit dev-only compatibility or retire it.
- Migration required: Process/schema tooling.
- Risk: Medium.

### Issue: Ownership is inconsistent in local SQLite

- Severity: Medium
- Location: `profiles`, `recovery_sessions`, `agent_outputs`, `validation_scores` in SQLite
- Current design: Some SQLite tables have `user_id`, but several child tables rely on parent filtering or do not have ownership columns.
- Problem: Local/dev fallback identities and production UUID identities do not behave identically.
- Example failure mode: A local recovery/profile row can be read or reused outside the intended user scope.
- Recommended fix: Make ownership explicit on all user-data tables, or enforce all access through parent joins and document that invariant.
- Migration required: Additive for SQLite, already partially present in Supabase.
- Risk: Low.

### Issue: Run events are high-volume but under-retained

- Severity: Medium
- Location: `run_events`
- Current design: Every SSE event payload is persisted with no visible retention or summarization policy.
- Problem: The inspected backend SQLite DB had 66,352 `run_events` rows. This will grow quickly.
- Example failure mode: Event replay storage dominates DB size while product history only needs recent replay plus compact audit.
- Recommended fix: Add retention policy, event categories, optional archival, and summarize important run milestones into `agent_steps`/`run_summaries`.
- Migration required: No destructive migration initially; add cleanup job later.
- Risk: Low.

### Issue: Analytics aggregate tables are not maintained

- Severity: Medium
- Location: `daily_stats`, `model_usage_stats`
- Current design: Tables exist in Supabase migration but no active write/update path was found.
- Problem: Consumers may trust stale or empty analytics.
- Example failure mode: Admin dashboard shows zero model cost while `agent_outputs` has nonzero cost.
- Recommended fix: Either remove them from active product docs until implemented, or populate them via scheduled jobs/materialized views from normalized event/cost tables.
- Migration required: No schema migration required if using jobs/views.
- Risk: Low.

### Issue: RLS is enabled but not complete for all exposed tables

- Severity: Medium
- Location: Supabase RLS section in `001_supabase_schema.sql` and `003_application_reviews.sql`
- Current design: RLS is enabled on most user-facing tables; `run_events`, `agent_checkpoints`, aggregate analytics tables are not all treated uniformly in the initial migration.
- Problem: If frontend/PostgREST access expands beyond backend service-role access, missing RLS becomes a security risk.
- Example failure mode: A client can query event or checkpoint rows if table exposure/policies change.
- Recommended fix: Enable RLS and define read policies on every table in exposed schemas, even if backend currently uses service role.
- Migration required: Additive security migration.
- Risk: Medium if client DB access is introduced; low if backend-only remains strict.

### Issue: Referential integrity gaps

- Severity: Medium
- Location: `run_events.job_id`, `error_logs.session_id`, `error_logs.application_id`, `user_preferences.default_resume_id`
- Current design: Some relationships are plain ids without foreign keys, or have FKs without composite ownership guarantees.
- Problem: Orphans and cross-owner references are possible.
- Example failure mode: A `user_preferences.default_resume_id` could point to a resume owned by another user unless application code prevents it.
- Recommended fix: Add foreign keys where missing; for cross-owner relationships, use composite unique keys such as `(id, user_id)` and composite FKs where practical.
- Migration required: Additive, but backfill/orphan cleanup needed before validation.
- Risk: Medium.

## Recommended Target Direction

Keep `applications` as the user-visible workflow container, but move durable truth into versioned tables.

### Inputs

- `documents`
- `document_versions`
- `document_parse_results`
- `job_postings`
- `job_posting_snapshots`
- `profile_sources`
- `profile_snapshots`

### Execution

- `pipeline_runs`
- `agent_steps`
- `model_invocations`
- `prompt_versions`

### Evidence

- `retrieval_queries`
- `retrieval_results`
- `evidence_items`
- Optional `document_chunks` and embeddings if retrieval becomes first-class

### Outputs

- `resume_artifacts`
- `application_review_versions`
- `exports`
- `user_edits`

### Validation and Evaluation

- `validation_runs`
- `validation_checks`
- `validation_findings`
- `scores`
- `rubrics`
- links to evaluation datasets and judgments where production outputs are evaluated

### Observability

- `cost_events`
- `usage_events`
- `run_events`
- `error_logs`
- materialized or scheduled aggregate tables/views

## Immediate Fixes

Prefer additive, reversible changes:

1. Add missing indexes for high-value queries:
   - `applications(user_id, status, updated_at desc) where deleted_at is null`
   - `application_reviews(user_id, updated_at desc)`
   - `pipeline_runs(user_id, created_at desc)`
   - `pipeline_runs(application_id)`
   - `agent_outputs(application_id, created_at desc)`
   - `validation_scores(application_id, created_at desc)`
   - `run_events(user_id, created_at desc)` if user-level event queries are expected
2. Add explicit model metadata to every agent output write path, not only the Supabase adapter signature.
3. Add `pipeline_run_id` or `job_id` to `agent_outputs` and `validation_scores` as nullable columns.
4. Add `status_reason`, `error_id`, or `failure_stage` on run/application summaries.
5. Add RLS/policies for any exposed table that lacks them.
6. Document canonical status values and reconcile `in_progress` vs `processing`.
7. Treat `daily_stats` and `model_usage_stats` as derived-only and document how they are populated.

## Medium-Term Refactor

1. Add `optimization_runs` or `agent_runs` as the parent execution record.
2. Split `agent_outputs` into:
   - `agent_steps`: lifecycle, prompt/model/config/cost/provenance
   - `agent_artifacts`: structured outputs and text/blob snapshots
3. Add versioned final artifacts:
   - `resume_artifacts`
   - `application_review_versions`
   - `exports`
4. Add source data tables:
   - `documents`
   - `document_versions`
   - `job_posting_snapshots`
5. Add validation details:
   - `validation_runs`
   - `validation_findings`
6. Add request-level cost records:
   - `model_invocations` or `cost_events`
7. Add prompt/pipeline provenance:
   - `prompt_versions`
   - `pipeline_versions`
   - prompt content hash and code/config hash

## Long-Term Architecture

1. Use event logging for user actions and pipeline transitions.
2. Store immutable artifacts with content hashes and parent artifact links.
3. Support experiment tracking by connecting production runs to the eval suite concepts.
4. Add materialized views or warehouse-style reporting tables for cost, success rate, latency, and quality analytics.
5. Add vector/full-text retrieval schema only if retrieval becomes a core product capability.
6. Add organization/team ownership only when product requirements justify it.
7. Define retention policies for raw resumes, job postings, profile snapshots, event streams, and model prompts/responses.

## Suggested Migration Plan

### 1. Safe Additive Changes

- Add nullable provenance columns and missing indexes.
- Add `agent_runs`/`agent_steps` without changing existing writes.
- Add `resume_artifacts` or `application_review_versions`.
- Add RLS on all exposed user-data tables.

### 2. Backfill and Compatibility Layer

- Backfill one run per existing application where possible.
- Backfill one step per existing `agent_outputs` row.
- Backfill one artifact per existing `application_reviews` row.
- Preserve existing API response shapes by reading from new tables and falling back to old columns.

### 3. Application Code Migration

- Write new runs/steps/artifacts first.
- Continue updating legacy columns as denormalized summaries for UI compatibility.
- Route final export reads through artifact versions instead of mutable `applications.optimized_resume_text`.

### 4. Cleanup and Deprecation

- Stop writing raw generated outputs directly into `applications` except as summaries.
- Mark legacy columns as compatibility-only.
- Remove or archive stale aggregate tables if replaced by views/jobs.
- Defer destructive column/table cleanup until after production confidence and backups.

## Open Questions

1. Is an `application` meant to represent one job target, one generation run, or a long-lived workspace for many runs?
2. Should users be able to refine and compare multiple final resume versions?
3. Are raw uploaded files stored anywhere, or only extracted text?
4. Which outputs must be legally/auditably reproducible?
5. Should profile data be user-editable facts, scraped snapshots, or model-derived summaries?
6. Is Supabase now the canonical production DB, or must SQLite remain feature-equivalent?
7. What retention policy applies to resumes, job postings, events, and model inputs?
8. Should usage limits count started runs, completed runs, or successful final exports?
9. Should cost attribution be per user, per run, per application, per model invocation, or all of these?

