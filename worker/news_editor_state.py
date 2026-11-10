"""Unverified same-day checkpoints; cache never grants factual approval."""
import json
from pathlib import Path

STATE_VERSION = '2.0-full-narration-review'


def read_state(path, day, slot, excluded_source_urls=()):
    path = Path(path)
    if not path.is_file():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    if (state.get("news_date") != day or state.get("slot") != slot
            or state.get('version') != STATE_VERSION
            or state.get("factual_approval") is not False or state.get("discarded") is True):
        return None
    if any(url in str(state.get('report', '')) for url in excluded_source_urls if url):
        return None  # A cached report cannot revive a materially rejected source.
    return state


def save_state(path, day, slot, report, episode=None, completed=()):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"version": STATE_VERSION, "news_date": day, "slot": slot,
        "factual_approval": False, "report": report, "draft": episode,
        "developed_segment_ids": sorted(completed)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def discard_state(path):
    path = Path(path)
    if path.exists():
        path.write_text('{"discarded":true,"factual_approval":false}\n', encoding="utf-8")
