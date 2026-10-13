"""GitHub-only retention: preserve latest public ODE video and pending runs.

Default is a plan. --apply removes only allowlisted Actions media artifacts/caches.
No YouTube write, repository file write, or PC media cleanup is implemented here.
"""
import argparse
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import re
import sys
import zipfile
import requests

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE if HERE.name == "worker" else HERE.parents[1] / "worker"))
from youtube_publication import youtube_service, assert_channel, EXPECTED_ID, EXPECTED_TITLE, EXPECTED_HANDLE

REPO = "Lucascristao/odinheiroexplica"
MEDIA_NAMES = {"daily-production-review", "news-production-review", "news-single-production-review"}
RECEIPT_NAMES = {"daily-youtube-private-receipt", "news-youtube-private-receipt", "news-single-youtube-private-receipt"}
WORKFLOWS = {".github/workflows/render-daily.yml", ".github/workflows/render-news.yml", ".github/workflows/render-news-single.yml"}
RECOVERY = {".github/workflows/resume-delivery.yml", ".github/workflows/news-resume-publication.yml",
            ".github/workflows/news-auto-thumbnail.yml", ".github/workflows/publish-news.yml", ".github/workflows/upload-thumbnail.yml"}
EDITOR = ".github/workflows/news-autonomous-editor.yml"
CACHE_KEY = re.compile(r"news-live-(\d+)-(\d+)\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")
LOCAL = timezone(timedelta(hours=-3))


class Guard(ValueError):
    """Only fixed, non-sensitive guard codes are returned in reports."""


