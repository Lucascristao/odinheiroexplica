import hashlib
import unittest
from unittest.mock import Mock, patch
from news_content_hold import hold
from youtube_publication import EXPECTED_ID


class ContentHold(unittest.TestCase):
    def setUp(self):
        self.record = {'project_id': 'noticia-2026-11-10-manha', 'video_id': '1ofBrOabvfc',
            'episode_sha256': hashlib.sha256(b'original').hexdigest(), 'requested_privacy': 'private',
            'reason': 'Material narration error confirmed in the source and recorded for correction.'}
        self.receipt = {**self.record, 'destination': 'youtube'}
        self.service = Mock()
        video = {'id': self.record['video_id'], 'snippet': {'channelId': EXPECTED_ID,
            'tags': ['ODE_EPISODE_' + self.record['project_id']]}, 'status': {'privacyStatus': 'public'}}
        confirmed = {**video, 'status': {'privacyStatus': 'private'}}
        self.service.videos.return_value.list.return_value.execute.side_effect = [{'items': [video]}, {'items': [confirmed]}]

    @patch('news_content_hold.assert_channel')
    def test_only_private_write_and_exact_original_id(self, channel):
        self.assertEqual(hold(self.service, self.record, self.receipt, b'original')['confirmed_privacy'], 'private')
        self.service.videos.return_value.update.assert_called_once_with(part='status',
            body={'id': '1ofBrOabvfc', 'status': {'privacyStatus': 'private'}})

    def test_changed_episode_or_receipt_cannot_withdraw_another_video(self):
        self.receipt['video_id'] = 'other_video'
        with self.assertRaises(ValueError):
            hold(self.service, self.record, self.receipt, b'original')
        self.service.videos.assert_not_called()


if __name__ == '__main__':
    unittest.main()
