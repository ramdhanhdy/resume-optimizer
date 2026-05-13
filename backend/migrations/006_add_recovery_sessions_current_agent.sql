alter table public.recovery_sessions
  add column if not exists current_agent int;

alter table public.recovery_sessions
  drop constraint if exists recovery_sessions_current_agent_check;

alter table public.recovery_sessions
  add constraint recovery_sessions_current_agent_check
  check (current_agent is null or (current_agent >= 0 and current_agent <= 4));
