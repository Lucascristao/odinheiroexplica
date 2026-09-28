
alter table public.video_projects
  add column if not exists tts_voice text not null default 'pt-BR-MacerioMultilingualNeural';

alter table public.project_scenes
  add column if not exists audio_path text,
  add column if not exists audio_voice text,
  add column if not exists narration_sha256 text,
  add column if not exists audio_generated_at timestamptz;

create index if not exists project_scenes_audio_pending_idx
  on public.project_scenes (project_id, scene_index)
  where audio_duration_seconds is null;

create or replace function public.apply_scene_audio_result(
  p_scene_id uuid,
  p_project_id uuid,
  p_expected_narration_sha256 text,
  p_audio_path text,
  p_audio_duration_seconds numeric,
  p_audio_voice text
)
returns public.project_scenes
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_owner uuid := auth.uid();
  v_row public.project_scenes;
  v_current_hash text;
begin
  if v_owner is null then
    raise exception 'authentication_required';
  end if;

  select encode(digest(narration, 'sha256'), 'hex')
  into v_current_hash
  from public.project_scenes
  where id = p_scene_id
    and project_id = p_project_id
    and owner_id = v_owner;

  if v_current_hash is null then
    raise exception 'scene_not_found';
  end if;

  if v_current_hash <> p_expected_narration_sha256 then
    raise exception 'narration_changed';
  end if;

  update public.project_scenes
  set
    audio_path = p_audio_path,
    audio_duration_seconds = p_audio_duration_seconds,
    audio_voice = p_audio_voice,
    narration_sha256 = p_expected_narration_sha256,
    audio_generated_at = now()
  where id = p_scene_id
    and project_id = p_project_id
    and owner_id = v_owner
  returning * into v_row;

  return v_row;
end;
$$;

revoke all on function public.apply_scene_audio_result(uuid, uuid, text, text, numeric, text) from public;
revoke all on function public.apply_scene_audio_result(uuid, uuid, text, text, numeric, text) from anon;
grant execute on function public.apply_scene_audio_result(uuid, uuid, text, text, numeric, text) to authenticated;

create or replace function public.recalculate_project_duration(p_project_id uuid)
returns numeric
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_owner uuid := auth.uid();
  v_duration numeric;
begin
  if v_owner is null then
    raise exception 'authentication_required';
  end if;

  select coalesce(sum(audio_duration_seconds), 0)
  into v_duration
  from public.project_scenes
  where project_id = p_project_id
    and owner_id = v_owner;

  update public.video_projects
  set duration_seconds = v_duration
  where id = p_project_id
    and owner_id = v_owner;

  return v_duration;
end;
$$;

revoke all on function public.recalculate_project_duration(uuid) from public;
revoke all on function public.recalculate_project_duration(uuid) from anon;
grant execute on function public.recalculate_project_duration(uuid) to authenticated;
