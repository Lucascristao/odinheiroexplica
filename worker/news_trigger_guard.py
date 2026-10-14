"""Recover a missing editorial trigger, never an existing episode or upload.

Only GitHub is contacted. Publication receipts prove an upload was recorded;
they do not claim that YouTube is currently public. No model/voice API is used.
"""
from datetime import datetime, timedelta, timezone
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler, urlopen
import zipfile
from zoneinfo import ZoneInfo

SLOTS = ("manha", "meio-dia", "noite")
MAX_ATTEMPTS = 3
COOLDOWN = timedelta(minutes=20)
EDITOR = "news-autonomous-editor.yml"
RENDER = "render-news-single.yml"
RECEIPT_ARTIFACT = "news-single-youtube-private-receipt"
MAX_RESPONSE = 8 * 1024 * 1024


def aware(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Operational timestamp requires timezone")
    return result


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GitHub:
    """Small authenticated REST client; never forward the token to blob storage."""
    def __init__(self, repository, token):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or not token:
            raise ValueError("GitHub repository/token unavailable")
        self.base = "https://api.github.com/repos/" + repository
        self.token = token
        self.opener = build_opener(NoRedirect)
        self.receipts = {}

    def request(self, path, *, payload=None, missing_ok=False, archive=False):
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(self.base + path, data=data, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json", "User-Agent": "ode-news-trigger-guard",
        }, method="POST" if payload is not None else "GET")
        try:
            response = self.opener.open(request, timeout=30)
        except HTTPError as error:
            if error.code == 404 and missing_ok:
                return None
            if archive and error.code in (301, 302, 303, 307, 308):
                location = error.headers.get("Location", "")
                url = urlparse(location)
                if url.scheme != "https" or not url.netloc or url.username or url.password:
                    raise ValueError("Unsafe artifact location") from None
                # Signed artifact URL came from GitHub; no Authorization header.
                response = urlopen(Request(location), timeout=30)
            else:
                raise RuntimeError("GitHub request failed (HTTP " + str(error.code) + ")") from None
        with response:
            body = response.read(MAX_RESPONSE + 1)
        if len(body) > MAX_RESPONSE:
            raise ValueError("GitHub response exceeded bounded size")
        return body if archive else (json.loads(body) if body else {})

    def episode_exists(self, path):
        item = self.request("/contents/" + path + "?ref=main", missing_ok=True)
        if item is not None and item.get("type") != "file":
            raise ValueError("Episode path is not a file")
        return item is not None

    def runs(self, workflow, day, zone):
        start = datetime.fromisoformat(day).replace(tzinfo=zone).astimezone(timezone.utc)
        query = urlencode({"branch": "main", "per_page": 100,
                           "created": ">=" + start.isoformat().replace("+00:00", "Z")})
        data = self.request("/actions/workflows/" + workflow + "/runs?" + query)
        if data.get("total_count", 0) > 100:
            raise ValueError("Incomplete workflow history")
        return data.get("workflow_runs", [])

    def upload_for_episode(self, runs, project_id):
        for run in runs:
            data = self.request(f"/actions/runs/{int(run['id'])}/artifacts?per_page=100")
            if data.get("total_count", 0) > 100:
                raise ValueError("Incomplete artifact history")
            for artifact in data.get("artifacts", []):
                if artifact.get("name") != RECEIPT_ARTIFACT:
                    continue
                if artifact.get("expired"):
                    raise ValueError("Upload receipt expired; cannot rule out an upload")
                identity = artifact["id"]
                if identity not in self.receipts:
                    if artifact.get("size_in_bytes", 0) > 2 * 1024 * 1024:
                        raise ValueError("Unexpectedly large upload receipt artifact")
                    blob = self.request(f"/actions/artifacts/{int(identity)}/zip", archive=True)
                    digest = artifact.get("digest")
                    if digest and digest != "sha256:" + hashlib.sha256(blob).hexdigest():
                        raise ValueError("Upload receipt artifact digest mismatch")
                    self.receipts[identity] = read_upload_receipt(blob)
                receipt = self.receipts[identity]
                if receipt.get("project_id") != project_id:
                    continue
                if (receipt.get("destination") != "youtube"
                        or receipt.get("privacy_requested") != "private"
                        or not re.fullmatch(r"[A-Za-z0-9_-]{11}", str(receipt.get("video_id", "")))
                        or not re.fullmatch(r"[0-9a-f]{64}", str(receipt.get("video_sha256", "")))):
                    raise ValueError("Upload receipt identity is incomplete")
                return {"video_id": receipt["video_id"], "run_id": run["id"], "artifact_id": identity}
        return None

    def dispatch_editor(self, day, slot):
        self.request("/actions/workflows/" + EDITOR + "/dispatches",
                     payload={"ref": "main", "inputs": {"date": day, "slot": slot}})


