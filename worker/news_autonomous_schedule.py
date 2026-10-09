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
    for name in ("project", "episode", "thumbnail", "private-receipt",
                 "thumbnail-receipt", "qa", "config", "output"):
        p.add_argument("--" + name, required=True)
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
    image = Path(args.thumbnail)
    validate_thumbnail_audit(
        Path(args.root).resolve(), project, image, project_source_path=args.project
    )
    receipt, delivered = load(args.private_receipt), load(args.thumbnail_receipt)
    video_id = receipt.get("video_id")
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", str(video_id)):
        raise SystemExit("ID de vídeo inválido.")
    image_hash = file_sha256(image)
    if (receipt.get("project_id") != project_id
        or receipt.get("destination") != "youtube"
        or receipt.get("privacy_requested") != "private"
        or delivered.get("project_id") != project_id
        or delivered.get("video_id") != video_id
        or delivered.get("thumbnail_sha256") != image_hash):
        raise SystemExit("Recibos do vídeo e capa não coincidem.")
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
    if lead < config["min_lead_minutes"]:
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
        "thumbnail_sha256": image_hash, "qa_status": qa["status"],
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
