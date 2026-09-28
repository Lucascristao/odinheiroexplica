import argparse
import hashlib
import json
import os
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
    }
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

    try:
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            response.read()
    except Exception as exc:
        print(f"ODE_PROGRESS_WARNING|{type(exc).__name__}: {exc}", flush=True)


if __name__ == "__main__":
    main()
