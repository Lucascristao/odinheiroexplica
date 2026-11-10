"""Receipt isolation, idempotency and bounded retries for optional late covers."""
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import tempfile
import unittest
from news_cover_recovery import validate_receipt, already_delivered, retry_available


class LateCoverTests(unittest.TestCase):
    def setUp(self):
        self.receipt = {'project_id': 'noticia-2026-11-10-manha', 'video_id': 'W34OwdmtBxc',
                        'destination': 'youtube', 'privacy_requested': 'private'}

    def test_original_private_upload_receipt_identifies_existing_video(self):
        self.assertEqual(validate_receipt(self.receipt), self.receipt['project_id'])

    def test_receipt_cannot_redirect_to_another_destination_or_path(self):
        for field, value in [('project_id', '../another'), ('destination', 'drive'), ('video_id', 'invalid')]:
            with self.assertRaises(ValueError):
                validate_receipt({**self.receipt, field: value})

    def test_already_attached_bytes_are_idempotent_but_changed_cover_needs_delivery(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporary:
            folder = Path(temporary)
            image = folder / 'thumbnail.jpg'
            image.write_bytes(b'fixture approved pixels')
            delivery = {**self.receipt, 'thumbnail_sha256': hashlib.sha256(image.read_bytes()).hexdigest()}
            self.assertTrue(already_delivered(delivery, self.receipt, folder))
            self.assertFalse(already_delivered({**delivery, 'video_id': 'abcdefghijk'}, self.receipt, folder))
            image.write_bytes(b'new fixture pixels')
            self.assertFalse(already_delivered(delivery, self.receipt, folder))

    def test_quota_failure_waits_then_retries_without_unlimited_calls(self):
        now = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
        state = {'attempts': [{'started_at': (now-timedelta(minutes=30)).isoformat()}]}
        self.assertFalse(retry_available(state, now))
        self.assertTrue(retry_available(state, now+timedelta(hours=1)))
        state['attempts'] *= 3
        self.assertFalse(retry_available(state, now+timedelta(hours=4)))


if __name__ == '__main__':
    unittest.main()
