"""Resolve a one-run fresh-audio request without reading persistent markers."""

import argparse
import json
import os
from pathlib import Path
import re

from tts_config import VOICE_POLICY_CACHE_KEY, VOICE_POLICY_VERSION


def force_fresh_audio(event_name: str, run_attempt: str, requested: str) -> bool:
    # A re-run is a resume even when its original manual input was true.
    # Push events never consume the old force_fresh_audio marker in daily.txt.
    return (
        event_name == "workflow_dispatch"
        and run_attempt == "1"
        and requested.strip().lower() == "true"
    )


def single_line(value: object, replacement: str) -> str:
    return str(value).replace("\r", replacement).replace("\n", replacement).replace("\0", replacement)


def environment_values(project: dict, environment: dict) -> dict[str, str]:
    titles = project.get("packaging", {}).get("titles") or []
    title = (titles[0].get("text") if titles else None) or project.get("title") or "O Dinheiro Explica"
    slug = project.get("project_id") or "video-diario"
    if not re.fullmatch(r"[A-Za-z0-9._-]+", VOICE_POLICY_VERSION):
        raise RuntimeError("Versão da política de voz inválida para o cache.")
    if not re.fullmatch(r"[0-9a-f]{16}", VOICE_POLICY_CACHE_KEY):
        raise RuntimeError("Fingerprint da política de voz inválido para o cache.")
    fresh = force_fresh_audio(
        environment.get("GITHUB_EVENT_NAME", ""),
        environment.get("GITHUB_RUN_ATTEMPT", ""),
        environment.get("ODE_REQUESTED_FRESH_AUDIO", "false"),
    )
    return {
        "ODE_VIDEO_TITLE": single_line(title, " "),
        "ODE_PROJECT_SLUG": single_line(slug, "-"),
        "ODE_FORCE_FRESH_AUDIO": "true" if fresh else "false",
        "ODE_VOICE_POLICY_VERSION": VOICE_POLICY_VERSION,
        "ODE_VOICE_POLICY_CACHE_KEY": VOICE_POLICY_CACHE_KEY,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    project = json.loads(Path(args.project).read_text(encoding="utf-8-sig"))
    for name, value in environment_values(project, dict(os.environ)).items():
        print(f"{name}={value}")


if __name__ == "__main__":
    main()
