"""Reject release of a different episode, revision, media or failed QA."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from restore_news_publication import validate_bundle


class RestoreNewsPublicationTests(unittest.TestCase):
    def setUp(self):
        self.project_id = "noticia-2026-10-10-teste-producao"
        self.video = b"original MP4 bytes"
        self.digest = hashlib.sha256(self.video).hexdigest()
        self.files = {
            "video/generated/daily-project.json": self.encode({"project_id": self.project_id, "title": "Notícia verificada"}),
            "video/generated/daily-delivery-qa.json": self.encode({"status": "warn", "failures": [], "video": {"sha256": self.digest}}),
            "render-output/daily-youtube.json": self.encode({"title": "Notícia verificada"}),
            "render-output/daily-video.mp4": self.video,
        }
        self.receipt = {"project_id": self.project_id, "destination": "youtube", "privacy_requested": "private",
                        "video_sha256": self.digest, "video_id": "abcdefghijk"}
        self.episode = self.encode({"episode_id": self.project_id, "editorial_status": "autonomous_fact_checked"})

    @staticmethod
    def encode(value):
        return json.dumps(value, ensure_ascii=False, indent=2).encode()

    def validate(self, current=None, source=None):
        return validate_bundle(self.files, self.encode(self.receipt), current or self.episode, source or self.episode)

    def test_restore_exact_original_with_nonblocking_warnings(self):
        self.assertEqual(self.validate(), (self.project_id, "abcdefghijk"))

    def test_changed_episode_blocks_previous_revision(self):
        with self.assertRaisesRegex(ValueError, "Episódio mudou"):
            self.validate(current=self.episode + b" ")

    def test_windows_line_endings_do_not_change_revision(self):
        self.assertEqual(self.validate(current=self.episode.replace(b"\n", b"\r\n"))[0], self.project_id)

    def test_changed_video_is_rejected_even_with_valid_receipt(self):
        self.files["render-output/daily-video.mp4"] = b"different MP4"
        with self.assertRaisesRegex(ValueError, "MP4 difere"):
            self.validate()

    def test_critical_qa_blocks_release(self):
        self.files["video/generated/daily-delivery-qa.json"] = self.encode({"status": "warn", "failures": [{"code": "missing-audio"}], "video": {"sha256": self.digest}})
        with self.assertRaisesRegex(ValueError, "QA original"):
            self.validate()

    def test_receipt_for_other_media_is_rejected(self):
        self.receipt["video_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Recibo não comprova"):
            self.validate()

    def test_metadata_for_other_title_is_rejected(self):
        self.files["render-output/daily-youtube.json"] = self.encode({"title": "Outro vídeo"})
        with self.assertRaisesRegex(ValueError, "Título do pacote"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
