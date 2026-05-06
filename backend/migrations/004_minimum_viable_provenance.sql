-- Migration 004: Minimum viable provenance schema
-- Adds versioned execution, evidence, artifact, and model-invocation tables.
-- Fully additive; no destructive changes.

-- ============================================
-- 1. profile_snapshots — Immutable profile index versions
-- ============================================
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

create index if not exists idx_profile_snapshots_user_created
  on public.profile_snapshots(user_id, created_at desc);
create index if not exists idx_profile_snapshots_app
  on public.profile_snapshots(application_id);
create index if not exists idx_profile_snapshots_run
  on public.profile_snapshots(pipeline_run_id);

-- ============================================
-- 2. evidence_items — First-class source evidence
-- ============================================
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

create index if not exists idx_evidence_items_app_type
  on public.evidence_items(application_id, source_type);
create index if not exists idx_evidence_items_user
  on public.evidence_items(user_id);
create index if not exists idx_evidence_items_snapshot
  on public.evidence_items(profile_snapshot_id);

-- ============================================
-- 3. agent_steps — Immutable per-agent execution records
-- ============================================
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

create index if not exists idx_agent_steps_app_created
  on public.agent_steps(application_id, created_at desc);
create index if not exists idx_agent_steps_run_agent
  on public.agent_steps(pipeline_run_id, agent_number, attempt_number);
create index if not exists idx_agent_steps_user
  on public.agent_steps(user_id);
create index if not exists idx_agent_steps_job_id
  on public.agent_steps(job_id);

-- ============================================
-- 4. resume_artifacts — Immutable generated/edited resume artifacts
-- ============================================
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

create index if not exists idx_resume_artifacts_app_current
  on public.resume_artifacts(application_id, is_current, created_at desc);
create index if not exists idx_resume_artifacts_user
  on public.resume_artifacts(user_id);
create index if not exists idx_resume_artifacts_step
  on public.resume_artifacts(agent_step_id);
create index if not exists idx_resume_artifacts_parent
  on public.resume_artifacts(parent_artifact_id);

-- ============================================
-- 5. validation_findings — First-class validation results
-- ============================================
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

create index if not exists idx_validation_findings_app_type
  on public.validation_findings(application_id, finding_type);
create index if not exists idx_validation_findings_user
  on public.validation_findings(user_id);
create index if not exists idx_validation_findings_step
  on public.validation_findings(agent_step_id);
create index if not exists idx_validation_findings_artifact
  on public.validation_findings(resume_artifact_id);

-- ============================================
-- 6. model_invocations — Request-level model/cost records
-- ============================================
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

create index if not exists idx_model_invocations_step
  on public.model_invocations(agent_step_id);
create index if not exists idx_model_invocations_user
  on public.model_invocations(user_id);
create index if not exists idx_model_invocations_app
  on public.model_invocations(application_id);
create index if not exists idx_model_invocations_run
  on public.model_invocations(pipeline_run_id);


-- ============================================
-- COMPATIBILITY COLUMNS ON EXISTING TABLES
-- ============================================

-- agent_outputs: link to pipeline run, job, and agent step
alter table public.agent_outputs
  add column if not exists pipeline_run_id bigint references public.pipeline_runs(id) on delete set null,
  add column if not exists job_id uuid,
  add column if not exists agent_step_id bigint references public.agent_steps(id) on delete set null,
  add column if not exists prompt_name text,
  add column if not exists prompt_hash text,
  add column if not exists params jsonb default '{}'::jsonb;

create index if not exists idx_agent_outputs_run
  on public.agent_outputs(pipeline_run_id);
create index if not exists idx_agent_outputs_step
  on public.agent_outputs(agent_step_id);

-- validation_scores: link to pipeline run and agent step
alter table public.validation_scores
  add column if not exists pipeline_run_id bigint references public.pipeline_runs(id) on delete set null,
  add column if not exists agent_step_id bigint references public.agent_steps(id) on delete set null;

create index if not exists idx_validation_scores_run
  on public.validation_scores(pipeline_run_id);
create index if not exists idx_validation_scores_step
  on public.validation_scores(agent_step_id);

-- application_reviews: link to current artifact
alter table public.application_reviews
  add column if not exists current_artifact_id bigint references public.resume_artifacts(id) on delete set null;

-- run_events: add FK to pipeline_runs(job_id)
do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'run_events_job_id_fkey'
      and conrelid = 'public.run_events'::regclass
  ) then
    alter table public.run_events
      add constraint run_events_job_id_fkey
      foreign key (job_id) references public.pipeline_runs(job_id) on delete cascade not valid;
    -- NOT VALID: constraint is not enforced on existing rows.
    -- After confirming no orphan job_id values exist, run:
    --   ALTER TABLE public.run_events VALIDATE CONSTRAINT run_events_job_id_fkey;
  end if;
end;
$$;

-- Additional indexes for common query patterns
create index if not exists idx_pipeline_runs_application
  on public.pipeline_runs(application_id);
