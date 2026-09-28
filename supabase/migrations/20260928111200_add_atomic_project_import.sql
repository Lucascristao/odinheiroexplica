create or replace function public.import_video_project(payload jsonb)
returns uuid
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_owner uuid := auth.uid();
  v_project_id uuid;
  v_source jsonb;
  v_claim jsonb;
  v_scene jsonb;
begin
  if v_owner is null then raise exception 'authentication_required'; end if;
  if payload is null or jsonb_typeof(payload) <> 'object' then raise exception 'invalid_payload'; end if;
  if coalesce(payload->>'version', '') <> '1.0' then raise exception 'unsupported_schema_version'; end if;
  if nullif(trim(payload #>> '{story,subject}'), '') is null then raise exception 'story_subject_required'; end if;

  insert into public.video_projects (
    owner_id, schema_version, status, subject, angle, promise, category,
    viral_score, risk_flags, raw_payload
  )
  values (
    v_owner,
    payload->>'version',
    'IMPORTED',
    payload #>> '{story,subject}',
    nullif(payload #>> '{story,angle}', ''),
    nullif(payload #>> '{story,promise}', ''),
    nullif(payload #>> '{story,category}', ''),
    case when jsonb_typeof(payload #> '{editorial,viral_score}') = 'number'
      then (payload #>> '{editorial,viral_score}')::smallint else null end,
    coalesce(array(
      select jsonb_array_elements_text(
        case when jsonb_typeof(payload #> '{editorial,risk_flags}') = 'array'
          then payload #> '{editorial,risk_flags}' else '[]'::jsonb end
      )
    ), '{}'::text[]),
    payload
  )
  returning id into v_project_id;

  for v_source in
    select value from jsonb_array_elements(
      case when jsonb_typeof(payload->'sources') = 'array' then payload->'sources' else '[]'::jsonb end
    )
  loop
    insert into public.project_sources (
      project_id, owner_id, source_key, title, url, publisher,
      source_type, published_at, license, notes, metadata
    )
    values (
      v_project_id, v_owner, nullif(v_source->>'id', ''), nullif(v_source->>'title', ''),
      v_source->>'url', nullif(v_source->>'publisher', ''), nullif(v_source->>'source_type', ''),
      case when nullif(v_source->>'published_at', '') is not null
        then (v_source->>'published_at')::timestamptz else null end,
      nullif(v_source->>'license', ''), nullif(v_source->>'notes', ''),
      coalesce(v_source->'metadata', '{}'::jsonb)
    );
  end loop;

  for v_claim in
    select value from jsonb_array_elements(
      case when jsonb_typeof(payload->'claims') = 'array' then payload->'claims' else '[]'::jsonb end
    )
  loop
    insert into public.project_claims (
      project_id, owner_id, claim_key, claim_text, confidence,
      verification_status, source_keys, metadata
    )
    values (
      v_project_id, v_owner, nullif(v_claim->>'id', ''), v_claim->>'text',
      coalesce(nullif(v_claim->>'confidence', ''), 'medium'),
      coalesce(nullif(v_claim->>'verification_status', ''), 'unverified'),
      coalesce(array(
        select jsonb_array_elements_text(
          case when jsonb_typeof(v_claim->'source_ids') = 'array'
            then v_claim->'source_ids' else '[]'::jsonb end
        )
      ), '{}'::text[]),
      coalesce(v_claim->'metadata', '{}'::jsonb)
    );
  end loop;

  for v_scene in
    select value from jsonb_array_elements(
      case when jsonb_typeof(payload #> '{script,scenes}') = 'array'
        then payload #> '{script,scenes}' else '[]'::jsonb end
    )
  loop
    insert into public.project_scenes (
      project_id, owner_id, scene_index, title, narration,
      visual_type, visual_payload, claim_keys
    )
    values (
      v_project_id, v_owner, (v_scene->>'index')::integer,
      nullif(v_scene->>'title', ''), coalesce(v_scene->>'narration', ''),
      nullif(v_scene #>> '{visual,type}', ''),
      coalesce(v_scene #> '{visual,payload}', '{}'::jsonb),
      coalesce(array(
        select jsonb_array_elements_text(
          case when jsonb_typeof(v_scene->'claim_ids') = 'array'
            then v_scene->'claim_ids' else '[]'::jsonb end
        )
      ), '{}'::text[])
    );
  end loop;

  return v_project_id;
end;
$$;

revoke all on function public.import_video_project(jsonb) from public;
revoke all on function public.import_video_project(jsonb) from anon;
grant execute on function public.import_video_project(jsonb) to authenticated;

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
  v_row public.video_projects;
begin
  if auth.uid() is null then raise exception 'authentication_required'; end if;

  update public.video_projects
  set status = p_new_status
  where id = p_project_id
    and owner_id = auth.uid()
    and status = p_expected_status
  returning * into v_row;

  if v_row.id is null then raise exception 'state_changed_or_project_not_found'; end if;

  return v_row;
end;
$$;

revoke all on function public.transition_video_project_status(uuid, text, text) from public;
revoke all on function public.transition_video_project_status(uuid, text, text) from anon;
grant execute on function public.transition_video_project_status(uuid, text, text) to authenticated;
