"""Reject a stale or underdeveloped new edition before spending voice quota."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from news_schedule import load_config, editorial_window
from news_quality_contract import editorial_fingerprint
from news_minimum_duration import require_developed_script


def validate_production(episode, config, now):
    if episode.get("editorial_status") != "autonomous_fact_checked":
        return
    if episode["news_date"] < config.get("schedule_effective_from", "9999"):
        return  # Preserve archived pilot/render contracts and caches.
    prefix = "noticia-" + episode["news_date"] + "-"
    slot = episode["episode_id"].removeprefix(prefix)
    active, _, _ = editorial_window(config, episode["news_date"], slot, now)
    if not active:
        raise ValueError("News production window expired before synthesis; do not create another stranded private video")
    quality = episode.get("editorial_quality") or {}
    review = quality.get("review") or {}
    count = sum(len(s["narration"].split()) for s in episode["segments"])
    if (quality.get("version") != config["editorial_quality"]["version"]
            or quality.get("reviewed_content_sha256") != editorial_fingerprint(episode)
            or quality.get("narration_word_count") != count
            or review.get("approved") is not True or review.get("issues") != []):
        raise ValueError("New news edition lacks developed narration and the second source review")
    require_developed_script(episode, config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", required=True)
    args = parser.parse_args()
    validate_production(json.loads(Path(args.episode).read_text(encoding="utf-8")), load_config(), datetime.now(timezone.utc))
    print("NEWS_PRODUCTION_WINDOW_AND_QUALITY_PASS")
