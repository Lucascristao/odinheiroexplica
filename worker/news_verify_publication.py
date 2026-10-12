"""Read-only confirmation of scheduled public YouTube news release."""
import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
from zoneinfo import ZoneInfo
from youtube_publication import youtube_service, assert_channel, lookup_existing

SLOT_HOURS = {"manha": "08:00", "meio-dia": "12:00", "noite": "20:00"}
CHECK_HOURS_UTC = {"manha": (12, 45), "meio-dia": (16, 45), "noite": (0, 45)}
LOCAL_ZONE = ZoneInfo("America/Fortaleza")


def edition_date(slot, explicit_date=None, run_created_at=None, now=None):
    if explicit_date:
        parsed = date.fromisoformat(explicit_date).isoformat()
        if parsed != explicit_date:
            raise ValueError("Data exige formato YYYY-MM-DD.")
        return parsed
    if run_created_at:
        # Most recent nominal cron occurrence; a dispatch delayed >24h needs --news-date.
        created = datetime.fromisoformat(run_created_at.replace("Z", "+00:00"))
        if created.tzinfo is None:
            raise ValueError("Data de criação da run exige fuso.")
        created = created.astimezone(timezone.utc)
        hour, minute = CHECK_HOURS_UTC[slot]
        nominal = created.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if nominal > created:
            nominal -= timedelta(days=1)
        return nominal.astimezone(LOCAL_ZONE).date().isoformat()
    return (now or datetime.now(timezone.utc)).astimezone(LOCAL_ZONE).date().isoformat()


def check_publication(slot, day, episodes_dir=Path("news/episodes")):
    project_id = f"noticia-{day}-{slot}"
    episode_path = Path(episodes_dir) / f"{day}-{slot}.json"
    outcome = {
        "episode_id": project_id, "episode_path": str(episode_path),
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_local_time": SLOT_HOURS[slot], "news_date": day,
        "episode_exists": episode_path.is_file(), "public_confirmed": False,
        "video_id": None, "privacy_observed": None,
    }
    if not outcome["episode_exists"]:
        return {**outcome, "stage": "episode_missing", "message":
                "JSON da edição ausente nesta revisão; conferir tarefa editorial, escrita e runs antes de retomar."}
    try:
        episode = json.loads(episode_path.read_text(encoding="utf-8"))
        if not isinstance(episode, dict) or episode.get("episode_id") != project_id:
            raise ValueError("Identidade da edição divergente.")
    except (ValueError, OSError):
        return {**outcome, "stage": "episode_invalid", "message": "JSON da edição inválido ou identidade divergente."}
    try:
        service = youtube_service()
        channel = assert_channel(service)
        marker = "ODE_EPISODE_" + project_id
        video = lookup_existing(service, channel, marker)
        if not video:
            return {**outcome, "stage": "upload_missing", "message":
                    "Edição existe, mas vídeo não foi encontrado; conferir render, QA e recibo de upload."}
        video_id = video["id"]
        outcome.update(video_id=video_id, url="https://youtu.be/" + video_id)
        state = service.videos().list(part="status,snippet", id=video_id).execute().get("items", [])
        if len(state) != 1:
            return {**outcome, "stage": "status_unavailable", "message": "Não foi possível ler status do YouTube."}
        snippet = state[0].get("snippet", {})
        if (state[0].get("id") != video_id or snippet.get("channelId") != channel["id"]
                or marker not in snippet.get("tags", [])):
            return {**outcome, "stage": "identity_mismatch", "message": "Identidade do vídeo/episódio/canal divergente."}
        privacy = state[0].get("status", {}).get("privacyStatus")
        outcome.update(privacy_observed=privacy, public_confirmed=privacy == "public")
        return {**outcome, "stage": "public_confirmed" if privacy == "public" else "not_public",
                "message": "Publicação pública confirmada." if privacy == "public" else
                "Vídeo encontrado, mas não está público; conferir agendamento e eventuais restrições de API."}
    except Exception as error:
        # Do not copy arbitrary API/credential exception strings into public artifacts.
        return {**outcome, "stage": "api_error", "error_type": type(error).__name__,
                "message": "Consulta autenticada falhou; conferir a configuração e o serviço sem repetir upload."}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slot", choices=SLOT_HOURS, required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--news-date", help="Data explícita YYYY-MM-DD para rechecagem manual.")
    p.add_argument("--run-created-at", help="Criação UTC da run agendada, para fixar a janela antes de filas/atrasos.")
    p.add_argument("--episodes-dir", default="news/episodes")
    args = p.parse_args()
    try:
        day = edition_date(args.slot, args.news_date, args.run_created_at)
        outcome = check_publication(args.slot, day, Path(args.episodes_dir))
    except ValueError:
        outcome = {"stage": "window_unresolved", "public_confirmed": False,
                   "message": "Data da edição/janela inválida; especificar --news-date."}
    outcome["run_created_at"] = args.run_created_at
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("YOUTUBE_PUBLICATION_CHECK:", outcome["stage"], outcome.get("episode_id"), outcome.get("url"))
    if not outcome["public_confirmed"]:
        raise SystemExit(outcome["message"])


if __name__ == "__main__":
    main()