def timestamp(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise Guard("timestamp_without_timezone")
    return parsed


class GitHub:
    def __init__(self, token):
        self.headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28"}

    def request(self, method, endpoint):
        # External URLs from API response bodies are never accepted as destinations.
        response = requests.request(method, "https://api.github.com/repos/" + REPO + endpoint,
                                    headers=self.headers, timeout=60)
        if method == "DELETE":
            if response.status_code != 204:
                raise Guard("github_delete_not_confirmed")
            return None
        if response.status_code != 200:
            raise Guard(f"github_read_failed_http_{response.status_code}")
        return response.json()

    def pages(self, endpoint, key):
        output = []
        for page in range(1, 21):
            data = self.request("GET", endpoint + ("&" if "?" in endpoint else "?") + f"per_page=100&page={page}")
            values = data.get(key)
            if not isinstance(values, list):
                raise Guard("github_list_invalid")
            output.extend(values)
            if len(values) < 100:
                return output
        raise Guard("github_inventory_incomplete")

    def artifacts(self):
        return self.pages("/actions/artifacts", "artifacts")

    def caches(self):
        return self.pages("/actions/caches", "actions_caches")

    def run(self, run_id):
        return self.request("GET", f"/actions/runs/{int(run_id)}")

    def active_runs(self):
        found = {}
        for status in ("queued", "in_progress", "waiting", "pending", "requested"):
            for run in self.pages("/actions/runs?status=" + status, "workflow_runs"):
                found[run["id"]] = run
        return list(found.values())

    def receipt(self, artifact):
        if artifact.get("expired") or artifact.get("size_in_bytes", 0) > 1024 * 1024:
            raise Guard("receipt_unavailable_or_oversized")
        response = requests.get("https://api.github.com/repos/" + REPO + f"/actions/artifacts/{int(artifact['id'])}/zip",
                                headers=self.headers, timeout=60, stream=True)
        if response.status_code != 200:
            raise Guard("receipt_download_failed")
        payload = bytearray()
        for block in response.iter_content(65536):
            payload.extend(block)
            if len(payload) > 1024 * 1024:
                raise Guard("receipt_download_oversized")
        return parse_receipt(bytes(payload))

    def delete(self, target):
        endpoint = "artifacts" if target["kind"] == "artifact" else "caches"
        self.request("DELETE", f"/actions/{endpoint}/{int(target['id'])}")


def parse_receipt(payload):
    # Only compact receipt JSON is read in memory; no extraction or large media download.
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        entries = archive.infolist()
        if len(entries) > 16 or sum(item.file_size for item in entries) > 2 * 1024 * 1024:
            raise Guard("receipt_archive_oversized")
        matches = [item for item in entries if item.filename in {
            "daily-youtube-private.json", "render-output/daily-youtube-private.json"}]
        if len(matches) != 1 or matches[0].file_size > 128 * 1024:
            raise Guard("receipt_archive_ambiguous")
        data = json.loads(archive.read(matches[0]))
    if (not isinstance(data, dict) or not SHA.fullmatch(str(data.get("video_sha256", "")))
            or not re.fullmatch(r"[A-Za-z0-9_-]{11}", str(data.get("video_id", "")))
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,119}", str(data.get("project_id", "")))):
        raise Guard("receipt_identity_invalid")
    return {key: data.get(key) for key in ("project_id", "video_id", "video_sha256")}


def latest_public(service, channel):
    playlist = channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
    if (channel.get("id") != EXPECTED_ID or not playlist
            or channel.get("snippet", {}).get("title") != EXPECTED_TITLE
            or channel.get("snippet", {}).get("customUrl", "").casefold() != EXPECTED_HANDLE):
        raise Guard("channel_identity_invalid")
    token, found = None, []
    for _ in range(20):
        page = service.playlistItems().list(part="contentDetails", playlistId=playlist,
                                            maxResults=50, pageToken=token).execute()
        ids = [item["contentDetails"]["videoId"] for item in page.get("items", [])]
        videos = service.videos().list(part="snippet,status", id=",".join(ids)).execute().get("items", []) if ids else []
        for video in videos:
            snippet = video.get("snippet", {})
            if snippet.get("channelId") != EXPECTED_ID:
                raise Guard("video_channel_mismatch")
            if video.get("status", {}).get("privacyStatus") != "public":
                continue
            markers = [tag[12:] for tag in snippet.get("tags", []) if isinstance(tag, str) and tag.startswith("ODE_EPISODE_")]
            published = snippet.get("publishedAt")
            timestamp(published)
            found.append({"project_id": markers[0] if len(markers) == 1 else None, "marker_count": len(markers),
                          "video_id": video["id"], "published_at": published,
                          "media_markers": [tag[10:] for tag in snippet.get("tags", [])
                                            if isinstance(tag, str) and tag.startswith("ODE_MEDIA_")]})
        token = page.get("nextPageToken")
        if not token:
            break
    else:
        raise Guard("youtube_upload_inventory_incomplete")
    if not found:
        raise Guard("no_public_channel_video")
    latest = max(found, key=lambda item: timestamp(item["published_at"]))
    if len({item["video_id"] for item in found if timestamp(item["published_at"]) == timestamp(latest["published_at"])}) != 1:
        raise Guard("latest_public_timestamp_ambiguous")
    if latest["marker_count"] != 1 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,119}", str(latest["project_id"])):
        raise Guard("latest_unmanaged_public")
    del latest["marker_count"]
    return latest


def dependency_family(key):
    python = re.fullmatch(r"setup-python-Linux-x64-(?:(?:20\.04|22\.04|24\.04)-Ubuntu-python-)?(\d+\.\d+)\.\d+-pip-.+", key)
    if python:
        return "setup-python-" + python[1]
    for prefix in ("node-cache-Linux-x64-npm-", "playwright-chromium-Linux-"):
        if key.startswith(prefix) and len(key) > len(prefix):
            return prefix
    return None


