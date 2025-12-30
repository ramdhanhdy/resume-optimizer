# Supabase PostgreSQL Schema v2 - Analytics-Optimized

## Current SQLite Database Issues (Findings from Inspection)

### Critical Data Quality Problems:
| Issue | Count | Impact |
|-------|-------|--------|
| Placeholder `company_name` = "Company" | 122/122 (100%) | No company data captured |
| Placeholder `job_title` = "Position" | 122/122 (100%) | No job title captured |
| All `status` = "in_progress" | 122/122 (100%) | Can't track completion |
| Zero `total_cost` | 122/122 (100%) | Cost tracking broken |
| Zero tokens in agent_outputs | 383/511 (75%) | Token usage not recorded |
| Zero cost in agent_outputs | 383/511 (75%) | Per-agent costs missing |

### Schema Design Gaps:
1. **No job_url column** - URL lost after fetching
2. **No model_provider column** - Can't distinguish OpenRouter vs Gemini vs Anthropic
3. **No user_id** - Pre-auth, all data mixed together
4. **Status never updated** - Pipeline doesn't mark completed/failed
5. **Cost triggers missing** - `total_cost` never aggregated from agent_outputs
6. **No completion timestamp** - Can't measure pipeline duration

---

## Design Principles

1. **User-Centric**: All data tied to `user_id` for multi-tenant isolation and per-user analytics
2. **Denormalized for Analytics**: Key metrics pre-computed; avoid expensive JOINs for dashboards
3. **Time-Series Ready**: Proper timestamps and partitioning-friendly structure
4. **Cost Tracking**: Granular LLM cost tracking per agent, model, and user
5. **Audit Trail**: Full history of all operations for debugging and analysis
6. **Data Quality Enforcement**: NOT NULL constraints, CHECK constraints, and triggers to prevent bad data

---

## Schema Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│     users       │────<│   applications   │────<│  agent_outputs  │
│  (Supabase Auth)│     └──────────────────┘     └─────────────────┘
└─────────────────┘              │                        │
        │                        │                        │
        │                        ▼                        │
        │               ┌──────────────────┐              │
        │               │validation_scores │              │
        │               └──────────────────┘              │
        │                                                 │
        ▼                                                 ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   user_usage    │     │    profiles      │     │  llm_requests   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │
        │                        │
        ▼                        ▼
┌─────────────────┐     ┌──────────────────┐
│  subscriptions  │     │  pipeline_runs   │
└─────────────────┘     └──────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │   run_events     │
                        └──────────────────┘
```

---

## Core Tables

### 1. `applications` - Resume Optimization Jobs

```sql
create table public.applications (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  
  -- Job Details
  company_name text,
  job_title text,
  job_url text,
  job_posting_text text,
  
  -- Resume Data
  original_resume_text text,
  optimized_resume_text text,
  
  -- Denormalized Metrics (for fast queries)
  overall_score numeric(5,2),
  total_cost_usd numeric(10,6) default 0,
  total_input_tokens int default 0,
  total_output_tokens int default 0,
  
  -- Status & Metadata
  status text not null default 'pending' 
    check (status in ('pending', 'processing', 'completed', 'failed', 'cancelled')),
  model_used text,
  pipeline_version text default 'v1',
  
  -- Timestamps
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz,
  
  -- Soft delete
  deleted_at timestamptz
);

