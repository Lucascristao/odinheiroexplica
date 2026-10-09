"""Schedule a thoroughly gated private news upload for YouTube publication.

No human-per-episode approval is requested: the user's standing authorization is
stored in config/news-autonomy.json. Fail closed on incomplete provenance.
"""
import argparse
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

from thumbnail_contract import validate_thumbnail_audit, file_sha256
from youtube_publication import assert_channel, youtube_service, EXPECTED_ID


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    p = argparse.ArgumentParser()
    for name in ("project", "episode", "private-receipt", "qa", "config", "output"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--thumbnail", help="Capa opcional criada e auditada pelo ChatGPT")
    p.add_argument("--thumbnail-receipt", help="Recibo da capa opcional, se anexada")
    p.add_argument("--root", default=".")
    args = p.parse_args()
    config = load(args.config)
    if config.get("enabled") is not True or config.get("version") != "1.0":
        raise SystemExit("Publicação autônoma desabilitada.")
    project, episode, qa = load(args.project), load(args.episode), load(args.qa)
    project_id = project.get("project_id")
    if not re.fullmatch(r"noticia-\d{4}-\d{2}-\d{2}-[a-z0-9-]+", str(project_id)):
        raise SystemExit("Somente notícias únicas podem ser agendadas.")
    if episode.get("episode_id") != project_id or episode.get("editorial_status") != config["required_editorial_status"]:
        raise SystemExit("Notícia sem apuração autônoma identificada.")
    if qa.get("status") != config["require_qa_status"] or qa.get("failures") or qa.get("warnings"):
        raise SystemExit("QA técnico não está integralmente aprovado.")
    receipt = load(args.private_receipt)
    if bool(args.thumbnail) != bool(args.thumbnail_receipt):
        raise SystemExit("Capa e recibo precisam ser informados juntos; ambos opcionais.")
    image_hash = None
    delivered = None
    if args.thumbnail:
        image = Path(args.thumbnail)
        validate_thumbnail_audit(
            Path(args.root).resolve(), project, image, project_source_path=args.project
        )
        image_hash = file_sha256(image)
        delivered = load(args.thumbnail_receipt)
    video_id = receipt.get("video_id")
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", str(video_id)):
        raise SystemExit("ID de vídeo inválido.")
    if (receipt.get("project_id") != project_id
        or receipt.get("destination") != "youtube"
        or receipt.get("privacy_requested") != "private"):
        raise SystemExit("Recibo do vídeo privado não corresponde ao episódio.")
    if delivered is not None and (
        delivered.get("project_id") != project_id
        or delivered.get("video_id") != video_id
        or delivered.get("thumbnail_sha256") != image_hash
    ):
        raise SystemExit("Recibo da capa não coincide com o vídeo.")
    raw_target = episode.get("publication_target_local")
    if not isinstance(raw_target, str):
        raise SystemExit("Episódio sem horário de publicação explícito.")
    target = datetime.fromisoformat(raw_target)
    local_zone = ZoneInfo(config["timezone"])
    if target.tzinfo is None or target.utcoffset() is None:
        raise SystemExit("Horário de publicação precisa trazer timezone explícito.")
    local_target = target.astimezone(local_zone)
    allowed = config["publication_hours"]
    if (local_target.strftime("%H:%M") not in allowed
        or local_target.date().isoformat() != episode.get("news_date")
        or local_target.second or local_target.microsecond):
        raise SystemExit("Publicação fora da data/horários autorizados.")
    now = datetime.now(timezone.utc)
    lead = (target.astimezone(timezone.utc) - now).total_seconds() / 60
    recovery = config.get("one_time_late_recovery") or {}
    eligible_recovery = (
        project_id == "noticia-2026-10-09-manha"
        and recovery.get("episode_id") == project_id
        and recovery.get("original_publication_local") == "2026-10-09T08:00:00-03:00"
        and raw_target == recovery.get("original_publication_local")
        and recovery.get("authorized_by_user") is True
        and recovery.get("mode") == "publish_immediately_after_qa"
        and now.astimezone(local_zone).date().isoformat() == "2026-10-09"
        and lead < config["min_lead_minutes"]
    )
    if lead < config["min_lead_minutes"] and not eligible_recovery:
        raise SystemExit("Janela de publicação perdida: preservar vídeo privado.")
    service = youtube_service()
    assert_channel(service)
    items = service.videos().list(part="snippet,status", id=video_id).execute().get("items", [])
    if len(items) != 1 or items[0]["snippet"].get("channelId") != EXPECTED_ID:
        raise SystemExit("Vídeo não pertence ao canal esperado.")
    tags = items[0]["snippet"].get("tags", [])
    if "ODE_EPISODE_" + project_id not in tags:
        raise SystemExit("Vídeo sem identificação editorial correta.")
    status = items[0]["status"]
    if status.get("privacyStatus") != "private":
        raise SystemExit("Vídeo não está privado; não alterar.")
    existing = status.get("publishAt")
    desired = target.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    if eligible_recovery:
        if existing:
            raise SystemExit("Recuperação bloqueada: vídeo já foi agendado, não sobrescrever.")
        service.videos().update(
            part="status",
            body={"id": video_id, "status": {"privacyStatus": "public"}},
        ).execute()
        fresh = service.videos().list(part="status,snippet", id=video_id).execute().get("items", [])
        if len(fresh) != 1 or fresh[0]["snippet"].get("channelId") != EXPECTED_ID:
            raise SystemExit("YouTube não confirmou o canal após recuperação.")
        if fresh[0]["status"].get("privacyStatus") != "public":
            raise SystemExit("YouTube não confirmou publicação pública da recuperação.")
        payload = {
            "project_id": project_id, "video_id": video_id, "status": "published_late_authorized",
            "publication_confirmation": "confirmed_public",
            "published_after_target_local": local_target.isoformat(),
            "confirmed_at_utc": datetime.now(timezone.utc).isoformat(),
            "thumbnail_sha256": image_hash,
            "thumbnail_status": "attached" if image_hash else "youtube_automatic",
            "qa_status": qa["status"], "url": "https://youtu.be/" + video_id,
        }
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("YOUTUBE_NEWS_LATE_RECOVERY_PUBLISHED:", payload["url"])
        return
    if existing:
        previous = datetime.fromisoformat(existing.replace("Z", "+00:00"))
        if previous != target.astimezone(timezone.utc):
            raise SystemExit("Vídeo já tem outro horário; não sobrescrever.")
    else:
        service.videos().update(
            part="status",
            body={"id": video_id, "status": {"privacyStatus": "private", "publishAt": desired}},
        ).execute()
    fresh = service.videos().list(part="status,snippet", id=video_id).execute().get("items", [])
    if len(fresh) != 1 or fresh[0]["snippet"].get("channelId") != EXPECTED_ID:
        raise SystemExit("YouTube não confirmou canal/agendamento.")
    confirmed = fresh[0]["status"].get("publishAt")
    if not confirmed or datetime.fromisoformat(confirmed.replace("Z", "+00:00")) != target.astimezone(timezone.utc):
        raise SystemExit("YouTube não confirmou o horário programado.")
    if fresh[0]["status"].get("privacyStatus") != "private":
        raise SystemExit("Vídeo não ficou privado até a data programada.")
    payload = {
        "project_id": project_id, "video_id": video_id,
        "scheduled_for_utc": desired, "scheduled_for_local": local_target.isoformat(),
        "thumbnail_sha256": image_hash,
        "thumbnail_status": "attached" if image_hash else "youtube_automatic",
        "qa_status": qa["status"],
        "status": "scheduled_private_until_publish_at",
        "confirmed_at_utc": now.isoformat(), "url": "https://youtu.be/" + video_id,
        "publication_confirmation": "pending_until_due",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("YOUTUBE_NEWS_SCHEDULED:", payload["url"], desired)


if __name__ == "__main__":
    main()