def make_plan(github, service, channel, *, now=None, protected=(), closed=(), require_night_date=None,
              prune_stale_dependencies=False, protected_caches=()):
    now = now or datetime.now(timezone.utc)
    report = {"version": "1.0", "repository": REPO, "created_at_utc": now.isoformat(),
              "status": "guarded", "reason": None, "delete": [], "keep": [], "removed": []}
    latest = latest_public(service, channel)
    if require_night_date and latest["project_id"] != "noticia-" + require_night_date + "-noite":
        report.update(reason="required_night_not_public", latest_public=latest)
        return report
    artifacts, caches = github.artifacts(), github.caches()
    active = github.active_runs()
    for run in active:
        if run.get("repository", {}).get("full_name", "").casefold() != REPO.casefold():
            raise Guard("active_run_repository_identity_mismatch")
    own = os.getenv("GITHUB_RUN_ID", "")
    own_id = int(own) if re.fullmatch(r"[1-9]\d*", own) else None
    for run in active:
        if run.get("id") == own_id and run.get("path", "").split("@", 1)[0] != ".github/workflows/news-cloud-retention.yml":
            raise Guard("own_retention_run_identity_mismatch")
    active = [run for run in active if run.get("id") != own_id]
    if any(run.get("path", "").split("@", 1)[0] in RECOVERY for run in active):
        report.update(reason="active_recovery_source_unresolved", latest_public=latest)
        return report  # Active dispatch inputs do not expose the source run through run API.
    matches, receipts, opaque_runs = [], [], set()
    for artifact in artifacts:
        if artifact.get("name") not in RECEIPT_NAMES:
            continue
        run_id = artifact.get("workflow_run", {}).get("id")
        try:
            receipt = github.receipt(artifact)
        except (Guard, ValueError, OSError, zipfile.BadZipFile):
            if isinstance(run_id, int) and run_id > 0:
                opaque_runs.add(run_id)
            continue
        if isinstance(run_id, int) and run_id > 0:
            receipts.append((run_id, receipt))
        if receipt["video_id"] == latest["video_id"] and receipt["project_id"] == latest["project_id"]:
            if latest["media_markers"] and receipt["video_sha256"][:16] not in latest["media_markers"]:
                continue
            if isinstance(run_id, int) and run_id > 0:
                matches.append((run_id, receipt["video_sha256"]))
    if not matches or len({sha for _, sha in matches}) != 1:
        report.update(reason="latest_public_run_unproven", latest_public=latest)
        return report
    latest_runs = {run_id for run_id, _ in matches}
    keep_runs = set(protected) | latest_runs | {run["id"] for run in active}
    closed = set(closed)
    keep_runs.update(opaque_runs - closed)
    receipt_ids = list({receipt["video_id"] for _, receipt in receipts if isinstance(receipt["video_id"], str)})
    states = {}
    for start in range(0, len(receipt_ids), 50):
        for video in service.videos().list(part="snippet,status", id=",".join(receipt_ids[start:start+50])).execute().get("items", []):
            if video.get("snippet", {}).get("channelId") != EXPECTED_ID:
                raise Guard("receipt_video_channel_mismatch")
            states[video["id"]] = video.get("status", {}).get("privacyStatus")
    keep_runs.update(run_id for run_id, receipt in receipts if run_id not in closed and states.get(receipt["video_id"]) != "public")
    report["latest_public"] = {**latest, "video_sha256": matches[0][1], "run_ids": sorted(latest_runs)}
    closed, runs = set(closed), {}
    def eligible(run_id):
        if run_id in keep_runs or not isinstance(run_id, int) or run_id <= 0:
            return False
        if run_id not in runs:
            runs[run_id] = github.run(run_id)
        run = runs[run_id]
        if run.get("id") != run_id or run.get("repository", {}).get("full_name", "").casefold() != REPO.casefold():
            raise Guard("run_repository_identity_mismatch")
        if run.get("path", "").split("@", 1)[0] not in WORKFLOWS or run.get("status") != "completed":
            return False
        older = timestamp(run["updated_at"]).astimezone(LOCAL).date() < now.astimezone(LOCAL).date()
        return run_id in closed or (older and run.get("conclusion") == "success")
    for artifact in artifacts:
        if artifact.get("name") not in MEDIA_NAMES or artifact.get("expired"):
            continue  # Source code, all receipts, confirmations and QA artifacts are preserved.
        run_id = artifact.get("workflow_run", {}).get("id")
        item = {"kind": "artifact", "id": artifact["id"], "name": artifact["name"], "run_id": run_id,
                "bytes": artifact.get("size_in_bytes", 0), "created_at": artifact.get("created_at")}
        report["delete" if eligible(run_id) else "keep"].append(item)
    for cache in caches:
        match = CACHE_KEY.fullmatch(cache.get("key", ""))
        if not match or cache.get("ref") != "refs/heads/main":
            continue
        run_id = int(match[1])
        item = {"kind": "cache", "id": cache["id"], "name": cache["key"], "run_id": run_id,
                "bytes": cache.get("size_in_bytes", 0), "created_at": cache.get("created_at")}
        voice_active = any(run.get("path", "").split("@", 1)[0] in WORKFLOWS | {EDITOR} for run in active)
        report["delete" if not voice_active and eligible(run_id) else "keep"].append(item)
    if prune_stale_dependencies:
        families = {}
        for cache in caches:
            family = dependency_family(cache.get("key", ""))
            if family and cache.get("ref") == "refs/heads/main":
                families.setdefault(family, []).append(cache)
        for family_caches in families.values():
            keep = set(protected_caches) | {max(family_caches, key=lambda value: timestamp(value[field]))["id"]
                                            for field in ("last_accessed_at", "created_at")}
            for cache in family_caches:
                item = {"kind": "cache", "id": cache["id"], "name": cache["key"], "run_id": None,
                        "bytes": cache.get("size_in_bytes", 0), "created_at": cache.get("created_at")}
                report["keep" if active or cache["id"] in keep else "delete"].append(item)
    report.update(status="planned", planned_bytes=sum(item["bytes"] for item in report["delete"]),
                  protected_run_ids=sorted(keep_runs), closed_run_ids=sorted(closed))
    return report


