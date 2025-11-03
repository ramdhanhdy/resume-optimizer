# Supabase Auth, Database, and Metering Specification (MVP)

## Context
- Backend: FastAPI on Cloud Run (Procfile/buildpacks). Currently SQLite via `DATABASE_PATH`.
- Frontend: React/Vite. No auth yet.
- Product rule: 5 free resume generations per user, then paywall.
- Decision: Use Supabase for Auth and Postgres (replace SQLite). Stripe for billing.

## Goals and Non-Goals
- Goals
  - Replace SQLite with Supabase Postgres with minimal API changes to backend routes.
  - Add Supabase Auth for user identity; support email/password and social; optional magic links.
  - Enforce per-user usage cap (5/mo by default) and integrate Stripe subscriptions to bypass cap.
  - Keep backend-only DB access using service role; do not expose direct client DB writes in MVP.
- Non-Goals
  - Multi-tenant orgs/roles beyond `user` scope.
  - Complex analytics; basic reporting only.

## Sources (grounding)
- Supabase Docs: Rate limits and MAUs
  - https://supabase.com/docs/guides/auth/rate-limits
  - https://supabase.com/docs/guides/platform/manage-your-usage/monthly-active-users
- Stripe subscriptions/trials
  - https://docs.stripe.com/billing/subscriptions/trials
  - Usage/pricing guides: Stripe, Chargebee, Lago, Stigg

## Architecture Overview
- Auth (Supabase Auth)
  - Frontend signs in users with Supabase (email/password, magic link, or OAuth).
  - Backend receives `Authorization: Bearer <access_token>` for protected endpoints.
  - Backend verifies token using Supabase Admin API (`supabase.auth.get_user(token)`) or JWKS verification, extracts `uid`.

- Database (Supabase Postgres)
  - Replace SQLite with relational tables in `public` schema.
  - JSON fields from SQLite become `jsonb`.
  - Row Level Security (RLS): enabled by default. Backend uses `service_role` key and bypasses RLS in MVP. Client will not call PostgREST directly in MVP.

- Metering (5 free generations)
  - Store per-`uid` usage in `user_usage`.
  - Default policy: monthly cap (resets monthly). Lifetime cap available via config.
  - Enforcement is transactional at the start of generation pipeline.

- Billing (Stripe)
  - Backend endpoint creates Stripe Checkout sessions with `client_reference_id=<uid>`.
  - Webhook updates `subscriptions` table keyed by `uid`.
  - Active subscribers bypass metering limits.

- Deployment
  - Cloud Run env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DB_PROVIDER=supabase`.
  - Keep `CORS_ORIGINS` for frontend domains.

## Database Schema (SQL)

```sql
-- applications
create table if not exists public.applications (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  company_name text,
  job_title text,
  job_posting_text text,
  original_resume_text text,
  optimized_resume_text text,
  model_used text,
  total_cost double precision not null default 0,
  status text not null default 'in_progress',
  notes text
);

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end; $$;

create trigger applications_set_updated_at
before update on public.applications
for each row execute function public.set_updated_at();

-- agent_outputs
create table if not exists public.agent_outputs (
  id bigint generated always as identity primary key,
  application_id bigint not null references public.applications(id) on delete cascade,
  agent_number int,
  agent_name text,
  input_data jsonb,
  output_data jsonb,
  cost double precision not null default 0,
  input_tokens int not null default 0,
  output_tokens int not null default 0,
  created_at timestamptz not null default now()
);

-- validation_scores
create table if not exists public.validation_scores (
  id bigint generated always as identity primary key,
  application_id bigint not null references public.applications(id) on delete cascade,
  requirements_match double precision,
  ats_optimization double precision,
  cultural_fit double precision,
  presentation_quality double precision,
  competitive_positioning double precision,
  overall_score double precision,
  red_flags jsonb,
  recommendations jsonb,
  created_at timestamptz not null default now()
);

-- profiles
create table if not exists public.profiles (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  sources jsonb,
  profile_text text,
  profile_index text
);

create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

-- recovery_sessions
create table if not exists public.recovery_sessions (
  id bigint generated always as identity primary key,
  session_id text unique,
  form_data jsonb,
  file_metadata jsonb,
  status text not null default 'pending',
  completed_agents jsonb not null default '[]',
  ip_address text,
  user_agent text,
  expires_at timestamptz,
  last_retry_at timestamptz,
  retry_count int not null default 0,
  application_id bigint references public.applications(id),
  error_id text,
  error_type text,
  error_category text,
  error_message text
);

-- agent_checkpoints
create table if not exists public.agent_checkpoints (
  id bigint generated always as identity primary key,
  session_id text references public.recovery_sessions(session_id) on delete cascade,
  agent_index int,
  agent_name text,
  agent_output jsonb,
  execution_time_ms int,
  model_used text,
  tokens_used int,
  cost_usd double precision
);

-- error_logs
create table if not exists public.error_logs (
  id bigint generated always as identity primary key,
  error_id text,
  session_id text,
  error_type text,
  error_category text,
  error_message text,
  error_stacktrace text,
  request_path text,
  request_method text,
  user_agent text,
  ip_address text,
  additional_context jsonb,
  created_at timestamptz not null default now()
);

-- user_usage (metering)
create table if not exists public.user_usage (
  uid uuid primary key,
  generation_count int not null default 0,
  lifetime_generation_count int not null default 0,
  period_started_at timestamptz not null default date_trunc('month', now())
);

