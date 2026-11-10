"""Recovery must use corrected content while preserving any started upload."""
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from news_render_dispatch import ensure_render, choose_action, UPLOAD_STEP
from news_schedule import load_config


class FakeAPI:
    def __init__(self, previous=None, upload='skipped'):
        self.current = json.dumps({'news_date': '2026-11-10', 'episode_id': 'noticia-2026-11-10-manha-2',
            'editorial_status': 'autonomous_fact_checked', 'publication_target_local': '2026-11-10T10:30:00-03:00'}).encode()
        self.previous = previous
        self.upload = upload
        self.writes = []

    def episode(self, path, ref='main'):
        return self.current if ref == 'main' else self.previous

    def request(self, path, payload=None):
        if payload is not None:
            self.writes.append((path, payload))
            return None
        if path.startswith('/commits?'):
            return [{'commit': {'committer': {'date': '2026-11-10T12:00:00Z'}}}]
        if path.startswith('/actions/workflows/'):
            return {'workflow_runs': [{'id': 42, 'head_sha': 'previous', 'status': 'completed', 'conclusion': 'cancelled',
                'event': 'workflow_dispatch', 'display_title': 'ODE render | news/episodes/2026-11-10-manha-2.json',
                'created_at': '2026-11-10T12:01:00Z', 'updated_at': '2026-11-10T12:10:00Z'}]}
        if path.startswith('/actions/runs/42/jobs'):
            return {'jobs': [{'steps': [{'name': UPLOAD_STEP, 'conclusion': self.upload}]}]}
        raise AssertionError(path)


class RevisedBeforeUpload(unittest.TestCase):
    def test_no_attempt_ceiling_still_preserves_upload_and_cooldown(self):
        now = datetime(2026, 11, 10, 23, tzinfo=timezone.utc)
        run = {'id': 42, 'status': 'completed', 'conclusion': 'failure', 'run_attempt': 12,
               'created_at': '2026-11-10T15:00:00Z', 'updated_at': '2026-11-10T22:00:00Z'}
        jobs = {42: [{'steps': [{'name': UPLOAD_STEP, 'conclusion': 'skipped'}]}]}
        self.assertEqual(choose_action([run], jobs, now, max_attempts=None)['action'], 'rerun')
        jobs[42][0]['steps'][0]['conclusion'] = 'success'
        self.assertEqual(choose_action([run], jobs, now, max_attempts=None)['reason'], 'upload_started_or_state_unknown')

    def run_recovery(self, api):
        return ensure_render(api, 'news/episodes/2026-11-10-manha-2.json', api.current, load_config(),
                             datetime(2026, 11, 10, 13, tzinfo=timezone.utc), apply=True)

    def test_revised_episode_gets_current_main_after_all_uploads_skipped(self):
        api = FakeAPI(previous=b'{"rejected":"old event"}')
        result = self.run_recovery(api)
        self.assertEqual(result['reason'], 'episode_revised_before_upload')
        self.assertEqual(api.writes, [('/actions/workflows/render-news-single.yml/dispatches',
            {'ref': 'main', 'inputs': {'edition_path': 'news/episodes/2026-11-10-manha-2.json'}})])

    def test_episode_absent_in_quarantine_commit_can_be_reselected(self):
        api = FakeAPI(previous=None)
        self.assertEqual(self.run_recovery(api)['action'], 'dispatch')

    def test_unchanged_episode_keeps_existing_run_and_voice_cache(self):
        api = FakeAPI()
        api.previous = api.current
        self.assertEqual(self.run_recovery(api)['action'], 'rerun')
        self.assertEqual(api.writes, [('/actions/runs/42/rerun-failed-jobs', {})])

    def test_started_or_unknown_upload_prevents_new_video_even_after_rewrite(self):
        for state in ('failure', 'success', None):
            api = FakeAPI(previous=b'old', upload=state)
            with self.subTest(state=state):
                self.assertEqual(self.run_recovery(api)['reason'], 'upload_started_or_state_unknown')
                self.assertEqual(api.writes, [])

    def test_dry_run_never_dispatches_revised_episode(self):
        api = FakeAPI(previous=b'old')
        result = ensure_render(api, 'news/episodes/2026-11-10-manha-2.json', api.current, load_config(),
                               datetime(2026, 11, 10, 13, tzinfo=timezone.utc), apply=False)
        self.assertFalse(result['applied'])
        self.assertEqual(api.writes, [])


if __name__ == '__main__':
    unittest.main()
