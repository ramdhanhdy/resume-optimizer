alter table public.recovery_sessions
  drop constraint if exists recovery_sessions_status_check;

alter table public.recovery_sessions
  add constraint recovery_sessions_status_check
  check (status in (
    'pending',
    'processing',
    'failed',
    'recovered',
    'deleted',
    'in_progress',
    'expired',
    'abandoned'
  ));

alter table public.error_logs
  alter column error_id drop default;

alter table public.error_logs
  alter column error_id type text using error_id::text;

alter table public.error_logs
  alter column error_id set default gen_random_uuid()::text;
