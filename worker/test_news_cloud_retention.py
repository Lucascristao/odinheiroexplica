"""Offline cloud retention tests; remote APIs and real deletes are never called."""
from copy import deepcopy
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch
import zipfile

shim = types.ModuleType("requests")
shim.request = Mock(side_effect=AssertionError("External HTTP prohibited in offline tests"))
shim.get = Mock(side_effect=AssertionError("External HTTP prohibited in offline tests"))
spec = importlib.util.spec_from_file_location("cloud_retention", Path(__file__).with_name("news_cloud_retention.py"))
cloud = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {"requests": shim}):
    spec.loader.exec_module(cloud)


class FakeGitHub:
    def __init__(self):
        self.items = [self.artifact(1, "news-single-youtube-private-receipt", 100),
                      self.artifact(2, "news-single-production-review", 100),
                      self.artifact(3, "daily-production-review", 101),
                      self.artifact(4, "news-single-production-review", 102),
                      self.artifact(5, "news-production-review", 103),
                      self.artifact(6, "ode-news-qa-feedback", 101),
                      self.artifact(7, "unknown-media-name", 101)]
        self.cache_items = [{"id": 20 + run, "key": f"news-live-{run}-1", "ref": "refs/heads/main",
                             "size_in_bytes": 300, "created_at": "2026-10-11T10:00:00Z"}
                            for run in (100, 101, 102, 103)]
        self.run_items = {run: {"id": run, "repository": {"full_name": cloud.REPO},
                          "path": ".github/workflows/render-news-single.yml", "status": "completed",
                          "conclusion": "failure" if run == 103 else "success", "updated_at": "2026-10-11T12:00:00Z"}
                          for run in (100, 101, 102, 103)}
        self.run_items[102]["status"] = "in_progress"
        self.active = []
        self.receipts = {1: {"project_id": "noticia-2026-10-12-meio-dia", "video_id": "Latest12345", "video_sha256": "a" * 64}}
        self.deleted = []

    @staticmethod
    def artifact(identifier, name, run):
        return {"id": identifier, "name": name, "workflow_run": {"id": run}, "size_in_bytes": 1000,
                "created_at": "2026-10-11T10:00:00Z", "expired": False}

    def artifacts(self):
        return deepcopy(self.items)

    def caches(self):
        return deepcopy(self.cache_items)

    def active_runs(self):
        return deepcopy(self.active)

    def run(self, identifier):
        return deepcopy(self.run_items[identifier])

    def receipt(self, artifact):
        value = self.receipts[artifact["id"]]
        if isinstance(value, Exception):
            raise value
        return deepcopy(value)

    def delete(self, target):
        self.deleted.append(deepcopy(target))  # Record only: no HTTP or filesystem deletion.


