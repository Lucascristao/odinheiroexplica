"""One schedule shared by editor, watchdog, render recovery and publication.

Historical three-slot configurations remain readable for archived runs/tests.
"""
from datetime import datetime, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo

LEGACY_SLOTS = {"manha": "08:00", "meio-dia": "12:00", "noite": "20:00"}


def load_config(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    return json.loads((root / "config/news-autonomy.json").read_text(encoding="utf-8"))


def slots(config):
    rows = config.get("slots")
    if not rows:
        return {name: {"publication": hour, "production": config["production_hours"][i]}
                for i, (name, hour) in enumerate(LEGACY_SLOTS.items())}
    result = {}
    for row in rows:
        name = row["id"]
        if name in result:
            raise ValueError("Duplicate news slot")
        for key in ("production", "publication"):
            datetime.strptime(row[key], "%H:%M")
        if row["production"] >= row["publication"]:
            raise ValueError("Production must precede publication on the same day")
        result[name] = row
    return result


def nominal_occurrence(cron, created_at, config):
    """Resolve a delayed daily cron from its nominal time, never runner start."""
    minute, hour, *rest = cron.split()
    if rest != ["*", "*", "*"]:
        raise ValueError("Expected a fixed daily editorial cron")
    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    if created.tzinfo is None:
        raise ValueError("Run creation must include timezone")
    from datetime import timezone
    created = created.astimezone(timezone.utc)
    occurrence = created.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
    if occurrence > created:
        occurrence -= timedelta(days=1)
    local = occurrence.astimezone(ZoneInfo(config["timezone"]))
    matches = [name for name, row in slots(config).items()
               if cron in row.get("crons_utc", [])]
    if len(matches) != 1:
        raise ValueError("Cron does not identify one configured slot")
    return local.date().isoformat(), matches[0]


def editorial_window(config, day, slot, now):
    zone = ZoneInfo(config["timezone"])
    row = slots(config)[slot]
    start = datetime.fromisoformat(day + "T" + row["production"]).replace(tzinfo=zone)
    target = datetime.fromisoformat(day + "T" + row["publication"]).replace(tzinfo=zone)
    # Do not spend voice/render quota on an edition that cannot finish in time.
    budget = config.get("minimum_production_budget_minutes", 45)
    grace = config.get("late_tolerance_minutes", 0) if config.get("publish_if_late") else 0
    end = target + timedelta(minutes=grace - budget)
    midnight = start.replace(hour=0, minute=0) + timedelta(days=1)
    end = min(end, midnight - timedelta(minutes=budget))
    return (config.get("enabled") is True and now.astimezone(zone).date().isoformat() == day
            and start <= now <= end), start, end


def main():
    import argparse
    import os
    from datetime import timezone
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot")
    parser.add_argument("--date")
    parser.add_argument("--cron")
    parser.add_argument("--created-at")
    args = parser.parse_args()
    config = load_config()
    now = datetime.now(timezone.utc)
    if args.cron:
        day, slot = nominal_occurrence(args.cron, args.created_at, config)
    else:
        day = args.date or now.astimezone(ZoneInfo(config["timezone"])).date().isoformat()
        slot = args.slot
    if slot not in slots(config):
        raise SystemExit("Unknown editorial slot")
    active, start, end = editorial_window(config, day, slot, now)
    payload = {"NEWS_DATE": day, "NEWS_SLOT": slot, "NEWS_SLOT_ACTIVE": str(active).lower()}
    if os.getenv("GITHUB_ENV"):
        with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as stream:
            stream.write("".join(f"{key}={value}\n" for key, value in payload.items()))
    print(json.dumps({**payload, "start": start.isoformat(), "latest_editor_start": end.isoformat()}))


if __name__ == "__main__":
    main()
