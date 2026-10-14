"""Idempotent hand-off from a committed news episode to the real render workflow."""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

WORKFLOW = "render-news-single.yml"
TITLE_PREFIX = "ODE render | "
UPLOAD_STEP = "Entregar vídeo privado sem Google Drive"
SLOTS = {"manha": "08:00", "meio-dia": "12:00", "noite": "20:00"}


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Horário sem fuso.")
    return parsed


def eligible(episode_path, episode, config, now):
    match = re.fullmatch(r"news/episodes/(\d{4}-\d{2}-\d{2})-(manha|meio-dia|noite)\.json", episode_path)
    if not match:
        raise ValueError("A retomada automática exige caminho canônico de data e janela.")
    day, slot = match.groups()
    zone = ZoneInfo(config["timezone"])
    target = timestamp(episode["publication_target_local"]).astimezone(zone)
    if (episode.get("episode_id") != f"noticia-{day}-{slot}"
            or episode.get("news_date") != day
            or episode.get("editorial_status") != "autonomous_fact_checked"
            or target.date().isoformat() != day
            or target.strftime("%H:%M") != SLOTS[slot]
            or target.second or target.microsecond
            or SLOTS[slot] not in config["publication_hours"]):
        raise ValueError("Identidade, apuração ou horário da edição inválidos.")
    grace = config.get("late_tolerance_minutes", 0)
    if type(grace) is not int or not 0 <= grace <= 180:
        raise ValueError("Tolerância inválida.")
    start_hour = config["production_hours"][list(SLOTS).index(slot)]
    start = datetime.fromisoformat(f"{day}T{start_hour}:00").replace(tzinfo=zone)
    if config.get("enabled") is not True:
        return "disabled"
    deadline = target + timedelta(minutes=grace if config.get("publish_if_late") is True else 0)
    if now.astimezone(zone).date().isoformat() != day or not start <= now <= deadline:
        return "outside_window"
    return None


def choose_action(runs, jobs_by_id, now, max_attempts=3):
    """Runs supplied here are positively correlated with this episode only."""
    if any(run.get("status") != "completed" for run in runs):
        return {"action": "none", "reason": "render_active"}
    if any(run.get("conclusion") == "success" for run in runs):
        return {"action": "none", "reason": "render_succeeded"}
    if not runs:
        return {"action": "dispatch", "reason": "committed_episode_without_render"}
    # An upload that started may have a side effect even if its step failed.
    # Only the existing receipt/publication recovery may handle that state.
    for run in runs:
        jobs = jobs_by_id.get(run["id"], [])
        steps = [step for job in jobs for step in job.get("steps", []) if step.get("name") == UPLOAD_STEP]
        if len(steps) != 1 or steps[0].get("conclusion") != "skipped":
            return {"action": "none", "reason": "upload_started_or_state_unknown", "run_id": run["id"]}
    latest = max(runs, key=lambda run: timestamp(run["created_at"]))
    if latest.get("conclusion") not in ("failure", "cancelled", "timed_out"):
        return {"action": "none", "reason": "render_conclusion_not_retryable", "run_id": latest["id"]}
    # Count attempts across all runs, rather than resetting the budget with a new ID.
    if sum(int(run.get("run_attempt", 1)) for run in runs) >= max_attempts:
        return {"action": "none", "reason": "retry_limit", "run_id": latest["id"]}
    if now - timestamp(latest["updated_at"]) < timedelta(minutes=10):
        return {"action": "none", "reason": "retry_cooldown", "run_id": latest["id"]}
    return {"action": "rerun", "reason": "failure_before_upload", "run_id": latest["id"]}


class GitHub:
    def __init__(self, repo, token):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("Repositório inválido.")
        self.base = "https://api.github.com/repos/" + repo
        self.token = token

    def request(self, path, payload=None):
        request = urllib.request.Request(self.base + path,
            data=None if payload is None else json.dumps(payload).encode(),
            method="GET" if payload is None else "POST",
            headers={"Authorization": "Bearer " + self.token, "Accept": "application/vnd.github+json",
                     "Content-Type": "application/json", "X-GitHub-Api-Version": "2022-11-28"})
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read()
        return json.loads(body) if body else None

    def episode(self, path, ref="main"):
        result = self.request("/contents/" + path + "?ref=" + urllib.parse.quote(ref, safe=""))
        return base64.b64decode(result["content"]).replace(b"\r\n", b"\n")


