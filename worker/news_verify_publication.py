"""Read-only confirmation of scheduled public YouTube news release."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from zoneinfo import ZoneInfo
from youtube_publication import youtube_service, assert_channel, lookup_existing

SLOT_HOURS = {"manha": "08:00", "meio-dia": "12:00", "noite": "20:00"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slot", choices=SLOT_HOURS, required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    day = datetime.now(ZoneInfo("America/Fortaleza")).date().isoformat()
    project_id = f"noticia-{day}-{args.slot}"
    service = youtube_service()
    channel = assert_channel(service)
    video = lookup_existing(service, channel, "ODE_EPISODE_" + project_id)
    if not video:
        raise SystemExit("Vídeo da janela não encontrado no canal; publicação não confirmada.")
    video_id = video["id"]
    state = service.videos().list(part="status,snippet", id=video_id).execute().get("items", [])
    if len(state) != 1:
        raise SystemExit("Não foi possível ler status do YouTube.")
    privacy = state[0].get("status", {}).get("privacyStatus")
    outcome = {
        "episode_id": project_id, "video_id": video_id,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_local_time": SLOT_HOURS[args.slot],
        "privacy_observed": privacy, "public_confirmed": privacy == "public",
        "url": "https://youtu.be/" + video_id,
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("YOUTUBE_PUBLICATION_CHECK:", outcome["url"], privacy)
    if privacy != "public":
        raise SystemExit("Agendamento não resultou em vídeo público; investigar restrição de API.")


if __name__ == "__main__":
    main()
