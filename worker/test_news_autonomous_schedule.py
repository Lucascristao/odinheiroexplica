"""Regression tests: publishing a single news episode without custom cover."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
import news_autonomous_schedule as scheduler


class YouTubeReply:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class FakeVideos:
    def __init__(self, episode_id):
        self.episode_id = episode_id
        self.status = {"privacyStatus": "private"}
        self.updated = False

    def list(self, **kwargs):
        return YouTubeReply({"items": [{
            "snippet": {
                "channelId": scheduler.EXPECTED_ID,
                "tags": ["ODE_EPISODE_" + self.episode_id],
            },
            "status": dict(self.status),
        }]})

    def update(self, *, part, body):
        if part != "status" or body["status"]["privacyStatus"] not in ("private", "public"):
            raise AssertionError("not a private scheduled video")
        self.status.update(body["status"])
        self.updated = True
        return YouTubeReply({})


class FakeService:
    def __init__(self, episode_id):
        self.impl = FakeVideos(episode_id)

    def videos(self):
        return self.impl


class TestScheduleWithoutCover(unittest.TestCase):
    def test_youtube_tag_eventually_consistent_after_upload(self):
        class LaterTags(FakeVideos):
            def __init__(self, episode_id):
                super().__init__(episode_id)
                self.reads = 0

            def list(self, **kwargs):
                self.reads += 1
                data = super().list(**kwargs).execute()
                if self.reads < 3:
                    data["items"][0]["snippet"].pop("tags")
                return YouTubeReply(data)

        episode_id = "noticia-2026-10-09-manha"
        service = FakeService(episode_id)
        service.impl = LaterTags(episode_id)
        with patch.object(scheduler.time, "sleep") as sleep:
            video = scheduler.confirmed_video_identity(service, "abcdefghijk", episode_id)
        self.assertEqual(video["snippet"]["tags"], ["ODE_EPISODE_" + episode_id])
        self.assertEqual(service.impl.reads, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertFalse(service.impl.updated)

    def test_absent_youtube_tag_never_allows_publication(self):
        episode_id = "noticia-2026-10-09-manha"
        service = FakeService(episode_id)
        class Untagged(FakeVideos):
            def list(self, **kwargs):
                data = super().list(**kwargs).execute()
                data["items"][0]["snippet"]["tags"] = ["unrelated"]
                return YouTubeReply(data)

        service.impl = Untagged(episode_id)
        with patch.object(scheduler.time, "sleep"):
            with self.assertRaisesRegex(SystemExit, "preservar privado"):
                scheduler.confirmed_video_identity(service, "abcdefghijk", episode_id, attempts=3)
        self.assertFalse(service.impl.updated)

    def test_publish_at_without_cover(self):
        tomorrow = datetime.now(ZoneInfo("America/Fortaleza")).date() + timedelta(days=1)
        day = tomorrow.isoformat()
        project_id = "noticia-" + day + "-manha"
        with tempfile.TemporaryDirectory() as root:
            paths = {}
            payloads = {
                "project": {"project_id": project_id},
                "episode": {"episode_id": project_id, "news_date": day,
                            "editorial_status": "autonomous_fact_checked",
                            "publication_target_local": day + "T08:00:00-03:00"},
                "qa": {"status": "pass", "failures": [], "warnings": []},
                "config": {"version": "1.0", "enabled": True,
                           "required_editorial_status": "autonomous_fact_checked",
                           "require_qa_status": "pass",
                           "timezone": "America/Fortaleza",
                           "publication_hours": ["08:00", "12:00", "20:00"],
                           "min_lead_minutes": 5,
                           "require_thumbnail_audit": False,
                           "require_thumbnail_receipt": False},
                "private-receipt": {"project_id": project_id,
                                    "video_id": "abcdefghijk",
                                    "destination": "youtube",
                                    "privacy_requested": "private"},
            }
            for name, value in payloads.items():
                target = Path(root) / (name + ".json")
                target.write_text(json.dumps(value), encoding="utf-8")
                paths[name] = str(target)
            output = str(Path(root) / "scheduled.json")
            argv = ["schedule", "--root", root]
            for name, value in paths.items():
                argv.extend(["--" + name, value])
            argv.extend(["--output", output])
            service = FakeService(project_id)
            with patch.object(sys, "argv", argv), \
                 patch.object(scheduler, "youtube_service", return_value=service), \
                 patch.object(scheduler, "assert_channel", return_value=True):
                scheduler.main()
            result = json.loads(Path(output).read_text(encoding="utf-8"))
            self.assertTrue(service.impl.updated)
            self.assertEqual(result["thumbnail_status"], "youtube_automatic")
            self.assertIsNone(result["thumbnail_sha256"])
            self.assertEqual(result["status"], "scheduled_private_until_publish_at")
            self.assertEqual(service.impl.status["privacyStatus"], "private")
            self.assertTrue(service.impl.status.get("publishAt", "").endswith("Z"))


    def test_approved_late_morning_recovery_publishes_public_only_with_real_gates(self):
        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)

        project_id = "noticia-2026-10-09-manha"
        with tempfile.TemporaryDirectory() as root:
            paths = {}
            payloads = {
                "project": {"project_id": project_id},
                "episode": {"episode_id": project_id, "news_date": "2026-10-09",
                            "editorial_status": "autonomous_fact_checked",
                            "publication_target_local": "2026-10-09T08:00:00-03:00"},
                "qa": {"status": "pass", "failures": [], "warnings": []},
                "config": {"version": "1.0", "enabled": True,
                           "required_editorial_status": "autonomous_fact_checked",
                           "require_qa_status": "pass", "timezone": "America/Fortaleza",
                           "publication_hours": ["08:00", "12:00", "20:00"],
                           "min_lead_minutes": 5,
                           "one_time_late_recovery": {
                               "episode_id": project_id,
                               "original_publication_local": "2026-10-09T08:00:00-03:00",
                               "authorized_by_user": True,
                               "mode": "publish_immediately_after_qa"}},
                "private-receipt": {"project_id": project_id,
                                    "video_id": "abcdefghijk",
                                    "destination": "youtube",
                                    "privacy_requested": "private"},
            }
            args = ["schedule", "--root", root]
            for name, payload in payloads.items():
                filename = Path(root) / (name + ".json")
                filename.write_text(json.dumps(payload), encoding="utf-8")
                args.extend(["--" + name, str(filename)])
            output = Path(root) / "late-result.json"
            args.extend(["--output", str(output)])
            service = FakeService(project_id)
            with patch.object(sys, "argv", args), \
                 patch.object(scheduler, "datetime", FixedDateTime), \
                 patch.object(scheduler, "youtube_service", return_value=service), \
                 patch.object(scheduler, "assert_channel", return_value=True):
                scheduler.main()
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(service.impl.updated)
            self.assertEqual(service.impl.status["privacyStatus"], "public")
            self.assertEqual(result["status"], "published_late_authorized")
            self.assertEqual(result["publication_confirmation"], "confirmed_public")
            self.assertEqual(result["thumbnail_status"], "youtube_automatic")

    def test_late_tolerance_warnings_and_critical_failures(self):
        day = "2026-10-10"
        project_id = "noticia-" + day + "-meio-dia"
        cases = [
            ("within", 15, 45, "warn", [], "published_within_tolerance"),
            ("boundary", 16, 30, "warn", [], "published_within_tolerance"),
            ("outside", 16, 31, "warn", [], "blocked"),
            ("critical", 15, 45, "fail", [{"code": "missing-video"}], "blocked"),
            ("almost_due", 14, 58, "warn", [], "scheduled_private_until_publish_at"),
        ]

        for label, hour, minute, qa_status, failures, expected in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as root:
                payloads = {
                    "project": {"project_id": project_id},
                    "episode": {"episode_id": project_id, "news_date": day,
                                "editorial_status": "autonomous_fact_checked",
                                "publication_target_local": day + "T12:00:00-03:00"},
                    "qa": {"status": qa_status, "failures": failures,
                           "warnings": [{"code": "estimated-visual-anchors", "message": "Revisar no próximo ciclo."}]},
                    "config": {"version": "1.0", "enabled": True,
                               "required_editorial_status": "autonomous_fact_checked",
                               "require_qa_status": "pass",
                               "allow_qa_warnings": True,
                               "publish_if_late": True,
                               "late_tolerance_minutes": 90,
                               "timezone": "America/Fortaleza",
                               "publication_hours": ["08:00", "12:00", "20:00"],
                               "min_lead_minutes": 5},
                    "private-receipt": {"project_id": project_id,
                                        "video_id": "abcdefghijk", "destination": "youtube",
                                        "privacy_requested": "private"},
                }
                args = ["schedule", "--root", root]
                for name, payload in payloads.items():
                    target = Path(root) / (name + ".json")
                    target.write_text(json.dumps(payload), encoding="utf-8")
                    args += ["--" + name, str(target)]
                output = Path(root) / "result.json"
                args += ["--output", str(output)]

                class FixedNow(datetime):
                    @classmethod
                    def now(cls, tz=None):
                        return datetime(2026, 10, 10, hour, minute, tzinfo=timezone.utc)

                service = FakeService(project_id)
                with patch.object(sys, "argv", args), \
                     patch.object(scheduler, "datetime", FixedNow), \
                     patch.object(scheduler, "youtube_service", return_value=service), \
                     patch.object(scheduler, "assert_channel", return_value=True):
                    if expected == "blocked":
                        with self.assertRaisesRegex(SystemExit, "Janela de tolerância|QA técnico"):
                            scheduler.main()
                        self.assertFalse(service.impl.updated)
                    else:
                        scheduler.main()
                        result = json.loads(output.read_text(encoding="utf-8"))
                        self.assertEqual(result["status"], expected)
                        self.assertEqual(result["qa_warning_count"], 1)
                        self.assertTrue(service.impl.updated)
                        self.assertEqual(service.impl.status["privacyStatus"],
                                         "private" if expected.startswith("scheduled") else "public")
                        if label == "boundary":
                            self.assertEqual(result["delay_minutes"], 90)

    def test_reject_missing_thumbnail_receipt(self):
        # A submitted cover still requires its own verified receipt.
        tomorrow = datetime.now(ZoneInfo("America/Fortaleza")).date() + timedelta(days=1)
        day = tomorrow.isoformat()
        with tempfile.TemporaryDirectory() as root:
            files = {
                "project": {"project_id": "noticia-" + day + "-manha"},
                "episode": {"episode_id": "noticia-" + day + "-manha",
                            "editorial_status": "autonomous_fact_checked"},
                "qa": {"status": "pass", "failures": [], "warnings": []},
                "config": {"version": "1.0", "enabled": True,
                           "required_editorial_status": "autonomous_fact_checked",
                           "require_qa_status": "pass"},
                "private-receipt": {},
            }
            args = ["schedule", "--root", root]
            for name, value in files.items():
                path = Path(root) / (name + ".json")
                path.write_text(json.dumps(value))
                args.extend(["--" + name, str(path)])
            args += ["--output", str(Path(root) / "out.json"),
                     "--thumbnail", str(Path(root) / "thumbnail.jpg")]
            with patch.object(sys, "argv", args):
                with self.assertRaises(SystemExit):
                    scheduler.main()


if __name__ == "__main__":
    unittest.main()