class CloudRetentionTests(unittest.TestCase):
    def setUp(self):
        self.github = FakeGitHub()
        self.now = datetime(2026, 10, 13, 23, 0, tzinfo=timezone.utc)
        self.channel = {"id": cloud.EXPECTED_ID, "snippet": {"title": cloud.EXPECTED_TITLE, "customUrl": cloud.EXPECTED_HANDLE},
                        "contentDetails": {"relatedPlaylists": {"uploads": "uploads-id"}}}
        self.video = {"id": "Latest12345", "snippet": {"channelId": cloud.EXPECTED_ID,
                      "tags": ["ODE_EPISODE_noticia-2026-10-12-meio-dia", "ODE_MEDIA_" + "a" * 16],
                      "publishedAt": "2026-10-12T15:00:00Z"}, "status": {"privacyStatus": "public"}}
        self.videos = {self.video["id"]: self.video}
        self.service = Mock()
        self.service.playlistItems.return_value.list.return_value.execute.side_effect = lambda: {
            "items": [{"contentDetails": {"videoId": identifier}} for identifier in self.videos]}
        self.service.videos.return_value.list.side_effect = lambda **args: Mock(execute=lambda: {
            "items": [deepcopy(self.videos[identifier]) for identifier in args["id"].split(",") if identifier in self.videos]})

    def plan(self, **options):
        return cloud.make_plan(self.github, self.service, self.channel, now=self.now, **options)

    def test_plan_keeps_latest_and_active_unknown_receipt_qa(self):
        report = self.plan()
        self.assertEqual(report["status"], "planned")
        self.assertEqual({(item["kind"], item["id"]) for item in report["delete"]}, {("artifact", 3), ("cache", 121)})
        self.assertEqual(self.github.deleted, [])
        self.assertNotIn(100, [item["run_id"] for item in report["delete"]])
        self.assertNotIn(102, [item["run_id"] for item in report["delete"]])

    def test_no_public_video_and_wrong_channel_block(self):
        self.video["status"]["privacyStatus"] = "private"
        with self.assertRaises(cloud.Guard):
            self.plan()
        self.video["status"]["privacyStatus"] = "public"
        self.channel["snippet"]["customUrl"] = "@wrong"
        with self.assertRaises(cloud.Guard):
            self.plan()

    def test_newest_public_without_ode_marker_blocks_older_marked_video(self):
        self.videos["Unmarked123"] = {"id": "Unmarked123", "snippet": {"channelId": cloud.EXPECTED_ID,
            "publishedAt": "2026-10-13T16:00:00Z", "tags": []}, "status": {"privacyStatus": "public"}}
        with self.assertRaisesRegex(cloud.Guard, "latest_unmanaged_public"):
            self.plan()
        self.assertEqual(self.github.deleted, [])

    def test_newest_public_ambiguous_marker_or_time_blocks_cleanup(self):
        self.video["snippet"]["tags"].append("ODE_EPISODE_another-project")
        with self.assertRaisesRegex(cloud.Guard, "latest_unmanaged_public"):
            self.plan()
        self.video["snippet"]["tags"].pop()
        other = deepcopy(self.video)
        other["id"] = "Another1234"
        self.videos[other["id"]] = other
        with self.assertRaisesRegex(cloud.Guard, "latest_public_timestamp_ambiguous"):
            self.plan()
        self.assertEqual(self.github.deleted, [])

    def test_receipt_mismatch_guards_all_media(self):
        for field, value in (("project_id", "another-project"), ("video_id", "Other123456"), ("video_sha256", "b" * 64)):
            with self.subTest(field=field):
                saved = self.github.receipts[1][field]
                self.github.receipts[1][field] = value
                report = self.plan()
                self.assertEqual(report["status"], "guarded")
                self.assertEqual(report["delete"], [])
                self.github.receipts[1][field] = saved

    def test_nightly_requires_exact_public_night_but_manual_any_slot(self):
        self.assertEqual(self.plan()["status"], "planned")
        report = self.plan(require_night_date="2026-10-13")
        self.assertEqual(report["reason"], "required_night_not_public")
        self.assertEqual(report["delete"], [])

    def test_unknown_failed_run_preserved_until_explicitly_closed(self):
        self.assertNotIn(103, {item["run_id"] for item in self.plan()["delete"]})
        self.assertIn(103, {item["run_id"] for item in self.plan(closed=[103])["delete"]})
        self.assertNotIn(103, {item["run_id"] for item in self.plan(closed=[103], protected=[103])["delete"]})

    def test_active_recovery_source_unknown_guards_whole_plan(self):
        self.github.active = [{"id": 900, "path": ".github/workflows/news-resume-publication.yml",
                               "repository": {"full_name": cloud.REPO}}]
        report = self.plan(closed=[103])
        self.assertEqual(report["reason"], "active_recovery_source_unresolved")
        self.assertEqual(report["delete"], [])

    def test_active_editor_protects_all_voice_caches(self):
        self.github.active = [{"id": 900, "path": cloud.EDITOR, "repository": {"full_name": cloud.REPO}}]
        report = self.plan(closed=[103])
        self.assertFalse(any(item["kind"] == "cache" for item in report["delete"]))

    def test_older_private_or_unreadable_receipt_remains_resumable(self):
        self.github.items.append(self.github.artifact(10, "news-youtube-private-receipt", 101))
        self.github.receipts[10] = {"project_id": "old-private-project", "video_id": "Private1234", "video_sha256": "c" * 64}
        self.videos["Private1234"] = {"id": "Private1234", "snippet": {"channelId": cloud.EXPECTED_ID},
                                     "status": {"privacyStatus": "private"}}
        self.assertNotIn(101, {item["run_id"] for item in self.plan()["delete"]})
        self.github.receipts[10] = cloud.Guard("receipt_download_failed")
        self.assertNotIn(101, {item["run_id"] for item in self.plan()["delete"]})

    def test_foreign_repository_run_and_video_block(self):
        self.github.run_items[101]["repository"]["full_name"] = "someone/other-repo"
        with self.assertRaises(cloud.Guard):
            self.plan()
        self.github.run_items[101]["repository"]["full_name"] = cloud.REPO
        self.video["snippet"]["channelId"] = "other-channel"
        with self.assertRaises(cloud.Guard):
            self.plan()

    def test_apply_rechecks_identity_and_run_state_before_any_delete(self):
        report = self.plan()
        self.github.run_items[101]["status"] = "in_progress"
        with self.assertRaises(cloud.Guard):
            cloud.apply_plan(self.github, self.service, self.channel, report)
        self.assertEqual(self.github.deleted, [])

    def test_apply_rechecks_artifact_metadata_before_any_delete(self):
        report = self.plan()
        self.github.items[2]["size_in_bytes"] += 1
        with self.assertRaises(cloud.Guard):
            cloud.apply_plan(self.github, self.service, self.channel, report)
        self.assertEqual(self.github.deleted, [])

    def test_offline_apply_records_only_github_deletes_never_youtube_writes(self):
        report = self.plan()
        cloud.apply_plan(self.github, self.service, self.channel, report)
        self.assertEqual(len(self.github.deleted), 2)
        self.service.videos.return_value.delete.assert_not_called()
        self.service.videos.return_value.update.assert_not_called()
        self.service.videos.return_value.insert.assert_not_called()
        self.assertTrue(all(item["name"] in cloud.MEDIA_NAMES or cloud.CACHE_KEY.fullmatch(item["name"])
                            for item in self.github.deleted))

    def dependency_caches(self):
        for identifier, created, accessed in ((300, "2026-10-10", "2026-10-10"), (301, "2026-10-11", "2026-10-13"),
                                             (302, "2026-10-12", "2026-10-12")):
            self.github.cache_items.append({"id": identifier, "key": f"setup-python-Linux-x64-3.11.15-pip-hash{identifier}",
                  "ref": "refs/heads/main", "size_in_bytes": 340000000,
                  "created_at": created + "T10:00:00Z", "last_accessed_at": accessed + "T10:00:00Z"})

    def test_stale_dependency_family_keeps_latest_created_and_accessed(self):
        self.dependency_caches()
        self.assertNotIn(300, {item["id"] for item in self.plan()["delete"]})
        report = self.plan(prune_stale_dependencies=True)
        deleted = {item["id"] for item in report["delete"]}
        self.assertIn(300, deleted)
        self.assertNotIn(301, deleted)
        self.assertNotIn(302, deleted)
        self.assertNotIn(300, {item["id"] for item in self.plan(prune_stale_dependencies=True, protected_caches=[300])["delete"]})

    def test_any_active_run_keeps_dependency_caches(self):
        self.dependency_caches()
        self.github.active = [{"id": 999, "path": ".github/workflows/ci.yml", "repository": {"full_name": cloud.REPO}}]
        self.assertNotIn(300, {item["id"] for item in self.plan(prune_stale_dependencies=True)["delete"]})

    def test_actual_ubuntu_setup_python_key_family_is_pruned(self):
        self.dependency_caches()
        for cache in self.github.cache_items:
            if cache["id"] in (300, 301, 302):
                cache["key"] = "setup-python-Linux-x64-24.04-Ubuntu-python-3.11.17-pip-033c" + str(cache["id"])
        deleted = {item["id"] for item in self.plan(prune_stale_dependencies=True)["delete"]}
        self.assertIn(300, deleted)
        self.assertNotIn(301, deleted)
        self.assertNotIn(302, deleted)
        self.assertEqual(cloud.dependency_family("setup-python-Linux-x64-3.11.15-pip-legacy"), "setup-python-3.11")

    def test_own_validated_retention_run_does_not_block_dependency_pruning(self):
        self.dependency_caches()
        self.github.active = [{"id": 900, "path": ".github/workflows/news-cloud-retention.yml",
                               "repository": {"full_name": cloud.REPO}}]
        with patch.dict(cloud.os.environ, {"GITHUB_RUN_ID": "900"}):
            self.assertIn(300, {item["id"] for item in self.plan(prune_stale_dependencies=True)["delete"]})
            self.github.active.append({"id": 901, "path": ".github/workflows/ci.yml", "repository": {"full_name": cloud.REPO}})
            self.assertNotIn(300, {item["id"] for item in self.plan(prune_stale_dependencies=True)["delete"]})

    def test_invalid_or_foreign_own_run_is_never_excluded(self):
        self.dependency_caches()
        self.github.active = [{"id": 900, "path": ".github/workflows/ci.yml", "repository": {"full_name": cloud.REPO}}]
        with patch.dict(cloud.os.environ, {"GITHUB_RUN_ID": "not-an-id"}):
            self.assertNotIn(300, {item["id"] for item in self.plan(prune_stale_dependencies=True)["delete"]})
        with patch.dict(cloud.os.environ, {"GITHUB_RUN_ID": "900"}), self.assertRaises(cloud.Guard):
            self.plan(prune_stale_dependencies=True)

    def test_compact_receipt_zip_read_without_extraction_and_rejects_large_or_ambiguous(self):
        def archive(contents):
            result = io.BytesIO()
            with zipfile.ZipFile(result, "w") as output:
                for name, value in contents:
                    output.writestr(name, value)
            return result.getvalue()
        valid = json.dumps(self.github.receipts[1])
        self.assertEqual(cloud.parse_receipt(archive([("daily-youtube-private.json", valid)])), self.github.receipts[1])
        for contents in ([('daily-youtube-private.json', valid), ('render-output/daily-youtube-private.json', valid)],
                         [('daily-youtube-private.json', " " * 131073)], [('daily-video.mp4', " " * 2100000)]):
            with self.assertRaises(cloud.Guard):
                cloud.parse_receipt(archive(contents))


if __name__ == "__main__":
    unittest.main()
