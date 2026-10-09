"""Offline safety checks for public news release. No YouTube requests."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from youtube_publication import EXPECTED_ID, publish_after_review

VID = "zzzzzzzzzzz"
EP = "noticias-2026-10-08-noite"


class TestReleaseGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.image = Path(self.tmp.name, "thumb.jpg")
        self.image.write_bytes(b"reviewed-image-fixture")
        from youtube_publication import sha256
        self.digest = sha256(self.image)
        self.receipt = {"video_id": VID, "thumbnail_sha256": self.digest}
        self.approval = {
            "project_id": EP, "video_id": VID, "thumbnail_sha256": self.digest,
            "status": "approved_for_publication", "full_video_watched": True,
            "reviewer": "Revisão editorial",
        }
        self.service = MagicMock()
        self.service.videos.return_value.list.return_value.execute.side_effect = [
            {"items": [{"id": VID, "snippet": {"channelId": EXPECTED_ID, "tags": ["ODE_EPISODE_" + EP]},
                        "status": {"privacyStatus": "private"}}]},
            {"items": [{"id": VID, "snippet": {"channelId": EXPECTED_ID},
                        "status": {"privacyStatus": "public"}}]},
        ]

    def tearDown(self):
        self.tmp.cleanup()

    def test_correct_final_release(self):
        with patch.dict("os.environ", {"ODE_PUBLISH_CONFIRM": "PUBLICAR_" + EP}):
            result = publish_after_review(self.service, EP, VID, self.image, self.receipt, self.approval)
        self.assertEqual(result["confirmed_privacy"], "public")
        self.service.videos.return_value.update.assert_called_once()

    def test_unreviewed_video_blocks_write(self):
        self.approval["full_video_watched"] = False
        with patch.dict("os.environ", {"ODE_PUBLISH_CONFIRM": "PUBLICAR_" + EP}):
            with self.assertRaises(ValueError):
                publish_after_review(self.service, EP, VID, self.image, self.receipt, self.approval)
        self.service.videos.return_value.update.assert_not_called()

    def test_missing_confirmation_blocks_write(self):
        with patch.dict("os.environ", {"ODE_PUBLISH_CONFIRM": "no"}):
            with self.assertRaisesRegex(ValueError, "confirmação"):
                publish_after_review(self.service, EP, VID, self.image, self.receipt, self.approval)
        self.service.videos.return_value.update.assert_not_called()

    def test_cover_receipt_changed_blocks_write(self):
        self.receipt["thumbnail_sha256"] = "0" * 64
        with patch.dict("os.environ", {"ODE_PUBLISH_CONFIRM": "PUBLICAR_" + EP}):
            with self.assertRaisesRegex(ValueError, "recibo"):
                publish_after_review(self.service, EP, VID, self.image, self.receipt, self.approval)
        self.service.videos.return_value.update.assert_not_called()

    def test_youtube_does_not_confirm_publication(self):
        self.service.videos.return_value.list.return_value.execute.side_effect = [
            {"items": [{"id": VID, "snippet": {"channelId": EXPECTED_ID, "tags": ["ODE_EPISODE_" + EP]},
                        "status": {"privacyStatus": "private"}}]},
            {"items": [{"id": VID, "snippet": {"channelId": EXPECTED_ID},
                        "status": {"privacyStatus": "private"}}]},
        ]
        with patch.dict("os.environ", {"ODE_PUBLISH_CONFIRM": "PUBLICAR_" + EP}):
            with self.assertRaisesRegex(RuntimeError, "não confirmou"):
                publish_after_review(self.service, EP, VID, self.image, self.receipt, self.approval)


if __name__ == "__main__":
    unittest.main()
