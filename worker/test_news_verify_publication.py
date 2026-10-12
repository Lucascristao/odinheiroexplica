"""Offline regression tests for delayed monitoring and missing production stages."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent))
import news_verify_publication as monitor


class PublicationMonitorTests(unittest.TestCase):
    def test_delayed_night_run_keeps_previous_edition(self):
        self.assertEqual(monitor.edition_date("noite", run_created_at="2026-10-12T06:32:35Z"), "2026-10-11")

    def test_midnight_utc_is_previous_local_date(self):
        self.assertEqual(monitor.edition_date("noite", run_created_at="2026-10-12T00:46:00Z"), "2026-10-11")

    def test_queued_runner_uses_run_creation_not_current_time(self):
        self.assertEqual(monitor.edition_date("manha", run_created_at="2026-10-12T13:05:00Z"), "2026-10-12")

    def test_manual_date_overrides_schedule_inference(self):
        self.assertEqual(monitor.edition_date("noite", "2026-10-10", "2026-10-12T06:32:35Z"), "2026-10-10")

    def test_missing_timezone_is_rejected(self):
        with self.assertRaises(ValueError):
            monitor.edition_date("noite", run_created_at="2026-10-12T06:32:35")

    def test_manual_date_requires_canonical_format(self):
        with self.assertRaises(ValueError):
            monitor.edition_date("manha", explicit_date="20261012")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project_id = "noticia-2026-10-12-manha"
        self.marker = "ODE_EPISODE_" + self.project_id

    def episode(self, content=None):
        (self.root / "2026-10-12-manha.json").write_text(
            json.dumps(content or {"episode_id": self.project_id}), encoding="utf-8")

    def test_missing_episode_never_calls_authenticated_service(self):
        with patch.object(monitor, "youtube_service") as factory:
            result = monitor.check_publication("manha", "2026-10-12", self.root)
        self.assertEqual(result["stage"], "episode_missing")
        self.assertFalse(result["public_confirmed"])
        factory.assert_not_called()

    def test_invalid_episode_never_calls_authenticated_service(self):
        self.episode({"episode_id": "different"})
        with patch.object(monitor, "youtube_service") as factory:
            result = monitor.check_publication("manha", "2026-10-12", self.root)
        self.assertEqual(result["stage"], "episode_invalid")
        factory.assert_not_called()

    def check_video(self, *, privacy="public", video=None, returned_id="abc", channel_id="channel", tags=None, items=True):
        self.episode()
        service = Mock()
        item = {"id": returned_id, "snippet": {"channelId": channel_id,
                "tags": [self.marker] if tags is None else tags}, "status": {"privacyStatus": privacy}}
        service.videos.return_value.list.return_value.execute.return_value = {"items": [item] if items else []}
        with patch.object(monitor, "youtube_service", return_value=service), \
                patch.object(monitor, "assert_channel", return_value={"id": "channel"}), \
                patch.object(monitor, "lookup_existing", return_value={"id": "abc"} if video is None else video):
            result = monitor.check_publication("manha", "2026-10-12", self.root)
        service.videos.return_value.update.assert_not_called()
        service.videos.return_value.insert.assert_not_called()
        return result

    def test_upload_missing_differs_from_episode_missing(self):
        self.assertEqual(self.check_video(video={})["stage"], "upload_missing")

    def test_public_requires_observed_matching_video(self):
        result = self.check_video()
        self.assertTrue(result["public_confirmed"])
        self.assertEqual(result["stage"], "public_confirmed")

    def test_private_does_not_confirm_publication(self):
        result = self.check_video(privacy="private")
        self.assertFalse(result["public_confirmed"])
        self.assertEqual(result["stage"], "not_public")

    def test_other_channel_is_not_confirmed(self):
        self.assertEqual(self.check_video(channel_id="other")["stage"], "identity_mismatch")

    def test_other_episode_is_not_confirmed(self):
        self.assertEqual(self.check_video(tags=[])["stage"], "identity_mismatch")

    def test_other_video_id_is_not_confirmed(self):
        self.assertEqual(self.check_video(returned_id="different")["stage"], "identity_mismatch")

    def test_missing_status_is_reported(self):
        self.assertEqual(self.check_video(items=False)["stage"], "status_unavailable")

    def test_api_error_does_not_leak_exception_contents(self):
        self.episode()
        with patch.object(monitor, "youtube_service", side_effect=ValueError("fake-sensitive-value")):
            result = monitor.check_publication("manha", "2026-10-12", self.root)
        self.assertEqual(result["stage"], "api_error")
        self.assertNotIn("fake-sensitive-value", json.dumps(result))

    def test_cli_preserves_failure_artifact(self):
        report = self.root / "output.json"
        with patch.object(sys, "argv", ["monitor", "--slot", "manha", "--news-date", "2026-10-12",
                "--episodes-dir", str(self.root), "--output", str(report)]), self.assertRaises(SystemExit):
            monitor.main()
        self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["stage"], "episode_missing")

    def test_cli_preserves_invalid_window_report(self):
        report = self.root / "output.json"
        with patch.object(sys, "argv", ["monitor", "--slot", "manha", "--news-date", "invalid",
                "--output", str(report)]), self.assertRaises(SystemExit):
            monitor.main()
        self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["stage"], "window_unresolved")


if __name__ == "__main__":
    unittest.main()
