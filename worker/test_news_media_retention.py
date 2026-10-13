"""Offline retention checks. Only synthetic files in a disposable workspace fixture."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import news_media_retention as retention


class MediaRetentionTests(unittest.TestCase):
    def setUp(self):
        workspace = Path(__file__).resolve().parents[1]
        fixture_parent = workspace / "work"
        fixture_parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="retention-test-", dir=fixture_parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = datetime(2026, 10, 14, 1, 0, tzinfo=timezone.utc)  # Oct 13, 22h Fortaleza.
        self.latest = "noticia-2026-10-13-noite"
        self.old = "noticia-2026-10-12-manha"
        self.new_video = self.media("work/new/render-output/daily-video.mp4", b"synthetic latest video")
        self.source("work/new", self.latest)
        self.confirm, self.upload = self.receipts(self.latest, self.new_video, "Latest12345")
        self.old_video = self.media("work/old/render-output/daily-video.mp4", b"synthetic old video")
        self.old_audio = self.media("work/old/public/generated-audio/scene.wav", b"synthetic old voice")
        self.source("work/old", self.old)
        self.receipts(self.old, self.old_video, "Oldvideo123")

    def json(self, local, content):
        path = self.root / local
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content), encoding="utf-8")
        return path

    def media(self, local, content):
        path = self.root / local
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def source(self, scope, owner):
        return self.json(scope + "/video/generated/daily-project.json", {"project_id": owner})

    def receipts(self, owner, video, video_id):
        folder = "production/" + owner
        checked = self.now if owner == self.latest else self.now - timedelta(days=1)
        confirmation = self.json(folder + "/publication-confirmation.json", {
            "episode_id": owner, "video_id": video_id, "public_confirmed": True,
            "privacy_observed": "public", "stage": "public_confirmed", "checked_at_utc": checked.isoformat()})
        upload = self.json(folder + "/youtube-upload-receipt.json", {
            "project_id": owner, "video_id": video_id, "video_sha256": retention.digest(video)})
        return confirmation, upload

    def plan(self, **kwargs):
        return retention.make_plan(self.root, self.confirm, self.upload, now=self.now, tracked=set(), **kwargs)

    def alter_confirmation(self, **changes):
        data = json.loads(self.confirm.read_text())
        data.update(changes)
        self.confirm.write_text(json.dumps(data), encoding="utf-8")

    def test_default_is_reviewable_plan_without_deletion(self):
        plan = self.plan()
        self.assertEqual(plan["status"], "planned")
        self.assertEqual({item["path"] for item in plan["delete"]}, {
            "work/old/render-output/daily-video.mp4", "work/old/public/generated-audio/scene.wav"})
        self.assertTrue(self.old_video.exists())
        self.assertTrue(self.new_video.exists())
        self.assertTrue(plan["latest_mp4_local"])

    def test_missing_receipt_skips_without_scan_or_git(self):
        self.confirm.unlink()
        with patch.object(retention, "scan") as scan, patch.object(retention, "tracked_files") as git:
            plan = self.plan()
        self.assertEqual(plan["status"], "skipped")
        self.assertEqual(plan["delete"], [])
        scan.assert_not_called()
        git.assert_not_called()

    def test_wrong_slot_date_video_channel_and_private_status_skip(self):
        original = self.confirm.read_text()
        for change in ({"episode_id": "noticia-2026-10-13-manha"}, {"video_id": "Other123456"},
                       {"channel_id": "another-channel"}, {"privacy_observed": "private"},
                       {"public_confirmed": "true"}, {"stage": "not_public"}, {"news_date": "2026-10-12"}):
            with self.subTest(change=change):
                self.confirm.write_text(original, encoding="utf-8")
                self.alter_confirmation(**change)
                self.assertEqual(self.plan()["status"], "skipped")

    def test_stale_future_or_naive_confirmation_skips(self):
        for value in ((self.now - timedelta(minutes=61)).isoformat(),
                      (self.now + timedelta(seconds=1)).isoformat(), "2026-10-14T01:00:00"):
            self.alter_confirmation(checked_at_utc=value)
            self.assertEqual(self.plan()["status"], "skipped")

    def test_latest_hash_duplicate_and_latest_project_audio_preserved(self):
        duplicate = self.media("work/old/copy.mp4", self.new_video.read_bytes())
        voice = self.media("work/new/voice.pcm", b"latest voice")
        plan = self.plan()
        preserved = {item["path"]: item["reason"] for item in plan["preserve"]}
        self.assertEqual(preserved[duplicate.relative_to(self.root).as_posix()], "latest_publication")
        self.assertEqual(preserved[voice.relative_to(self.root).as_posix()], "latest_publication")
        retention.apply_plan(self.root, plan, tracked=set(), now=self.now)
        self.assertTrue(self.new_video.exists())
        self.assertTrue(duplicate.exists())
        self.assertTrue(voice.exists())

    def test_pending_project_preserved_even_with_older_public_receipt(self):
        self.json("work/production-state.json", {"project_id": self.old, "stage": "dispatch-requested"})
        plan = self.plan()
        self.assertEqual(plan["delete"], [])
        self.assertIn(self.old, plan["pending_project_ids"])

    def test_unconfirmed_owned_and_unknown_media_preserved(self):
        self.source("run_artifacts/pending", "noticia-2026-10-13-meio-dia")
        self.media("run_artifacts/pending/voice.wav", b"pending")
        self.media("render-output/unowned.mp4", b"unknown")
        plan = self.plan()
        reasons = {item["reason"] for item in plan["preserve"]}
        self.assertIn("pending_or_unconfirmed_production", reasons)
        self.assertIn("unknown_or_conflicting_owner", reasons)

    def test_code_metadata_zip_dependencies_and_tracked_media_survive(self):
        code = self.media("work/old/script.py", b"print('preserve')")
        archive = self.media("work/old/archive.zip", b"archive may contain code")
        dependency = self.media("work/capture-deps/fixture.wav", b"dependency")
        metadata = self.root / "work/old/video/generated/daily-project.json"
        plan = retention.make_plan(self.root, self.confirm, self.upload, now=self.now,
                                   tracked={"work/old/render-output/daily-video.mp4"})
        retention.apply_plan(self.root, plan, tracked={"work/old/render-output/daily-video.mp4"}, now=self.now)
        for path in (code, archive, dependency, metadata, self.old_video):
            self.assertTrue(path.exists())

    def test_completed_owner_without_matching_mp4_preserves_audio(self):
        self.old_video.write_bytes(b"different unuploaded revision")
        self.assertEqual(self.plan()["delete"], [])

    def test_conflicting_source_owners_preserved(self):
        self.json("work/old/video/data/daily.json", {"project_id": "noticia-2026-10-13-meio-dia"})
        self.assertEqual(self.plan()["delete"], [])

    def test_keep_video_requires_latest_sha_and_allowed_path(self):
        plan = self.plan(keep_video=self.new_video, keep_sha256=retention.digest(self.new_video))
        self.assertEqual(plan["status"], "planned")
        for kwargs in ({"keep_video": self.old_video, "keep_sha256": retention.digest(self.old_video)},
                       {"keep_video": self.new_video, "keep_sha256": "0" * 64}):
            with self.assertRaises(ValueError):
                self.plan(**kwargs)

    def test_traversal_and_outside_media_refused(self):
        for path in ("work/../production/a.mp4", self.root.parent / "outside.mp4", "worker/code.mp4"):
            with self.subTest(path=path), self.assertRaises(retention.UnsafePath):
                retention.safe_path(self.root, path, media=True)

    def test_link_or_junction_preflight_refuses_before_any_deletion(self):
        # Windows symlink creation can require privileges; reparse detection is also tested offline.
        plan = self.plan()
        real_lstat = Path.lstat
        candidate = self.old_audio
        def fake_lstat(path):
            value = real_lstat(path)
            if path == candidate:
                return type("ReparseStat", (), {"st_mode": value.st_mode, "st_file_attributes": 0x400})()
            return value
        with patch.object(Path, "lstat", fake_lstat), self.assertRaises(retention.UnsafePath):
            retention.apply_plan(self.root, plan, tracked=set(), now=self.now)
        self.assertTrue(self.old_video.exists())
        self.assertTrue(self.old_audio.exists())

    def test_modified_media_or_ownership_aborts_entire_apply(self):
        for altered in (self.old_audio, self.root / "work/old/video/generated/daily-project.json"):
            original = altered.read_bytes()
            plan = self.plan()
            altered.write_bytes(b"modified fixture")
            with self.assertRaises(ValueError):
                retention.apply_plan(self.root, plan, tracked=set(), now=self.now)
            self.assertTrue(self.old_video.exists())
            altered.write_bytes(original)

    def test_expired_confirmation_rechecked_before_apply(self):
        self.alter_confirmation(checked_at_utc=(self.now - timedelta(minutes=59)).isoformat())
        plan = self.plan()
        with self.assertRaises(ValueError):
            retention.apply_plan(self.root, plan, tracked=set(), now=self.now + timedelta(minutes=2))
        self.assertTrue(self.old_video.exists())

    def test_apply_fixture_only_keeps_audit_hashes_and_is_idempotent(self):
        plan = self.plan()
        expected = sum(item["bytes"] for item in plan["delete"])
        retention.apply_plan(self.root, plan, tracked=set(), now=self.now)
        retention.write_audit(self.root, "work/media-retention/test-audit.json", plan)
        self.assertEqual(plan["reclaimed_bytes"], expected)
        self.assertEqual(len(plan["removed"]), 2)
        self.assertTrue(all(len(item["sha256"]) == 64 for item in plan["removed"]))
        self.assertFalse(self.old_video.exists())
        self.assertFalse(self.old_audio.exists())
        self.assertTrue(self.confirm.exists())
        self.assertTrue(self.new_video.exists())
        self.assertEqual(self.plan()["delete"], [])

    def test_audit_cannot_overwrite_code_or_receipt(self):
        plan = self.plan()
        for path in ("worker/overwritten.json", "production/receipt.json", "work/../evil.json"):
            with self.assertRaises(retention.UnsafePath):
                retention.write_audit(self.root, path, plan)

    def inventory(self, paths, approved=True):
        return self.json("work/media-retention/reviewed-inventory.json", {
            "approved": approved, "purpose": "past_production_media", "files": [
                {"path": str(path), "sha256": retention.digest(path), "bytes": path.stat().st_size}
                for path in paths]})

    def test_inventory_draft_is_unapproved_and_does_not_mutate_media(self):
        inventory = retention.inventory_candidates(self.root, tracked=set())
        self.assertFalse(inventory["approved"])
        self.assertTrue(all(Path(item["path"]).is_absolute() for item in inventory["files"]))
        self.assertTrue(self.old_video.exists())

    def test_reviewed_inventory_allows_evergreen_and_unknown_derived_media(self):
        evergreen = self.media("run_artifacts/evergreen/video.mp4", b"old evergreen")
        self.source("run_artifacts/evergreen", "historical-evergreen-2026-10-01")
        unknown = self.media("render-output/past-review.wav", b"old explicitly reviewed recording")
        archive = self.media("work/old/video-review.zip", b"explicitly reviewed production archive")
        inventory = self.inventory([evergreen, unknown, archive])
        plan = self.plan(inventory=inventory, pending_projects=["noticia-2026-10-13-meio-dia"])
        retention.apply_plan(self.root, plan, tracked=set(), now=self.now)
        for path in (evergreen, unknown, archive):
            self.assertFalse(path.exists())
        self.assertTrue(inventory.exists())
        self.assertTrue(self.new_video.exists())

    def test_inventory_never_overrides_latest_or_pending_project(self):
        pending = self.media("work/pending/voice.wav", b"pending voice")
        self.source("work/pending", "noticia-2026-10-13-meio-dia")
        inventory = self.inventory([pending, self.new_video])
        plan = self.plan(inventory=inventory, pending_projects=["noticia-2026-10-13-meio-dia"])
        deleted = {item["path"] for item in plan["delete"]}
        self.assertNotIn(pending.relative_to(self.root).as_posix(), deleted)
        self.assertNotIn(self.new_video.relative_to(self.root).as_posix(), deleted)

    def test_inventory_rejects_unapproved_changed_tracked_dependency_or_code(self):
        for kind in ("unapproved", "changed", "tracked", "dependency", "code"):
            with self.subTest(kind=kind):
                path = self.media("work/reviewed/" + kind + ".mp4", b"fixture")
                if kind == "dependency":
                    path = self.media("work/capture-deps/asset.mp4", b"dependency")
                elif kind == "code":
                    path = self.media("work/reviewed/source.py", b"code")
                inventory = self.inventory([path], approved=kind != "unapproved")
                if kind == "changed":
                    path.write_bytes(b"changed")
                tracked = {path.relative_to(self.root).as_posix()} if kind == "tracked" else set()
                with self.assertRaises(ValueError):
                    retention.make_plan(self.root, self.confirm, self.upload, now=self.now, tracked=tracked, inventory=inventory)

    def test_inventory_change_aborts_before_deleting_any_media(self):
        unknown = self.media("render-output/old-audio.wav", b"old voice")
        inventory = self.inventory([unknown])
        plan = self.plan(inventory=inventory)
        inventory.write_text("{}", encoding="utf-8")
        with self.assertRaises(ValueError):
            retention.apply_plan(self.root, plan, tracked=set(), now=self.now)
        self.assertTrue(self.old_video.exists())
        self.assertTrue(unknown.exists())

    def test_new_pending_source_after_plan_aborts_before_deleting(self):
        plan = self.plan()
        self.source("work/old/new-active-run", "noticia-2026-10-13-meio-dia")
        with self.assertRaises(ValueError):
            retention.apply_plan(self.root, plan, tracked=set(), now=self.now)
        self.assertTrue(self.old_video.exists())

    def test_old_closed_runtime_state_not_forever_pending_with_reviewed_inventory(self):
        self.json("work/production-state.json", {"project_id": self.old, "stage": "dispatch-requested",
                  "updated_at": (self.now - timedelta(days=3)).isoformat()})
        inventory = self.inventory([self.old_video, self.old_audio])
        plan = self.plan(inventory=inventory)
        self.assertEqual(len(plan["delete"]), 2)

    def test_recent_runtime_protects_inventory_without_explicit_pending_ids(self):
        self.json("work/production-state.json", {"project_id": self.old, "stage": "rendering",
                  "updated_at": (self.now - timedelta(minutes=3)).isoformat()})
        inventory = self.inventory([self.old_video, self.old_audio])
        self.assertEqual(self.plan(inventory=inventory)["delete"], [])

    def test_conflicting_latest_owner_preserved_even_with_reviewed_inventory(self):
        voice = self.media("work/new/raw.wav", b"latest narration")
        self.json("work/new/video/data/daily.json", {"project_id": self.old})
        inventory = self.inventory([voice])
        plan = self.plan(inventory=inventory)
        self.assertNotIn("work/new/raw.wav", {item["path"] for item in plan["delete"]})

    def test_evergreen_registry_outside_media_allowlist_is_preserved_and_ignored(self):
        self.json("work/temporary-ownership.json", {"entries": [{
            "path": "video/generated/daily-review.json", "project_id": self.old,
            "source_project_sha256": "a" * 64}]})
        self.json("video/generated/daily-review.json", {"status": "preserved"})
        self.assertEqual(len(self.plan()["delete"]), 2)
        self.assertTrue((self.root / "video/generated/daily-review.json").exists())


if __name__ == "__main__":
    unittest.main()
