"""Schedule a thoroughly gated private news upload for YouTube publication.

No human-per-episode approval is requested: the user's standing authorization is
stored in config/news-autonomy.json. Fail closed on incomplete provenance.
"""
import argparse
from datetime import datetime, timezone
import json
import re
import time
from pathlib import Path
from zoneinfo import ZoneInfo

from thumbnail_contract import validate_thumbnail_audit, file_sha256
from youtube_publication import assert_channel, youtube_service, EXPECTED_ID


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def confirmed_video_identity(service, video_id: str, project_id: str,
                             attempts: int = 5) -> dict:
    """Read-after-write check; YouTube may lag after a private upload.

    Never fall back to matching title, description or an unauthenticated URL.
    An unproven editorial identity must remain private.
    """
    expected_tag = "ODE_EPISODE_" + project_id
    for attempt in range(attempts):
        items = service.videos().list(
            part="snippet,status", id=video_id
        ).execute().get("items", [])
        if len(items) == 1:
            video = items[0]
            if video.get("snippet", {}).get("channelId") != EXPECTED_ID:
                raise SystemExit("Vídeo não pertence ao canal esperado.")
            if expected_tag in video.get("snippet", {}).get("tags", []):
                return video
        elif len(items) > 1:
            raise SystemExit("YouTube retornou identidade ambígua.")
        if attempt + 1 < attempts:
            time.sleep(min(2 ** attempt, 5))
    raise SystemExit("Vídeo sem identificação editorial confirmada após novas consultas; preservar privado.")


def confirm_release_status(service, video_id, project_id, privacy, publish_at=None,
                           attempts=5):
    """Retry only readback: a successful write can take seconds to become visible."""
    for attempt in range(attempts):
        video = confirmed_video_identity(service, video_id, project_id)
        status = video.get("status", {})
        if status.get("uploadStatus") in ("failed", "rejected", "deleted"):
            raise SystemExit("YouTube rejeitou o vídeo: " + str(status.get("rejectionReason") or status.get("failureReason") or status["uploadStatus"]))
        observed_target = status.get("publishAt")
        target_matches = publish_at is None or (
            observed_target is not None
            and datetime.fromisoformat(observed_target.replace("Z", "+00:00")) == publish_at
        )
        if status.get("privacyStatus") == privacy and target_matches:
            return video
        if attempt + 1 < attempts:
            time.sleep(min(2 ** attempt, 5))
    raise SystemExit("YouTube não confirmou " + ("o horário programado" if publish_at else "a publicação pública") + " após novas consultas; verificar o mesmo vídeo, sem repetir upload.")


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
    allowed_qa_states = ("pass", "warn") if config.get("allow_qa_warnings") is True else (config["require_qa_status"],)
    if qa.get("status") not in allowed_qa_states or qa.get("failures"):
        raise SystemExit("QA técnico possui falhas ou status inválido.")
    if qa.get("warnings"):
        print("QA_WARNINGS_NON_BLOCKING:", json.dumps(qa["warnings"], ensure_ascii=False))
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
    # Atraso operacional de até 90 min, conforme autorização permanente.
    # Não antecipa publicação: se o horário ainda está no futuro, agenda normalmente.
    grace_minutes = config.get("late_tolerance_minutes", 0)
    if type(grace_minutes) is not int or not 0 <= grace_minutes <= 180:
        raise SystemExit("Tolerância de publicação inválida.")
    delay_minutes = -lead
    eligible_late_grace = (
        config.get("publish_if_late") is True
        and grace_minutes > 0
        and 0 <= delay_minutes <= grace_minutes
        and now.astimezone(local_zone).date() == local_target.date()
    )
    # Exceções históricas explícitas continuam isoladas por episódio/data.
    recoveries = [config.get("one_time_late_recovery") or {}]
    recoveries.extend(config.get("additional_late_recoveries") or [])
    eligible_recovery = (
        delay_minutes >= 0
        and now.astimezone(local_zone).date() == local_target.date()
        and any(
            item.get("episode_id") == project_id
            and item.get("original_publication_local") == raw_target
            and item.get("authorized_by_user") is True
            and item.get("mode") == "publish_immediately_after_qa"
            for item in recoveries
        )
    )
    publish_now = eligible_late_grace or eligible_recovery
    if 0 < lead < config["min_lead_minutes"]:
        print("SHORT_LEAD_ADVISORY: programar no horário original sem atrasar nem cancelar.")
    service = youtube_service()
    assert_channel(service)
    video = confirmed_video_identity(service, video_id, project_id)
    status = video["status"]
    if status.get("privacyStatus") == "public":
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({
            "project_id": project_id, "video_id": video_id,
            "status": "already_public", "publication_confirmation": "confirmed_public",
            "confirmed_at_utc": datetime.now(timezone.utc).isoformat(),
            "url": "https://youtu.be/" + video_id,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("YOUTUBE_NEWS_ALREADY_PUBLIC:", "https://youtu.be/" + video_id)
        return
    if status.get("privacyStatus") != "private":
        raise SystemExit("Vídeo não está privado; não alterar.")
    if lead < 0 and not publish_now:
        raise SystemExit("Janela de tolerância vencida; preservar vídeo privado.")
    existing = status.get("publishAt")
    desired = target.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    if publish_now:
        if existing:
            raise SystemExit("Publicação imediata bloqueada: vídeo já foi agendado, não sobrescrever.")
        service.videos().update(
            part="status",
            body={"id": video_id, "status": {"privacyStatus": "public"}},
        ).execute()
        confirm_release_status(service, video_id, project_id, "public")
        payload = {
            "project_id": project_id, "video_id": video_id, "status": "published_within_tolerance" if eligible_late_grace else "published_late_authorized",
            "publication_confirmation": "confirmed_public",
            "delay_minutes": round(max(0, delay_minutes), 2),
            "late_tolerance_minutes": grace_minutes,
            "qa_warning_count": len(qa.get("warnings") or []),
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
    confirm_release_status(service, video_id, project_id, "private", target.astimezone(timezone.utc))
    payload = {
        "project_id": project_id, "video_id": video_id,
        "scheduled_for_utc": desired, "scheduled_for_local": local_target.isoformat(),
        "thumbnail_sha256": image_hash,
        "thumbnail_status": "attached" if image_hash else "youtube_automatic",
        "qa_status": qa["status"],
        "qa_warning_count": len(qa.get("warnings") or []),
        "late_tolerance_minutes": grace_minutes,
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