-- subscriptions
create table if not exists public.subscriptions (
  uid uuid primary key,
  status text not null default 'none' check (status in ('none','active','past_due','canceled')),
  plan_id text,
  customer_id text,
  current_period_end timestamptz
);

-- RPC for metering (monthly cap of 5)
create or replace function public.check_and_increment_usage(p_uid uuid, p_cap int default 5)
returns table(allowed boolean, remaining int) language plpgsql as $$
declare v_usage public.user_usage; v_now timestamptz := now();
begin
  select * into v_usage from public.user_usage where uid = p_uid for update;
  if not found then
    insert into public.user_usage(uid) values (p_uid) returning * into v_usage;
  end if;
  if v_usage.period_started_at < date_trunc('month', v_now) then
    update public.user_usage set generation_count = 0, period_started_at = date_trunc('month', v_now) where uid = p_uid returning * into v_usage;
  end if;
  if (select status from public.subscriptions where uid = p_uid) = 'active' then
    update public.user_usage set lifetime_generation_count = lifetime_generation_count + 1 where uid = p_uid;
    return query select true as allowed, null::int as remaining;
  end if;
  if v_usage.generation_count >= p_cap then
    return query select false as allowed, 0 as remaining;
  end if;
  update public.user_usage set generation_count = generation_count + 1, lifetime_generation_count = lifetime_generation_count + 1 where uid = p_uid returning * into v_usage;
  return query select true as allowed, (p_cap - v_usage.generation_count) as remaining;
end $$;
```

Notes
- Backend uses `service_role` and bypasses RLS for MVP. If exposing PostgREST to clients later, add RLS policies keyed by `auth.uid()`.

## Backend Implementation Plan
- Dependencies (`backend/requirements.txt`)
  - `supabase>=2.5.0`
  - `python-jose[cryptography]>=3.3.0` (if verifying JWT locally via JWKS) or use `supabase.auth.get_user(token)` with service role.
- DB adapter
  - Add `SupabaseDatabase` mirroring `ApplicationDatabase` methods using Supabase PostgREST:
    - `create_application`, `update_application`, `get_application`, `get_all_applications`, `delete_application`
    - `save_agent_output`, `get_agent_outputs`
    - `save_validation_scores`, `get_validation_scores`
    - `save_profile`, `get_latest_profile`
    - `create_recovery_session`, `get_recovery_session`, `update_recovery_session`
    - `save_agent_checkpoint`, `get_agent_checkpoints`
    - `log_error`, `cleanup_expired_sessions`
- Auth guard (FastAPI dependency)
  - Extract token from `Authorization` header.
  - Option A: Call `supabase.auth.get_user(token)` to validate and obtain `uid`.
  - Option B: Verify JWT with Supabase JWKS (`https://<project>.supabase.co/auth/v1/jwks`) using `python-jose`.
  - Inject `uid` into handlers.
- Metering enforcement
  - On `/api/pipeline/start`, call RPC `check_and_increment_usage(uid)`.
  - If `allowed=false`, return 402 with `{ code: 'LIMIT_REACHED', remaining: 0 }`.
  - Include `remaining` in success responses for UI meter.
- Stripe integration
  - Endpoint: `/api/billing/create-checkout-session` (plan config in server). Include `client_reference_id=<uid>` and `customer_metadata.uid=<uid>`.
  - Webhook: handle `checkout.session.completed`, `customer.subscription.updated/deleted` and upsert into `public.subscriptions`.
  - Active subscribers bypass cap in RPC.
- Configuration and env
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `DB_PROVIDER=supabase`

## Frontend Implementation Plan
- Use Supabase JS SDK for Auth (email/password or magic link).
- Persist session; fetch `access_token` and attach as `Authorization: Bearer` for protected routes.
- Show a usage meter; on 402, open Stripe checkout.

## Data Migration from SQLite
- Order:
  - applications → agent_outputs, validation_scores → profiles → recovery_sessions → agent_checkpoints → error_logs.
- Strategy:
  - Create a one-off Python script reading from SQLite and inserting into Supabase via admin client.
  - Preserve referential integrity (map application IDs to generated IDs if needed; or insert with specific IDs using identity override if you must keep numbers—recommended to let identity auto-generate and store a mapping for child tables).

## Security & RLS
- MVP: Only backend with `service_role` accesses PostgREST; RLS can remain default (enabled) as service role bypasses it.
- If exposing any client queries later, add RLS policies, e.g. on `user_usage`/`subscriptions`:

```sql
alter table public.user_usage enable row level security;
create policy select_own_usage on public.user_usage for select using (uid = auth.uid());
```

- Rotate `SUPABASE_SERVICE_ROLE_KEY` periodically; never expose to frontend.

## Observability
- Add structured logging around RPC calls and Stripe webhooks.
- Consider Supabase Logs for PostgREST and function calls.

## Acceptance Criteria
- Users authenticate with Supabase; backend verifies token and resolves `uid`.
- On first 5 monthly generations, pipeline starts and decrements remaining; `remaining` is returned.
- On the 6th attempt without subscription, API returns 402 with `LIMIT_REACHED`.
- After subscription becomes `active`, user can generate without hitting the cap.
- All CRUD routes backed by Supabase work as before; existing UI unaffected.

## Next Steps
- Provision Supabase project; share `SUPABASE_URL` and a service role key securely.
- I will: add dependencies, implement `SupabaseDatabase`, wire auth guard, add RPC + DDL, and provide a one-off migration script.