create index if not exists idx_application_reviews_user_updated
  on public.application_reviews(user_id, updated_at desc);


-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

-- enable row level security (idempotent)
alter table public.profile_snapshots enable row level security;
alter table public.evidence_items enable row level security;
alter table public.agent_steps enable row level security;
alter table public.resume_artifacts enable row level security;
alter table public.validation_findings enable row level security;
alter table public.model_invocations enable row level security;

-- All create policy statements are wrapped in DO $$ blocks that check
-- pg_policies first, making them safe to re-run.

-- profile_snapshots
do $$
begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='profile_snapshots' and policyname='Users can view own profile_snapshots') then
    create policy "Users can view own profile_snapshots"
      on public.profile_snapshots for select
      using (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='profile_snapshots' and policyname='Users can insert own profile_snapshots') then
    create policy "Users can insert own profile_snapshots"
      on public.profile_snapshots for insert
      with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='profile_snapshots' and policyname='Users can update own profile_snapshots') then
    create policy "Users can update own profile_snapshots"
      on public.profile_snapshots for update
      using (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='profile_snapshots' and policyname='Users can delete own profile_snapshots') then
    create policy "Users can delete own profile_snapshots"
      on public.profile_snapshots for delete
      using (auth.uid() = user_id);
  end if;
end;
$$;

-- evidence_items
do $$
begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='evidence_items' and policyname='Users can view own evidence_items') then
    create policy "Users can view own evidence_items"
      on public.evidence_items for select
      using (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='evidence_items' and policyname='Users can insert own evidence_items') then
    create policy "Users can insert own evidence_items"
      on public.evidence_items for insert
      with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='evidence_items' and policyname='Users can update own evidence_items') then
    create policy "Users can update own evidence_items"
      on public.evidence_items for update
      using (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='evidence_items' and policyname='Users can delete own evidence_items') then
    create policy "Users can delete own evidence_items"
      on public.evidence_items for delete
      using (auth.uid() = user_id);
  end if;
end;
$$;

-- agent_steps
do $$
begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='agent_steps' and policyname='Users can view own agent_steps') then
    create policy "Users can view own agent_steps"
      on public.agent_steps for select
      using (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='agent_steps' and policyname='Users can insert own agent_steps') then
    create policy "Users can insert own agent_steps"
      on public.agent_steps for insert
      with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='agent_steps' and policyname='Users can update own agent_steps') then
    create policy "Users can update own agent_steps"
      on public.agent_steps for update
      using (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='agent_steps' and policyname='Users can delete own agent_steps') then
    create policy "Users can delete own agent_steps"
      on public.agent_steps for delete
      using (auth.uid() = user_id);
  end if;
end;
$$;

-- resume_artifacts
do $$
begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='resume_artifacts' and policyname='Users can view own resume_artifacts') then
    create policy "Users can view own resume_artifacts"
      on public.resume_artifacts for select
      using (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='resume_artifacts' and policyname='Users can insert own resume_artifacts') then
    create policy "Users can insert own resume_artifacts"
      on public.resume_artifacts for insert
      with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='resume_artifacts' and policyname='Users can update own resume_artifacts') then
    create policy "Users can update own resume_artifacts"
      on public.resume_artifacts for update
      using (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='resume_artifacts' and policyname='Users can delete own resume_artifacts') then
    create policy "Users can delete own resume_artifacts"
      on public.resume_artifacts for delete
      using (auth.uid() = user_id);
  end if;
end;
$$;

-- validation_findings
do $$
begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='validation_findings' and policyname='Users can view own validation_findings') then
    create policy "Users can view own validation_findings"
      on public.validation_findings for select
      using (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='validation_findings' and policyname='Users can insert own validation_findings') then
    create policy "Users can insert own validation_findings"
      on public.validation_findings for insert
      with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='validation_findings' and policyname='Users can update own validation_findings') then
    create policy "Users can update own validation_findings"
      on public.validation_findings for update
      using (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='validation_findings' and policyname='Users can delete own validation_findings') then
    create policy "Users can delete own validation_findings"
      on public.validation_findings for delete
      using (auth.uid() = user_id);
  end if;
end;
$$;

-- model_invocations
do $$
begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='model_invocations' and policyname='Users can view own model_invocations') then
    create policy "Users can view own model_invocations"
      on public.model_invocations for select
      using (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='model_invocations' and policyname='Users can insert own model_invocations') then
    create policy "Users can insert own model_invocations"
      on public.model_invocations for insert
      with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='model_invocations' and policyname='Users can update own model_invocations') then
    create policy "Users can update own model_invocations"
      on public.model_invocations for update
      using (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='model_invocations' and policyname='Users can delete own model_invocations') then
    create policy "Users can delete own model_invocations"
      on public.model_invocations for delete
      using (auth.uid() = user_id);
  end if;
end;
$$;

-- Note: Backend uses service_role key which bypasses RLS
