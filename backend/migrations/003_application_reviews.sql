-- Migration 003: Canonical application review documents for frontend_v2

create table if not exists public.application_reviews (
  application_id bigint primary key references public.applications(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,

  plain_text text not null,
  markdown text not null,
  filename text not null,
  summary_points jsonb not null default '[]'::jsonb,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_application_reviews_user on public.application_reviews(user_id);
create index if not exists idx_application_reviews_created on public.application_reviews(created_at desc);

create trigger tr_application_reviews_updated_at
  before update on public.application_reviews
  for each row execute function public.update_updated_at();

alter table public.application_reviews enable row level security;

create policy "Users can view own application_reviews"
  on public.application_reviews for select
  using (
    auth.uid() = user_id
    and exists (
      select 1
      from public.applications
      where public.applications.id = application_reviews.application_id
        and public.applications.user_id = auth.uid()
    )
  );

create policy "Users can insert own application_reviews"
  on public.application_reviews for insert
  with check (
    auth.uid() = user_id
    and exists (
      select 1
      from public.applications
      where public.applications.id = application_reviews.application_id
        and public.applications.user_id = auth.uid()
    )
  );

create policy "Users can update own application_reviews"
  on public.application_reviews for update
  using (
    auth.uid() = user_id
    and exists (
      select 1
      from public.applications
      where public.applications.id = application_reviews.application_id
        and public.applications.user_id = auth.uid()
    )
  )
  with check (
    auth.uid() = user_id
    and exists (
      select 1
      from public.applications
      where public.applications.id = application_reviews.application_id
        and public.applications.user_id = auth.uid()
    )
  );
