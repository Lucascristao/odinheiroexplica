
create index if not exists project_sources_project_owner_idx
  on public.project_sources (project_id, owner_id);

create index if not exists project_claims_project_owner_idx
  on public.project_claims (project_id, owner_id);

create index if not exists project_scenes_project_owner_idx
  on public.project_scenes (project_id, owner_id);

create index if not exists render_jobs_project_owner_idx
  on public.render_jobs (project_id, owner_id);

create index if not exists publications_project_owner_idx
  on public.publications (project_id, owner_id);
