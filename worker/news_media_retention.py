"""Local media retention after a fresh, identity-checked public night edition.

Default: an auditable plan. --apply deletes only individually verified, untracked
media files belonging to older completed productions. Missing lineage is preserved.
This module never calls YouTube, an LLM, or another remote service.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

ALLOWED = ("work", "render-output", "run_artifacts", "public/generated-audio", "public/processed-audio")
MEDIA = {".mp4", ".wav", ".pcm"}  # ZIP archives can contain source/code; keep them.
INVENTORY_MEDIA = MEDIA | {".zip"}
DEPENDENCIES = {"node_modules", "site-packages", "capture-deps", "python-deps", "venv", ".venv", "__pycache__", ".git"}
LOCAL_ZONE = timezone(timedelta(hours=-3))  # America/Fortaleza has no DST.
CHANNEL_ID = "UCd7laspUAiQk0DEF9NQ-itw"
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{2,119}\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")
VIDEO = re.compile(r"[A-Za-z0-9_-]{11}\Z")


class UnsafePath(ValueError):
    pass


def safe_path(root: Path, supplied, *, media=False) -> Path:
    raw = os.fspath(supplied)
    if ".." in raw.replace("\\", "/").split("/"):
        raise UnsafePath("Path traversal refused.")
    path = Path(raw)
    path = path if path.is_absolute() else root / path
    try:
        relative = path.relative_to(root)
    except ValueError:
        raise UnsafePath("Path outside workspace.") from None
    if any(":" in part for part in relative.parts):
        raise UnsafePath("Alternate data streams refused.")
    current = root
    for part in ("", *relative.parts):
        if part:
            current /= part
        if current.exists() or current.is_symlink():
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise UnsafePath("Symlink, junction or reparse point refused.")
            if stat.S_ISREG(info.st_mode) and getattr(info, "st_nlink", 1) > 1:
                raise UnsafePath("Hard-linked file refused.")
    if path.resolve().is_relative_to(root) is False:
        raise UnsafePath("Resolved path outside workspace.")
    if media and not any(path.is_relative_to(root / directory) and path != root / directory for directory in ALLOWED):
        raise UnsafePath("Media path outside allowed directories.")
    return path


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def read_json(root: Path, path) -> dict:
    target = safe_path(root, path)
    if not target.is_file() or target.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("Missing or oversized metadata.")
    value = json.loads(target.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("Metadata must be an object.")
    return value


def project_id(data: dict):
    value = data.get("project_id") or data.get("episode_id")
    return value if isinstance(value, str) and ID.fullmatch(value) else None


def public_pair(confirmation: dict, upload: dict) -> bool:
    return bool(confirmation.get("public_confirmed") is True
                and confirmation.get("privacy_observed") == "public"
                and project_id(confirmation) == project_id(upload)
                and project_id(upload)
                and isinstance(upload.get("video_id"), str) and VIDEO.fullmatch(upload["video_id"])
                and confirmation.get("video_id") == upload["video_id"]
                and isinstance(upload.get("video_sha256"), str) and SHA.fullmatch(upload["video_sha256"])
                and confirmation.get("channel_id", CHANNEL_ID) == CHANNEL_ID
                and upload.get("channel_id", CHANNEL_ID) == CHANNEL_ID)


def validate_trigger(confirmation: dict, upload: dict, now: datetime, max_age_minutes=60):
    expected = "noticia-" + now.astimezone(LOCAL_ZONE).date().isoformat() + "-noite"
    if not public_pair(confirmation, upload) or project_id(confirmation) != expected:
        raise ValueError("Fresh public night episode/video identity required.")
    # This stage is only issued by the canonical monitor after channel/tag/ID checks.
    if confirmation.get("stage") != "public_confirmed":
        raise ValueError("Canonical identity-checked monitor confirmation required.")
    checked = datetime.fromisoformat(str(confirmation.get("checked_at_utc", "")).replace("Z", "+00:00"))
    if checked.tzinfo is None or not timedelta(0) <= now - checked <= timedelta(minutes=max_age_minutes):
        raise ValueError("Publication confirmation stale, future-dated or missing timezone.")
    if confirmation.get("news_date", expected[8:18]) != expected[8:18]:
        raise ValueError("Edition date differs from current local night.")


def tracked_files(root: Path):
    result = subprocess.run(["git", "-c", f"safe.directory={root.as_posix()}", "ls-files", "-z"],
                            cwd=root, check=True, capture_output=True)
    return set(result.stdout.decode("utf-8").split("\0")) - {""}


def scan(root: Path):
    """Inspect only production directories; dependencies and credentials are not read."""
    files = []
    for directory in ALLOWED:
        base = safe_path(root, directory)
        if not base.exists():
            continue
        for current, dirs, names in os.walk(base, followlinks=False):
            for name in list(dirs):
                safe_path(root, Path(current) / name)
                if name.casefold() in DEPENDENCIES:
                    dirs.remove(name)
            for name in names:
                path = safe_path(root, Path(current) / name)
                if not path.is_file():
                    raise UnsafePath("Non-regular artifact entry refused.")
                files.append(path)
    return files


def lineage(root: Path, files):
    scopes = []
    evidence = set()
    for path in files:
        local = path.relative_to(root).as_posix()
        if local.endswith(("/video/generated/daily-project.json", "/video/data/daily.json")):
            scope = path.parents[2]
        elif path.name in {".ode-temporary-owner.json", "daily-resume-receipt.json"}:
            scope = path.parent if path.name.startswith(".") else path.parents[2]
        else:
            continue
        data = read_json(root, path)
        owner = project_id(data)
        if owner and scope != root:
            scopes.append((scope, owner))
            evidence.add(path)
    registry = root / "work/temporary-ownership.json"
    if registry.exists():
        data = read_json(root, registry)
        evidence.add(registry)
        for entry in data.get("entries", []):
            if not isinstance(entry, dict) or not project_id(entry):
                continue
            target = safe_path(root, entry.get("path", ""))
            if not any(target.is_relative_to(root / directory) and target != root / directory for directory in ALLOWED):
                continue  # The evergreen registry also owns generated code/audit paths.
            # Registration must include its original source fingerprint.
            if isinstance(entry.get("source_project_sha256"), str) and SHA.fullmatch(entry["source_project_sha256"]):
                scopes.append((target, project_id(entry)))
    return scopes, evidence


def owner_of(path: Path, scopes):
    # Conflicting ancestors are deliberately preserved, even if one is more specific.
    owners = {owner for scope, owner in scopes if path == scope or path.is_relative_to(scope)}
    return next(iter(owners)) if len(owners) == 1 else None


def reviewed_inventory(root: Path, supplied, files, tracked):
    if supplied is None:
        return {}, None
    manifest_path = safe_path(root, supplied)
    data = read_json(root, manifest_path)
    if data.get("approved") is not True or data.get("purpose") != "past_production_media":
        raise ValueError("Inventory requires explicit local approval for past production media.")
    entries = data.get("files")
    if not isinstance(entries, list):
        raise ValueError("Inventory files must be a list.")
    result = {}
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not Path(item["path"]).is_absolute():
            raise ValueError("Inventory requires absolute file paths.")
        path = safe_path(root, item["path"], media=True)
        if path not in files or path.suffix.lower() not in INVENTORY_MEDIA:
            raise ValueError("Inventory path outside scanned production media (dependencies excluded).")
        if (path.relative_to(root).as_posix() in tracked or not isinstance(item.get("sha256"), str)
                or not SHA.fullmatch(item["sha256"]) or type(item.get("bytes")) is not int
                or path.stat().st_size != item["bytes"] or digest(path) != item["sha256"]):
            raise ValueError("Inventory media tracked or changed; review again.")
        if path in result:
            raise ValueError("Duplicate inventory path.")
        result[path] = item
    return result, manifest_path


def inventory_candidates(root: Path, *, tracked=None):
    """Produce an UNAPPROVED inventory for human/local review, never delete."""
    root = Path(root).absolute()
    files = scan(root)
    scopes, _ = lineage(root, files)
    tracked = set(tracked) if tracked is not None else tracked_files(root)
    return {"version": "1.0", "approved": False, "purpose": "past_production_media",
            "created_at_utc": datetime.now(timezone.utc).isoformat(), "files": [
                {"path": str(path), "project_id": owner_of(path, scopes), "bytes": path.stat().st_size,
                 "sha256": digest(path)} for path in files
                if path.suffix.lower() in INVENTORY_MEDIA and path.relative_to(root).as_posix() not in tracked]}


def completed_productions(root: Path):
    completed = {}
    evidence = set()
    production = safe_path(root, "production")
    if not production.exists():
        return completed, evidence
    for directory in production.iterdir():
        safe_path(root, directory)
        if not directory.is_dir():
            continue
        confirmation = directory / "publication-confirmation.json"
        upload = directory / "youtube-upload-receipt.json"
        if confirmation.exists() and upload.exists():
            a, b = read_json(root, confirmation), read_json(root, upload)
            evidence.update((confirmation, upload))
            if public_pair(a, b) and project_id(a) == directory.name:
                completed[project_id(a)] = b["video_sha256"]
        # Evergreen caches are retained; their Drive cleanup has a separate contract.
    return completed, evidence


def make_plan(root: Path, confirmation_path, upload_path, *, now=None, tracked=None,
              pending_projects=(), keep_video=None, keep_sha256=None, inventory=None):
    root = Path(root).absolute()
    safe_path(root, root)
    now = now or datetime.now(timezone.utc)
    result = {"version": "1.0", "created_at_utc": now.isoformat(), "status": "skipped",
              "latest_project_id": None, "video_id": None, "delete": [], "preserve": [],
              "reclaimed_bytes": 0, "removed": [], "reason": None}
    try:
        confirmation = read_json(root, confirmation_path)
        upload = read_json(root, upload_path)
        validate_trigger(confirmation, upload, now)
    except (ValueError, OSError) as error:
        # No arbitrary metadata, credentials or exception bodies enter the audit.
        result["reason"] = "fresh_public_night_confirmation_unavailable"
        if isinstance(error, UnsafePath):
            raise
        return result
    latest, latest_sha = project_id(upload), upload["video_sha256"]
    result.update(status="planned", latest_project_id=latest, video_id=upload["video_id"], latest_video_sha256=latest_sha,
                  confirmation_path=safe_path(root, confirmation_path).relative_to(root).as_posix(),
                  upload_receipt_path=safe_path(root, upload_path).relative_to(root).as_posix())
    files = scan(root)
    scopes, evidence = lineage(root, files)
    result["lineage_paths"] = sorted(path.relative_to(root).as_posix() for path in evidence)
    completed, completion_evidence = completed_productions(root)
    evidence.update(completion_evidence)
    evidence.update((safe_path(root, confirmation_path), safe_path(root, upload_path)))
    pending = set(pending_projects)
    result["context_paths"] = []
    for relative in ("work/production-state.json", "video/data/daily.json"):
        state_path = safe_path(root, relative)
        if state_path.exists():
            state = read_json(root, state_path)
            evidence.add(state_path)
            result["context_paths"].append(relative)
            if relative == "work/production-state.json" and project_id(state):
                recent = True
                if state.get("updated_at"):
                    try:
                        updated = datetime.fromisoformat(str(state["updated_at"]).replace("Z", "+00:00"))
                        recent = updated.tzinfo is not None and timedelta(0) <= now - updated <= timedelta(days=1)
                    except ValueError:
                        recent = True  # An undecodable runtime state is preserved.
                if recent and state.get("stage") not in {"complete", "failed", "cancelled", "closed"}:
                    pending.add(project_id(state))
    tracked = set(tracked) if tracked is not None else tracked_files(root)
    inventory_files, manifest_path = reviewed_inventory(root, inventory, files, tracked)
    if manifest_path:
        evidence.add(manifest_path)
        result["inventory_path"] = manifest_path.relative_to(root).as_posix()
    # The caller supplies active/resumable remote IDs after reading current runs.
    # An old failed window is not forever pending merely because it has source JSON.
    protected = None
    if keep_video is not None or keep_sha256 is not None:
        if not keep_video or keep_sha256 != latest_sha:
            raise ValueError("--keep-video and --keep-sha256 must identify the latest upload.")
        protected = safe_path(root, keep_video, media=True)
        if protected.suffix.lower() != ".mp4" or not protected.is_file() or digest(protected) != latest_sha:
            raise ValueError("Latest kept MP4 missing or hash differs from upload.")
    hashes = {}
    scope_complete = set()
    for path in files:
        if path.suffix.lower() != ".mp4":
            continue
        hashes[path] = digest(path)
        owner = owner_of(path, scopes)
        if owner in completed and hashes[path] == completed[owner]:
            scope_complete.update((scope, owner) for scope, candidate in scopes
                                  if candidate == owner and (path == scope or path.is_relative_to(scope)))
    for path in files:
        if path.suffix.lower() not in MEDIA and path not in inventory_files:
            continue
        owner = owner_of(path, scopes)
        local = path.relative_to(root).as_posix()
        value = hashes.get(path) or digest(path)
        item = {"path": local, "project_id": owner, "bytes": path.stat().st_size, "sha256": value}
        if local in tracked:
            reason = "tracked"
        elif (path == protected or value == latest_sha
              or any(candidate == latest for scope, candidate in scopes if path == scope or path.is_relative_to(scope))):
            reason = "latest_publication"
        elif owner is None and path not in inventory_files:
            reason = "unknown_or_conflicting_owner"
        elif any(candidate in pending for scope, candidate in scopes if path == scope or path.is_relative_to(scope)):
            reason = "pending_production"
        elif path in inventory_files:
            item["authorization"] = "reviewed_past_media_inventory"
            result["delete"].append(item)
            continue
        elif owner not in completed:
            reason = "pending_or_unconfirmed_production"
        elif not any(candidate == owner and path.is_relative_to(scope) for scope, candidate in scope_complete):
            reason = "completed_media_lineage_unproven"
        elif path.suffix.lower() == ".mp4" and value != completed[owner]:
            reason = "different_video_revision"
        else:
            result["delete"].append(item)
            continue
        result["preserve"].append({**item, "reason": reason})
    result["evidence"] = [{"path": path.relative_to(root).as_posix(), "sha256": digest(path)}
                          for path in sorted(evidence)]
    result["pending_project_ids"] = sorted(pending)
    result["planned_bytes"] = sum(item["bytes"] for item in result["delete"])
    result["latest_mp4_local"] = any(value == latest_sha for value in hashes.values())
    return result


def apply_plan(root: Path, plan: dict, *, tracked=None, now=None):
    if plan["status"] != "planned":
        return plan
    root = Path(root).absolute()
    now = now or datetime.now(timezone.utc)
    created = datetime.fromisoformat(plan["created_at_utc"])
    if not timedelta(0) <= now - created <= timedelta(minutes=5):
        raise ValueError("Plan stale; generate a fresh plan.")
    # Validate every evidence file and candidate before the first deletion.
    for item in plan["evidence"]:
        path = safe_path(root, item["path"])
        if not path.is_file() or digest(path) != item["sha256"]:
            raise ValueError("Production identity/ownership changed; nothing removed.")
    validate_trigger(read_json(root, plan["confirmation_path"]), read_json(root, plan["upload_receipt_path"]), now)
    _, current_lineage = lineage(root, scan(root))
    if sorted(path.relative_to(root).as_posix() for path in current_lineage) != plan["lineage_paths"]:
        raise ValueError("Source/run ownership appeared or disappeared; nothing removed.")
    context = [relative for relative in ("work/production-state.json", "video/data/daily.json")
               if safe_path(root, relative).exists()]
    if context != plan["context_paths"]:
        raise ValueError("Pending production state appeared or disappeared; nothing removed.")
    current_tracked = set(tracked) if tracked is not None else tracked_files(root)
    targets = []
    for item in plan["delete"]:
        path = safe_path(root, item["path"], media=True)
        permitted = INVENTORY_MEDIA if item.get("authorization") == "reviewed_past_media_inventory" else MEDIA
        if (path.suffix.lower() not in permitted or item["path"] in current_tracked
                or not path.is_file() or path.stat().st_size != item["bytes"] or digest(path) != item["sha256"]):
            raise ValueError("Media changed or tracked; nothing removed.")
        targets.append((path, item))
    # Delete files, never trees; all source/receipt/history JSON and directories remain.
    plan["status"] = "applied"
    for path, item in targets:
        safe_path(root, path, media=True)
        if digest(path) != item["sha256"]:
            raise ValueError("Media changed during apply; stopped.")
        path.unlink()
        plan["removed"].append(item)
        plan["reclaimed_bytes"] += item["bytes"]
    plan["applied_at_utc"] = now.isoformat()
    return plan


def write_audit(root: Path, destination, plan: dict):
    target = safe_path(root, destination)
    # Audits cannot overwrite a source, receipt, code file or production metadata.
    if not target.is_relative_to(root / "work/media-retention") or target.suffix.lower() != ".json":
        raise UnsafePath("Audit must be a JSON inside work/media-retention.")
    target.parent.mkdir(parents=True, exist_ok=True)
    safe_path(root, target)
    target.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--confirmation")
    parser.add_argument("--upload-receipt")
    parser.add_argument("--prepare-inventory", action="store_true", help="Write an unapproved local inventory only.")
    parser.add_argument("--pending-project", action="append", default=[])
    parser.add_argument("--keep-video")
    parser.add_argument("--keep-sha256")
    parser.add_argument("--inventory", help="Explicitly approved JSON inventory of absolute old-media paths + SHA256 + bytes.")
    parser.add_argument("--audit", help="JSON audit path inside work/media-retention; default is a new timestamped file.")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).absolute()
    audit = args.audit or "work/media-retention/" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
    if args.prepare_inventory:
        if args.apply:
            parser.error("--prepare-inventory cannot be combined with --apply")
        inventory = inventory_candidates(root)
        write_audit(root, audit, inventory)
        print("NEWS_MEDIA_INVENTORY unapproved", "files", len(inventory["files"]),
              "bytes", sum(item["bytes"] for item in inventory["files"]))
        return
    if not args.confirmation or not args.upload_receipt:
        parser.error("--confirmation and --upload-receipt are required for retention")
    plan = make_plan(root, args.confirmation, args.upload_receipt, pending_projects=args.pending_project,
                     keep_video=args.keep_video, keep_sha256=args.keep_sha256, inventory=args.inventory)
    # Validate and save a reviewable plan before any media deletion.
    write_audit(root, audit, plan)
    if args.apply:
        try:
            apply_plan(root, plan)
        except (OSError, ValueError):
            plan["status"] = "apply_failed"
            plan["reason"] = "changed_or_unsafe_local_files"
            write_audit(root, audit, plan)
            raise SystemExit("Retention stopped; inspect the local audit.") from None
        write_audit(root, audit, plan)
    print("NEWS_MEDIA_RETENTION", plan["status"], "planned_files", len(plan["delete"]),
          "reclaimed_bytes", plan["reclaimed_bytes"])


if __name__ == "__main__":
    main()