def read_upload_receipt(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        matches = [item for item in archive.infolist()
                   if item.filename.rsplit("/", 1)[-1] == "daily-youtube-private.json"]
        if len(matches) != 1 or matches[0].file_size > 128 * 1024:
            raise ValueError("Upload receipt missing or ambiguous")
        return json.loads(archive.read(matches[0]))


def active_window(config, slot, now):
    zone = ZoneInfo(config["timezone"])
    local = now.astimezone(zone)
    index = SLOTS.index(slot)
    start = datetime.fromisoformat(local.date().isoformat() + "T" + config["production_hours"][index]).replace(tzinfo=zone)
    publication = datetime.fromisoformat(local.date().isoformat() + "T" + config["publication_hours"][index]).replace(tzinfo=zone)
    tolerance = config.get("late_tolerance_minutes", 0) if config.get("publish_if_late") is True else 0
    if type(tolerance) is not int or not 0 <= tolerance <= 180 or publication <= start:
        raise ValueError("Invalid configured production/publication window")
    # Stop new editorial attempts one hour after the target, at the latest.
    # This is 09h/13h/21h under current config and never expands its tolerance.
    end = publication + timedelta(minutes=min(60, tolerance))
    return config.get("enabled") is True and start <= local < end, local.date().isoformat(), start, end


def editor_identity(run, config):
    title = run.get("display_title", "")
    match = re.fullmatch(r"ODE editor \| (\d{4}-\d{2}-\d{2}) \| (manha|meio-dia|noite)", title)
    if match:
        return match.groups()
    # Scheduled runs have no inputs/date. Their name preserves the actual cron;
    # bind it to the most recent nominal occurrence, not the runner start time.
    cron = re.fullmatch(r"ODE editor \| automatico \| (0|17) (9|13|21) \* \* \*", title)
    if cron and run.get("event") == "schedule":
        minute, hour = map(int, cron.groups())
        created = aware(run["created_at"]).astimezone(timezone.utc)
        nominal = created.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if nominal > created:
            nominal -= timedelta(days=1)
        local = nominal.astimezone(ZoneInfo(config["timezone"]))
        for index, start in enumerate(config["production_hours"]):
            if local.strftime("%H") == start[:2]:
                return local.date().isoformat(), SLOTS[index]
    return None


def plan_slot(api, config, slot, now):
    allowed, day, start, end = active_window(config, slot, now)
    result = {"slot": slot, "news_date": day, "window_start": start.isoformat(),
              "window_end": end.isoformat(), "episode_path": f"news/episodes/{day}-{slot}.json"}
    if not allowed:
        return {**result, "state": "outside", "reason": "outside_active_window_or_disabled"}
    if api.episode_exists(result["episode_path"]):
        return {**result, "state": "delegated_to_render", "reason": "episode_json_exists"}
    zone = ZoneInfo(config["timezone"])
    editors = api.runs(EDITOR, day, zone)
    renders = api.runs(RENDER, day, zone)
    # Legacy active runs have no reliable episode identity. Block conservatively;
    # do not infer an upload or a completed edition from their generic titles.
    active = [run for run in editors + renders if run.get("status") != "completed"]
    if active:
        return {**result, "state": "active", "reason": "editor_or_render_active", "run_ids": [run["id"] for run in active]}
    upload = api.upload_for_episode(renders, "noticia-" + day + "-" + slot)
    if upload:
        return {**result, "state": "completed", "reason": "exact_episode_upload_receipt", **upload}
    matching = [run for run in editors if editor_identity(run, config) == (day, slot)]
    completed = [run for run in matching if run.get("conclusion") == "success"]
    if completed:
        return {**result, "state": "completed", "reason": "editor_succeeded_but_json_absent", "run_id": completed[0]["id"]}
    attempts = sum(max(1, int(run.get("run_attempt", 1))) for run in matching)
    result["attempts"] = attempts
    if attempts >= MAX_ATTEMPTS:
        return {**result, "state": "maxattempt", "reason": "three_editor_attempts_reached"}
    if matching:
        latest = max(aware(run.get("updated_at") or run["created_at"]) for run in matching)
        if now < latest + COOLDOWN:
            return {**result, "state": "cooldown", "reason": "twenty_minutes_since_last_attempt_not_elapsed",
                    "retry_after": (latest + COOLDOWN).isoformat()}
    return {**result, "state": "missing", "reason": "missing_episode_and_no_active_or_uploaded_production"}


def run_watchdog(api, config, now, dry_run=True):
    results = []
    for slot in SLOTS:
        result = plan_slot(api, config, slot, now)
        if result["state"] == "missing" and not dry_run:
            # Capture/receipt reads can take time. Recheck current main, runs and
            # cooldown immediately before the only permitted write.
            result = plan_slot(api, config, slot, now)
            if result["state"] == "missing":
                api.dispatch_editor(result["news_date"], slot)
                result = {**result, "state": "dispatch", "reason": "editor_workflow_dispatch_accepted",
                          "next_attempt": result["attempts"] + 1}
        results.append(result)
    return {"checked_at": now.isoformat(), "dry_run": dry_run, "max_attempts": MAX_ATTEMPTS,
            "cooldown_minutes": 20, "slots": results}


def write_report(result, output):
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["### Conferência dos gatilhos de notícias", "", "Modo: " + ("somente leitura" if result.get("dry_run") else "recuperação automática"), ""]
    for item in result.get("slots", []):
        lines.append(f"- {item['news_date']} {item['slot']}: **{item['state']}** — {item['reason']}")
    if result.get("error_type"):
        lines.append("Falha de consulta; nenhuma recuperação adicional foi autorizada. Tipo: " + result["error_type"])
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write("\n".join(lines) + "\n")
    print(json.dumps(result, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/news-autonomy.json")
    parser.add_argument("--output", default="render-output/news-trigger-watchdog.json")
    parser.add_argument("--dispatch", action="store_true", help="Permit the bounded editor trigger; default is read-only.")
    args = parser.parse_args()
    result = {"dry_run": not args.dispatch, "slots": []}
    try:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        api = GitHub(os.environ["GITHUB_REPOSITORY"], os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN"))
        result = run_watchdog(api, config, datetime.now(timezone.utc), dry_run=not args.dispatch)
    except Exception as error:
        result["error_type"] = type(error).__name__
        write_report(result, args.output)
        raise SystemExit("Falha segura na conferência dos gatilhos; consultar o relatório.") from None
    write_report(result, args.output)


if __name__ == "__main__":
    main()
