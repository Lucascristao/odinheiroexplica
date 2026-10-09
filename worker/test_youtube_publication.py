"""Offline tests: channel isolation, private-only uploads, duplicate guard and thumbnail checks."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from youtube_publication import (
    EXPECTED_ID, EXPECTED_HANDLE, EXPECTED_TITLE,
    assert_channel, validate_package, load_receipt, upload_private, add_thumbnail,
)

CHANNEL = {"id": EXPECTED_ID, "snippet": {"title": EXPECTED_TITLE, "customUrl": EXPECTED_HANDLE},
           "contentDetails": {"relatedPlaylists": {"uploads": "UUxxxxxxxxxx"}}}


class YouTubePublicationTest(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.video = Path(self.work.name, "video.mp4")
        self.video.write_bytes(b"safe synthetic fixture, not a real video")
        self.receipt = Path(self.work.name, "receipt.json")
        self.metadata = {"title": "Notícia explicada", "description": "Texto de teste.", "tags": ["noticia"]}
        self.service = MagicMock()
        self.service.channels.return_value.list.return_value.execute.return_value = {"items": [CHANNEL]}

    def tearDown(self):
        self.work.cleanup()

    def test_only_expected_brand_channel_allowed(self):
        assert_channel(self.service)
        self.service.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "OTHER", "snippet": {"title": "Lucas Freitas", "customUrl": "@lucas"}}]
        }
        with self.assertRaisesRegex(ValueError, "outro canal"):
            assert_channel(self.service)

    def test_private_metadata_only(self):
        body = validate_package(self.video, self.metadata, "news-2026-10-09-am")
        self.assertEqual(body["status"], {"privacyStatus": "private"})
        self.assertIn("ODE_EPISODE_news-2026-10-09-am", body["snippet"]["tags"])
        revised = validate_package(self.video, self.metadata, "news-2026-10-09-am", "a" * 64)
        self.assertIn("ODE_SOURCE_" + "a" * 16, revised["snippet"]["tags"])


    def test_no_external_privacy_override(self):
        meta = {**self.metadata, "status": {"privacyStatus": "public"}}
        body = validate_package(self.video, meta, "news-2026-10-09-am")
        self.assertEqual(body["status"]["privacyStatus"], "private")

    def test_invalid_video_fails_before_network(self):
        with self.assertRaises(ValueError):
            validate_package(Path(self.work.name, "absent.mp4"), self.metadata, "news-2026-10-09-am")

    def test_existing_receipt_prevents_second_upload(self):
        from youtube_publication import save_receipt, sha256
        save_receipt(self.receipt, "news-2026-10-09-am", sha256(self.video), "zzzzzzzzzzz", False)
        result = upload_private(self.service, CHANNEL, self.video, self.metadata, "news-2026-10-09-am", self.receipt)
        self.assertEqual(result["video_id"], "zzzzzzzzzzz")
        self.service.videos.return_value.insert.assert_not_called()

    def test_edited_media_receipt_fails_closed(self):
        from youtube_publication import save_receipt, sha256
        save_receipt(self.receipt, "news-2026-10-09-am", sha256(self.video), "zzzzzzzzzzz", False)
        self.video.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "Recibo de outro"):
            upload_private(self.service, CHANNEL, self.video, self.metadata, "news-2026-10-09-am", self.receipt)

    def test_existing_upload_is_recovered_not_repeated(self):
        with patch("youtube_publication.lookup_existing", return_value={
            "id": "zzzzzzzzzzz",
            "status": {"privacyStatus": "private"},
            "snippet": {"channelId": EXPECTED_ID},
        }):
            result = upload_private(self.service, CHANNEL, self.video, self.metadata, "news-2026-10-09-am", self.receipt)
        self.assertTrue(result["recovered_existing_upload"])
        self.service.videos.return_value.insert.assert_not_called()

    def test_existing_public_upload_blocks_retry(self):
        with patch("youtube_publication.lookup_existing", return_value={
            "id": "zzzzzzzzzzz", "status": {"privacyStatus": "public"},
        }):
            with self.assertRaisesRegex(ValueError, "não está privado"):
                upload_private(self.service, CHANNEL, self.video, self.metadata, "news-2026-10-09-am", self.receipt)

    def test_thumbnail_rejects_video_on_other_channel(self):
        self.service.videos.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "zzzzzzzzzzz", "snippet": {"channelId": "WRONG"},
                       "status": {"privacyStatus": "private"}}]}
        cover = Path(self.work.name, "thumb.jpg")
        cover.write_bytes(b"not a production image")
        with self.assertRaisesRegex(ValueError, "não pertence"):
            add_thumbnail(self.service, cover, "zzzzzzzzzzz")
        self.service.thumbnails.return_value.set.assert_not_called()

    def test_thumbnail_rejects_non_private_video(self):
        self.service.videos.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "zzzzzzzzzzz", "snippet": {"channelId": EXPECTED_ID},
                       "status": {"privacyStatus": "public"}}]}
        cover = Path(self.work.name, "thumb.jpg")
        cover.write_bytes(b"not a production image")
        with self.assertRaisesRegex(ValueError, "privado"):
            add_thumbnail(self.service, cover, "zzzzzzzzzzz")
        self.service.thumbnails.return_value.set.assert_not_called()


if __name__ == "__main__":
    unittest.main()
