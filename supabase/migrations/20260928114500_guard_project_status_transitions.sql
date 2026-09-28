
create or replace function public.transition_video_project_status(
  p_project_id uuid,
  p_expected_status text,
  p_new_status text
)
returns public.video_projects
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_owner uuid := auth.uid();
  v_current public.video_projects;
  v_row public.video_projects;
  v_allowed boolean := false;
  v_hard_flags text[] := array[
    'RUMOR_NAO_CONFIRMADO',
    'FONTE_INSUFICIENTE',
    'TITULO_NAO_SUPORTADO_PELOS_FATOS',
    'RECOMENDACAO_FINANCEIRA',
    'PROMESSA_DE_GANHO',
    'URGENCIA_ARTIFICIAL',
    'RISCO_COPYRIGHT',
    'DADO_CONFLITANTE'
  ];
begin
  if v_owner is null then
    raise exception 'authentication_required';
  end if;

  select *
  into v_current
  from public.video_projects
  where id = p_project_id
    and owner_id = v_owner;

  if v_current.id is null then
    raise exception 'project_not_found';
  end if;

  if v_current.status <> p_expected_status then
    raise exception 'state_changed';
  end if;

  v_allowed :=
    (p_expected_status = 'IMPORTED' and p_new_status = 'VALIDATING')
    or (p_expected_status = 'VALIDATING' and p_new_status in ('IMPORTED', 'READY_TO_RENDER'))
    or (p_expected_status = 'READY_TO_RENDER' and p_new_status in ('VALIDATING', 'RENDERING'))
    or (p_expected_status = 'RENDERING' and p_new_status in ('READY_TO_REVIEW', 'ERROR'))
    or (p_expected_status = 'READY_TO_REVIEW' and p_new_status in ('VALIDATING', 'APPROVED'))
    or (p_expected_status = 'APPROVED' and p_new_status in ('READY_TO_REVIEW', 'UPLOADED'))
    or (p_expected_status = 'UPLOADED' and p_new_status in ('APPROVED', 'PUBLISHED'))
    or (p_expected_status = 'PUBLISHED' and p_new_status = 'ANALYZING')
    or (p_expected_status = 'ANALYZING' and p_new_status in ('PUBLISHED', 'ARCHIVED'))
    or (p_expected_status = 'ERROR' and p_new_status in ('VALIDATING', 'READY_TO_RENDER'));

  if not v_allowed then
    raise exception 'transition_not_allowed';
  end if;

  if p_new_status = 'READY_TO_RENDER' then
    if v_current.risk_flags && v_hard_flags then
      raise exception 'editorial_blockers_present';
    end if;

    if exists (
      select 1
      from public.project_claims c
      where c.project_id = p_project_id
        and c.owner_id = v_owner
        and (
          c.verification_status <> 'verified'
          or coalesce(array_length(c.source_keys, 1), 0) = 0
        )
    ) then
      raise exception 'claims_not_ready';
    end if;

    if not exists (
      select 1
      from public.project_scenes s
      where s.project_id = p_project_id
        and s.owner_id = v_owner
    ) then
      raise exception 'scenes_required';
    end if;

    if exists (
      select 1
      from public.project_scenes s
      where s.project_id = p_project_id
        and s.owner_id = v_owner
        and nullif(trim(s.narration), '') is null
    ) then
      raise exception 'scene_narration_required';
    end if;
  end if;

  update public.video_projects
  set status = p_new_status
  where id = p_project_id
    and owner_id = v_owner
    and status = p_expected_status
  returning * into v_row;

  if v_row.id is null then
    raise exception 'state_changed';
  end if;

  return v_row;
end;
$$;

revoke all on function public.transition_video_project_status(uuid, text, text) from public;
revoke all on function public.transition_video_project_status(uuid, text, text) from anon;
grant execute on function public.transition_video_project_status(uuid, text, text) to authenticated;