def ensure_render(api, episode_path, episode_bytes, config, now, apply=False):
    episode_bytes = episode_bytes.replace(b"\r\n", b"\n")
    episode = json.loads(episode_bytes)
    reason = eligible(episode_path, episode, config, now)
    if reason:
        return {"action": "none", "reason": reason}
    if api.episode(episode_path) != episode_bytes:
        raise ValueError("O episódio validado não coincide com a main atual.")
    commits = api.request("/commits?path=" + urllib.parse.quote(episode_path, safe="") + "&per_page=100")
    if not commits or len(commits) >= 100:
        return {"action": "none", "reason": "episode_history_ambiguous"}
    introduced = min(timestamp(item["commit"]["committer"]["date"]) for item in commits)
    collected = []
    # Bound the read; fail closed if the queried period cannot be exhausted.
    for page in range(1, 6):
        result = api.request(f"/actions/workflows/{WORKFLOW}/runs?branch=main&per_page=100&page={page}")
        batch = result["workflow_runs"]
        collected.extend(run for run in batch if timestamp(run["created_at"]) >= introduced)
        if len(batch) < 100 or any(timestamp(run["created_at"]) < introduced for run in batch):
            break
    else:
        return {"action": "none", "reason": "run_history_incomplete"}
    matching = []
    for run in collected:
        title = run.get("display_title", "")
        if title == TITLE_PREFIX + episode_path:
            matching.append(run)
        elif title.startswith(TITLE_PREFIX + "news/episodes/"):
            continue
        elif run.get("event") == "push":
            commit = api.request("/commits/" + run["head_sha"])
            paths = [item["filename"] for item in commit.get("files", [])
                     if re.fullmatch(r"news/episodes/[^/]+\.json", item["filename"])]
            if paths == [episode_path] and len(commit.get("files", [])) < 300:
                matching.append(run)
            elif episode_path in paths or len(commit.get("files", [])) >= 300:
                return {"action": "none", "reason": "legacy_run_ambiguous", "run_id": run["id"]}
        else:
            # A legacy workflow_dispatch did not expose its input in the REST run.
            # Its commit alone cannot prove which episode was requested.
            return {"action": "none", "reason": "legacy_run_ambiguous", "run_id": run["id"]}
    jobs = {}
    if matching and all(run.get("status") == "completed" and run.get("conclusion") != "success" for run in matching):
        for run in matching:
            jobs[run["id"]] = api.request(f"/actions/runs/{run['id']}/jobs?filter=latest&per_page=100")["jobs"]
    decision = choose_action(matching, jobs, now)
    if decision["action"] == "rerun":
        source = next(run for run in matching if run["id"] == decision["run_id"])
        if api.episode(episode_path, source["head_sha"]) != episode_bytes:
            return {"action": "none", "reason": "episode_changed_since_render", "run_id": source["id"]}
    if apply and decision["action"] == "dispatch":
        api.request(f"/actions/workflows/{WORKFLOW}/dispatches", {"ref": "main", "inputs": {"edition_path": episode_path}})
    elif apply and decision["action"] == "rerun":
        api.request(f"/actions/runs/{decision['run_id']}/rerun-failed-jobs", {})
    return {**decision, "applied": apply and decision["action"] != "none"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", required=True)
    parser.add_argument("--config", default="config/news-autonomy.json")
    parser.add_argument("--output", default="render-output/news-render-dispatch.json")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    api = GitHub(os.environ["GITHUB_REPOSITORY"], os.environ["GH_TOKEN"])
    decision = ensure_render(api, args.episode, Path(args.episode).read_bytes(),
        json.loads(Path(args.config).read_text(encoding="utf-8")), datetime.now(timezone.utc), args.apply)
    report = {"episode_path": args.episode, "checked_at": datetime.now(timezone.utc).isoformat(), **decision}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("NEWS_RENDER_HANDOFF:", json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
