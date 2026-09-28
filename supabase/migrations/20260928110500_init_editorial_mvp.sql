create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table public.video_projects (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  schema_version text not null default '1.0',
  status text not null default 'IMPORTED'
    check (status in (
      'IDEA','RESEARCHED','IMPORTED','VALIDATING','READY_TO_RENDER',
      'RENDERING','READY_TO_REVIEW','APPROVED','UPLOADED','PUBLISHED',
      'ANALYZING','ARCHIVED','ERROR'
    )),
  subject text not null,
  angle text,
  promise text,
  category text check (category is null or category in ('news','company','economy','money','evergreen')),
  viral_score smallint check (viral_score is null or viral_score between 0 and 100),
  risk_flags text[] not null default '{}',
  raw_payload jsonb not null default '{}'::jsonb,
  duration_seconds numeric(10,2),
  drive_file_id text,
  youtube_video_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  published_at timestamptz,
  unique (id, owner_id)
);

create index video_projects_owner_created_idx on public.video_projects (owner_id, created_at desc);
create index video_projects_owner_status_idx on public.video_projects (owner_id, status);

create trigger video_projects_set_updated_at
before update on public.video_projects
for each row execute function public.set_updated_at();

create table public.project_sources (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null,
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  source_key text,
  title text,
  url text not null,
  publisher text,
  source_type text check (source_type is null or source_type in ('primary','secondary','context')),
  published_at timestamptz,
  accessed_at timestamptz not null default now(),
  license text,
  notes text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  foreign key (project_id, owner_id) references public.video_projects (id, owner_id) on delete cascade,
  unique (project_id, source_key)
);

create table public.project_claims (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null,
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  claim_key text,
  claim_text text not null,
  confidence text not null default 'medium' check (confidence in ('low','medium','high')),
  verification_status text not null default 'unverified'
    check (verification_status in ('unverified','verified','conflicting','rejected')),
  source_keys text[] not null default '{}',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  foreign key (project_id, owner_id) references public.video_projects (id, owner_id) on delete cascade,
  unique (project_id, claim_key)
);

create table public.project_scenes (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null,
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  scene_index integer not null check (scene_index >= 0),
  title text,
  narration text not null default '',
  visual_type text,
  visual_payload jsonb not null default '{}'::jsonb,
  claim_keys text[] not null default '{}',
  audio_duration_seconds numeric(10,2),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  foreign key (project_id, owner_id) references public.video_projects (id, owner_id) on delete cascade,
  unique (project_id, scene_index)
);

create trigger project_scenes_set_updated_at
before update on public.project_scenes
for each row execute function public.set_updated_at();

create table public.render_jobs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null,
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  status text not null default 'queued' check (status in ('queued','running','completed','failed','cancelled')),
  stage text,
  progress smallint not null default 0 check (progress between 0 and 100),
  github_run_id text,
  error_message text,
  output_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  started_at timestamptz,
  finished_at timestamptz,
  foreign key (project_id, owner_id) references public.video_projects (id, owner_id) on delete cascade
);

create table public.publications (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null,
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  status text not null default 'draft' check (status in ('draft','ready','uploaded','published','failed')),
  title text,
  description text,
  thumbnail_variant text,
  youtube_video_id text,
  youtube_url text,
  published_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  foreign key (project_id, owner_id) references public.video_projects (id, owner_id) on delete cascade,
  unique (project_id)
);

create trigger publications_set_updated_at
before update on public.publications
for each row execute function public.set_updated_at();

create index project_sources_project_idx on public.project_sources (project_id);
create index project_sources_owner_idx on public.project_sources (owner_id);
create index project_claims_project_idx on public.project_claims (project_id);
create index project_claims_owner_idx on public.project_claims (owner_id);
create index project_scenes_project_order_idx on public.project_scenes (project_id, scene_index);
create index project_scenes_owner_idx on public.project_scenes (owner_id);
create index render_jobs_project_created_idx on public.render_jobs (project_id, created_at desc);
create index render_jobs_owner_status_idx on public.render_jobs (owner_id, status);
create index publications_owner_status_idx on public.publications (owner_id, status);

alter table public.video_projects enable row level security;
alter table public.project_sources enable row level security;
alter table public.project_claims enable row level security;
alter table public.project_scenes enable row level security;
alter table public.render_jobs enable row level security;
alter table public.publications enable row level security;

grant select, insert, update, delete on
  public.video_projects,
  public.project_sources,
  public.project_claims,
  public.project_scenes,
  public.render_jobs,
  public.publications
to authenticated;

create policy "video_projects_owner_all" on public.video_projects for all to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

create policy "project_sources_owner_all" on public.project_sources for all to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

create policy "project_claims_owner_all" on public.project_claims for all to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

create policy "project_scenes_owner_all" on public.project_scenes for all to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

create policy "render_jobs_owner_all" on public.render_jobs for all to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = owner_id);

create policy "publications_owner_all" on public.publications for all to authenticated
using ((select auth.uid()) is not null and (select auth.uid()) = owner_id)
with check ((select auth.uid()) is not null and (select auth.uid()) = owner_id);