-- Indexes for common queries
create index idx_applications_user_id on public.applications(user_id);
create index idx_applications_user_created on public.applications(user_id, created_at desc);
create index idx_applications_status on public.applications(status) where deleted_at is null;
create index idx_applications_created_at on public.applications(created_at desc);
```

### 2. `agent_outputs` - Per-Agent Execution Results

```sql
create table public.agent_outputs (
  id bigint generated always as identity primary key,
  application_id bigint not null references public.applications(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  
  -- Agent Identity
  agent_name text not null,
  agent_number int not null,
  
  -- Model & Cost Tracking
  model_provider text,  -- 'openai', 'anthropic', 'google', 'openrouter'
  model_name text,      -- 'gpt-4', 'claude-3-opus', etc.
  
  -- Token Usage
  input_tokens int not null default 0,
  output_tokens int not null default 0,
  total_tokens int generated always as (input_tokens + output_tokens) stored,
  
  -- Cost (in USD, 6 decimal precision for micro-costs)
  cost_usd numeric(10,6) not null default 0,
  
  -- Execution Metrics
  execution_time_ms int,
  retry_count int default 0,
  
  -- Data (JSONB for flexibility)
  input_data jsonb,
  output_data jsonb,
  
  -- Quality Metrics (optional, agent-specific)
  quality_score numeric(5,2),
  
  -- Timestamps
  created_at timestamptz not null default now(),
  
  -- Ensure ordering
  constraint unique_agent_per_app unique (application_id, agent_number)
);

-- Indexes
create index idx_agent_outputs_app_id on public.agent_outputs(application_id);
create index idx_agent_outputs_user_id on public.agent_outputs(user_id);
create index idx_agent_outputs_model on public.agent_outputs(model_provider, model_name);
create index idx_agent_outputs_created on public.agent_outputs(created_at desc);
```

### 3. `validation_scores` - Quality Assessment

```sql
create table public.validation_scores (
  id bigint generated always as identity primary key,
  application_id bigint not null references public.applications(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  
  -- Score Dimensions (0-100 scale)
  requirements_match numeric(5,2),
  ats_optimization numeric(5,2),
  cultural_fit numeric(5,2),
  presentation_quality numeric(5,2),
  competitive_positioning numeric(5,2),
  overall_score numeric(5,2),
  
  -- Detailed Feedback
  red_flags jsonb default '[]'::jsonb,
  recommendations jsonb default '[]'::jsonb,
  strengths jsonb default '[]'::jsonb,
  
  -- Model used for validation
  model_name text,
  
  -- Timestamps
  created_at timestamptz not null default now()
);

create index idx_validation_scores_app on public.validation_scores(application_id);
create index idx_validation_scores_user on public.validation_scores(user_id);
create index idx_validation_scores_overall on public.validation_scores(overall_score desc);
```

### 4. `profiles` - User Profile Memory

```sql
create table public.profiles (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  
  -- Profile Data
  sources jsonb default '[]'::jsonb,  -- ['linkedin:url', 'github:username', 'resume:hash']
  profile_text text,
  profile_index jsonb,  -- Structured profile data
  
  -- Metadata
  is_active boolean default true,
  version int default 1,
  
  -- Timestamps
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_profiles_user on public.profiles(user_id);
create index idx_profiles_user_active on public.profiles(user_id) where is_active = true;
```

---

## Usage & Billing Tables

### 5. `user_usage` - Metering

```sql
create table public.user_usage (
  user_id uuid primary key references auth.users(id) on delete cascade,
  
  -- Current Period
  period_start timestamptz not null default date_trunc('month', now()),
  generation_count int not null default 0,
  
  -- Lifetime Stats
  lifetime_generations int not null default 0,
  lifetime_cost_usd numeric(12,6) default 0,
  lifetime_input_tokens bigint default 0,
  lifetime_output_tokens bigint default 0,
  
  -- Timestamps
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

### 6. `subscriptions` - Stripe Integration

```sql
create table public.subscriptions (
  user_id uuid primary key references auth.users(id) on delete cascade,
  
  -- Stripe Data
  stripe_customer_id text unique,
  stripe_subscription_id text unique,
  
  -- Plan Details
  plan_id text,
  plan_name text,
  
  -- Status
  status text not null default 'none' 
    check (status in ('none', 'trialing', 'active', 'past_due', 'canceled', 'unpaid')),
  
  -- Billing Period
  current_period_start timestamptz,
  current_period_end timestamptz,
  cancel_at_period_end boolean default false,
  
  -- Timestamps
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_subscriptions_status on public.subscriptions(status);
create index idx_subscriptions_stripe_customer on public.subscriptions(stripe_customer_id);
```

---

## Pipeline Execution Tables

### 7. `pipeline_runs` - Job Execution Tracking

```sql
create table public.pipeline_runs (
  id bigint generated always as identity primary key,
  job_id uuid unique not null default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  application_id bigint references public.applications(id) on delete set null,
  
  -- Status
  status text not null default 'queued'
    check (status in ('queued', 'running', 'completed', 'failed', 'cancelled')),
  
  -- Progress
  current_step text,
  steps_completed int default 0,
  total_steps int default 5,
  progress_percent numeric(5,2) default 0,
  
  -- Error Info
  error_type text,
  error_message text,
  
  -- Timing
  started_at timestamptz,
  completed_at timestamptz,
  duration_ms int,
  
  -- Metadata
  client_ip text,
  user_agent text,
  
  -- Timestamps
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_pipeline_runs_user on public.pipeline_runs(user_id);
create index idx_pipeline_runs_job_id on public.pipeline_runs(job_id);
create index idx_pipeline_runs_status on public.pipeline_runs(status);
create index idx_pipeline_runs_created on public.pipeline_runs(created_at desc);
```

### 8. `run_events` - SSE Event Log

```sql
create table public.run_events (
  id bigint generated always as identity primary key,
  job_id uuid not null,
  seq int not null,
  
  -- Event Data
  event_type text not null,
  payload jsonb,
  
  -- Timestamp (milliseconds since epoch for SSE)
  ts bigint,
  created_at timestamptz not null default now(),
  
  constraint unique_job_seq unique (job_id, seq)
);

create index idx_run_events_job_seq on public.run_events(job_id, seq);
```

---

## Recovery & Error Tables

### 9. `recovery_sessions` - Error Recovery

```sql
create table public.recovery_sessions (
  id bigint generated always as identity primary key,
  session_id uuid unique not null default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  application_id bigint references public.applications(id) on delete set null,
  
  -- Form State
  form_data jsonb,
  file_metadata jsonb,
  
  -- Recovery State
  status text not null default 'pending'
    check (status in ('pending', 'in_progress', 'recovered', 'expired', 'abandoned')),
  completed_agents jsonb default '[]'::jsonb,
  
  -- Error Info
  error_id text,
  error_type text,
  error_category text,
  error_message text,
  
  -- Retry Tracking
  retry_count int default 0,
  last_retry_at timestamptz,
  
  -- Client Info
  ip_address text,
  user_agent text,
  
  -- Expiry
  expires_at timestamptz default (now() + interval '7 days'),
  
  -- Timestamps
  created_at timestamptz not null default now()
);

create index idx_recovery_sessions_user on public.recovery_sessions(user_id);
create index idx_recovery_sessions_session_id on public.recovery_sessions(session_id);
create index idx_recovery_sessions_status on public.recovery_sessions(status);
```

### 10. `agent_checkpoints` - Recovery Checkpoints

```sql
create table public.agent_checkpoints (
  id bigint generated always as identity primary key,
  session_id uuid not null references public.recovery_sessions(session_id) on delete cascade,
  
  -- Agent Info
  agent_index int not null,
  agent_name text not null,
  
  -- Output
  agent_output jsonb,
  
  -- Metrics
  execution_time_ms int,
  model_used text,
  tokens_used int,
  cost_usd numeric(10,6),
  
  -- Timestamps
  created_at timestamptz not null default now(),
  
  constraint unique_checkpoint unique (session_id, agent_index)
);

create index idx_agent_checkpoints_session on public.agent_checkpoints(session_id);
```

### 11. `error_logs` - Error Tracking

```sql
create table public.error_logs (
  id bigint generated always as identity primary key,
  error_id uuid unique not null default gen_random_uuid(),
  
  -- Context
  user_id uuid references auth.users(id) on delete set null,
  session_id uuid,
  application_id bigint,
  
  -- Error Details
  error_type text,
  error_category text check (error_category in ('TRANSIENT', 'RECOVERABLE', 'PERMANENT')),
  error_message text,
  error_stacktrace text,
  
  -- Request Context
  request_path text,
  request_method text,
  
  -- Client Info
  user_agent text,
  ip_address text,
  
  -- Additional Data
  additional_context jsonb,
  
  -- Timestamps
  created_at timestamptz not null default now()
);

create index idx_error_logs_user on public.error_logs(user_id);
create index idx_error_logs_type on public.error_logs(error_type);
create index idx_error_logs_category on public.error_logs(error_category);
create index idx_error_logs_created on public.error_logs(created_at desc);
```

---

## Analytics Tables (Materialized/Aggregated)

### 12. `daily_stats` - Daily Aggregates

```sql
create table public.daily_stats (
  id bigint generated always as identity primary key,
  date date not null,
  user_id uuid references auth.users(id) on delete cascade,
  
  -- Counts
  applications_created int default 0,
  applications_completed int default 0,
  applications_failed int default 0,
  
  -- Costs
  total_cost_usd numeric(12,6) default 0,
  total_input_tokens bigint default 0,
  total_output_tokens bigint default 0,
  
  -- Quality
  avg_overall_score numeric(5,2),
  
  -- Unique constraint
  constraint unique_daily_user unique (date, user_id)
);

create index idx_daily_stats_date on public.daily_stats(date desc);
create index idx_daily_stats_user on public.daily_stats(user_id);
```

### 13. `model_usage_stats` - Per-Model Analytics

```sql
create table public.model_usage_stats (
  id bigint generated always as identity primary key,
  date date not null,
  model_provider text not null,
  model_name text not null,
  agent_name text,
  
  -- Usage
  request_count int default 0,
  total_input_tokens bigint default 0,
  total_output_tokens bigint default 0,
  total_cost_usd numeric(12,6) default 0,
  
  -- Performance
  avg_execution_time_ms int,
  error_count int default 0,
  
  constraint unique_model_daily unique (date, model_provider, model_name, agent_name)
);

create index idx_model_usage_date on public.model_usage_stats(date desc);
create index idx_model_usage_provider on public.model_usage_stats(model_provider, model_name);
```

---

## Functions & Triggers

### Auto-Update Timestamps

```sql
create or replace function public.update_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- Apply to relevant tables
create trigger tr_applications_updated_at
  before update on public.applications
  for each row execute function public.update_updated_at();

create trigger tr_profiles_updated_at
  before update on public.profiles
  for each row execute function public.update_updated_at();

create trigger tr_user_usage_updated_at
  before update on public.user_usage
  for each row execute function public.update_updated_at();

create trigger tr_subscriptions_updated_at
  before update on public.subscriptions
  for each row execute function public.update_updated_at();

create trigger tr_pipeline_runs_updated_at
  before update on public.pipeline_runs
  for each row execute function public.update_updated_at();
```

### Metering Function

```sql
create or replace function public.check_and_increment_usage(
  p_user_id uuid,
  p_cap int default 5
)
returns table(allowed boolean, remaining int, is_subscribed boolean)
language plpgsql
security definer
as $$
declare
  v_usage public.user_usage;
  v_subscription public.subscriptions;
  v_now timestamptz := now();
begin
  -- Get or create usage record
  select * into v_usage from public.user_usage where user_id = p_user_id for update;
  
  if not found then
    insert into public.user_usage(user_id) values (p_user_id) returning * into v_usage;
  end if;
  
  -- Reset if new month
  if v_usage.period_start < date_trunc('month', v_now) then
    update public.user_usage 
    set generation_count = 0, period_start = date_trunc('month', v_now)
    where user_id = p_user_id 
    returning * into v_usage;
  end if;
  
  -- Check subscription
  select * into v_subscription from public.subscriptions where user_id = p_user_id;
  
  if v_subscription.status = 'active' then
    -- Subscriber: always allowed, increment lifetime
    update public.user_usage 
    set lifetime_generations = lifetime_generations + 1
    where user_id = p_user_id;
    
    return query select true, null::int, true;
    return;
  end if;
  
  -- Free user: check cap
  if v_usage.generation_count >= p_cap then
    return query select false, 0, false;
    return;
  end if;
  
  -- Increment and return
  update public.user_usage 
  set generation_count = generation_count + 1,
      lifetime_generations = lifetime_generations + 1
  where user_id = p_user_id 
  returning * into v_usage;
  
  return query select true, (p_cap - v_usage.generation_count)::int, false;
end;
$$;
```

### Update Application Totals Trigger

```sql
create or replace function public.update_application_totals()
returns trigger language plpgsql as $$
begin
  update public.applications
  set 
    total_cost_usd = (
      select coalesce(sum(cost_usd), 0) 
      from public.agent_outputs 
      where application_id = new.application_id
    ),
    total_input_tokens = (
      select coalesce(sum(input_tokens), 0) 
      from public.agent_outputs 
      where application_id = new.application_id
    ),
    total_output_tokens = (
      select coalesce(sum(output_tokens), 0) 
      from public.agent_outputs 
      where application_id = new.application_id
    )
  where id = new.application_id;
  
  return new;
end;
$$;

create trigger tr_agent_outputs_update_totals
  after insert or update on public.agent_outputs
  for each row execute function public.update_application_totals();
```

### Update Validation Score on Application

```sql
create or replace function public.update_application_score()
returns trigger language plpgsql as $$
begin
  update public.applications
  set overall_score = new.overall_score
  where id = new.application_id;
  
  return new;
end;
$$;

create trigger tr_validation_scores_update_app
  after insert or update on public.validation_scores
  for each row execute function public.update_application_score();
```

---

## Row Level Security (RLS)

```sql
-- Enable RLS on all user-facing tables
alter table public.applications enable row level security;
alter table public.agent_outputs enable row level security;
alter table public.validation_scores enable row level security;
alter table public.profiles enable row level security;
alter table public.user_usage enable row level security;
alter table public.subscriptions enable row level security;
alter table public.pipeline_runs enable row level security;
alter table public.recovery_sessions enable row level security;
alter table public.error_logs enable row level security;

-- Policies: Users can only see their own data
create policy "Users can view own applications"
  on public.applications for select
  using (auth.uid() = user_id);

create policy "Users can view own agent_outputs"
  on public.agent_outputs for select
  using (auth.uid() = user_id);

create policy "Users can view own validation_scores"
  on public.validation_scores for select
  using (auth.uid() = user_id);

create policy "Users can view own profiles"
  on public.profiles for select
  using (auth.uid() = user_id);

create policy "Users can view own usage"
  on public.user_usage for select
  using (auth.uid() = user_id);

create policy "Users can view own subscription"
  on public.subscriptions for select
  using (auth.uid() = user_id);

create policy "Users can view own pipeline_runs"
  on public.pipeline_runs for select
  using (auth.uid() = user_id);

create policy "Users can view own recovery_sessions"
  on public.recovery_sessions for select
  using (auth.uid() = user_id);

-- Note: Backend uses service_role key which bypasses RLS
```

---

## Sample Analytics Queries

### User Dashboard Stats
```sql
select 
  count(*) as total_applications,
  count(*) filter (where status = 'completed') as completed,
  avg(overall_score) as avg_score,
  sum(total_cost_usd) as total_spent
from applications
where user_id = $1 and deleted_at is null;
```

### Cost by Model (Admin)
```sql
select 
  model_provider,
  model_name,
  count(*) as requests,
  sum(cost_usd) as total_cost,
  avg(execution_time_ms) as avg_time_ms
from agent_outputs
where created_at >= now() - interval '30 days'
group by model_provider, model_name
order by total_cost desc;
```

### Daily Active Users
```sql
select 
  date_trunc('day', created_at) as day,
  count(distinct user_id) as dau
from applications
where created_at >= now() - interval '30 days'
group by 1
order by 1;
```

---

## Migration Notes

1. **ID Mapping**: SQLite uses auto-increment integers; Postgres uses `bigint generated always as identity`. IDs will change during migration.

2. **User Assignment**: Existing data has no `user_id`. Options:
   - Assign to a "legacy" system user
   - Map `client_id` patterns to users if identifiable
   - Leave `user_id` nullable for legacy data

3. **JSONB Conversion**: SQLite TEXT JSON fields → Postgres JSONB (validates JSON)

4. **Timestamps**: SQLite `CURRENT_TIMESTAMP` → Postgres `timestamptz`
