"""Unverified same-day checkpoints; cache never grants factual approval."""
import json
from pathlib import Path


def read_state(path, day, slot):
    path = Path(path)
    if not path.is_file():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    if (state.get("news_date") != day or state.get("slot") != slot
            or state.get("factual_approval") is not False or state.get("discarded") is True):
        return None
    return state


def save_state(path, day, slot, report, episode=None, completed=()):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"version": "1.0", "news_date": day, "slot": slot,
        "factual_approval": False, "report": report, "draft": episode,
        "developed_segment_ids": sorted(completed)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def discard_state(path):
    path = Path(path)
    if path.exists():
        path.write_text('{"discarded":true,"factual_approval":false}\n', encoding="utf-8")