def apply_plan(github, service, channel, report, **options):
    if report["status"] != "planned":
        return report
    fresh = make_plan(github, service, channel, **options)
    if fresh["status"] != "planned" or fresh["latest_public"] != report["latest_public"] or fresh["delete"] != report["delete"]:
        raise Guard("live_identity_or_inventory_changed")
    # The entire live inventory is checked before the first irreversible mutation.
    report["status"] = "applied"
    for target in report["delete"]:
        github.delete(target)
        report["removed"].append(target)
    report["reclaimed_bytes"] = sum(item["bytes"] for item in report["removed"])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--protect-run", type=int, action="append", default=[])
    parser.add_argument("--closed-run", type=int, action="append", default=[])
    parser.add_argument("--require-night-date", help="Scheduled cleanup requires this exact night edition public.")
    parser.add_argument("--prune-stale-dependencies", action="store_true")
    parser.add_argument("--protect-cache", type=int, action="append", default=[])
    args = parser.parse_args()
    report = {"repository": REPO, "status": "guarded", "delete": [], "removed": []}
    try:
        token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
        if not token:
            raise Guard("github_token_unavailable")
        github, service = GitHub(token), youtube_service()
        channel = assert_channel(service)  # Canonical ID + title + handle validation.
        if args.require_night_date and datetime.strptime(args.require_night_date, "%Y-%m-%d").strftime("%Y-%m-%d") != args.require_night_date:
            raise Guard("night_date_invalid")
        options = {"protected": args.protect_run, "closed": args.closed_run, "require_night_date": args.require_night_date,
                   "prune_stale_dependencies": args.prune_stale_dependencies, "protected_caches": args.protect_cache}
        report = make_plan(github, service, channel, **options)
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if args.apply:
            apply_plan(github, service, channel, report, **options)
    except Exception as error:
        report.update(status="guarded" if not report["removed"] else "partial", reason=str(error) if isinstance(error, Guard) else "cloud_retention_error")
    report["reclaimed_bytes"] = sum(item["bytes"] for item in report["removed"])
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("CLOUD_MEDIA_RETENTION", report["status"], "planned", len(report["delete"]), "removed", len(report["removed"]))
    if report["status"] in {"guarded", "partial"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
