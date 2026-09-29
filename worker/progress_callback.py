import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--title", default="Vídeo em produção")
    parser.add_argument("--status", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--percent", required=True, type=float)
    parser.add_argument("--detail", default="")
    parser.add_argument("--eta-seconds", type=int)
    parser.add_argument("--video-duration-seconds", type=float)
    parser.add_argument("--delivery-manifest")
    args = parser.parse_args()

    url = os.environ.get("ODE_PROGRESS_URL", "").strip()
    if not url:
        print("ODE_PROGRESS_URL ausente; progresso visual ignorado.", flush=True)
        return

    payload = {
        "run_id": args.run_id,
        "title": args.title,
        "status": args.status,
        "stage": args.stage,
        "percent": args.percent,
        "detail": args.detail,
        "run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")),
    }
    if args.delivery_manifest:
        delivery = json.loads(Path(args.delivery_manifest).read_text(encoding="utf-8"))
        files = delivery.get("files") or {}
        if not delivery.get("folder_id") or any(not files.get(key, {}).get("file_id") for key in ("video", "metadata", "publication_text")):
            raise RuntimeError("Manifesto de entrega incompleto. Não é possível confirmar o Drive.")
        payload["drive_folder_id"] = delivery["folder_id"]
        payload["delivery_confirmed"] = True
    if args.eta_seconds is not None:
        payload["eta_seconds"] = args.eta_seconds
    if args.video_duration_seconds is not None:
        payload["video_duration_seconds"] = args.video_duration_seconds

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    secret = os.environ.get("ODE_PROGRESS_SECRET", "").strip()
    headers = {"Content-Type": "application/json"}
    if secret:
        token = hashlib.sha256(
            ("ode-progress-v1:" + secret).encode("utf-8")
        ).hexdigest()
        headers["X-ODE-Progress-Token"] = token

    attempts = 3 if args.status in ("completed", "error") else 1
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, data=data, method="POST", headers=headers)
            with urllib.request.urlopen(req, timeout=8) as response:
                response.read()
            break
        except Exception as exc:
            print(f"ODE_PROGRESS_WARNING|{type(exc).__name__}: {exc}", flush=True)
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)


if __name__ == "__main__":
    main()
