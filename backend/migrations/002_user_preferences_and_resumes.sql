-- Migration 002: User preferences and saved resumes
-- Enables persistent user defaults (LinkedIn, GitHub) and saved resume management.

-- ============================================
-- SAVED RESUMES
-- ============================================

create table if not exists public.saved_resumes (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,

  label text not null,              -- User-given name, e.g. "General", "Tech"
  filename text,                     -- Original upload filename
  resume_text text not null,         -- Extracted resume content
  content_hash text,                 -- SHA-256 hash for dedup
  is_default boolean default false,  -- Whether this is the user's default resume

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_saved_resumes_user on public.saved_resumes(user_id);
create index if not exists idx_saved_resumes_user_default on public.saved_resumes(user_id) where is_default = true;
create index if not exists idx_saved_resumes_content_hash on public.saved_resumes(user_id, content_hash);

create trigger tr_saved_resumes_updated_at
  before update on public.saved_resumes
  for each row execute function public.update_updated_at();


-- ============================================
-- USER PREFERENCES
-- ============================================

create table if not exists public.user_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,

  default_linkedin_url text,
  default_github_username text,
  default_resume_id bigint references public.saved_resumes(id) on delete set null,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger tr_user_preferences_updated_at
  before update on public.user_preferences
  for each row execute function public.update_updated_at();


-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

alter table public.saved_resumes enable row level security;
alter table public.user_preferences enable row level security;

-- Users can manage their own saved resumes
create policy "Users can view own saved_resumes"
  on public.saved_resumes for select
  using (auth.uid() = user_id);

create policy "Users can insert own saved_resumes"
  on public.saved_resumes for insert
  with check (auth.uid() = user_id);

create policy "Users can update own saved_resumes"
  on public.saved_resumes for update
  using (auth.uid() = user_id);

create policy "Users can delete own saved_resumes"
  on public.saved_resumes for delete
  using (auth.uid() = user_id);

-- Users can manage their own preferences
create policy "Users can view own user_preferences"
  on public.user_preferences for select
  using (auth.uid() = user_id);

create policy "Users can insert own user_preferences"
  on public.user_preferences for insert
  with check (auth.uid() = user_id);

create policy "Users can update own user_preferences"
  on public.user_preferences for update
  using (auth.uid() = user_id);

-- Note: Backend uses service_role key which bypasses RLS
