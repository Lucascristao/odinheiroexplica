"""Regression: a fact-checked 44-second summary must not become future news."""
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
from news_schedule import load_config
from news_minimum_duration import DevelopmentIncomplete, policy_for_episode, require_developed_script, require_measured_duration
from news_production_gate import validate_production
from news_quality_contract import editorial_fingerprint
from news_editorial_quality import develop


class MinimumNewsDuration(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.episode = {'episode_id': 'noticia-2026-11-10-noite', 'news_date': '2026-11-10',
            'editorial_status': 'autonomous_fact_checked', 'segments': [{'narration': 'fixture ' * 99}]}
        self.episode['editorial_quality'] = {'version': '2026-11-10.1', 'narration_word_count': 99,
            'reviewed_content_sha256': editorial_fingerprint(self.episode), 'review': {'approved': True, 'issues': []}}

    def test_approved_facts_do_not_allow_a_short_future_script(self):
        with self.assertRaises(DevelopmentIncomplete):
            validate_production(self.episode, self.config, datetime(2026, 11, 10, 22, tzinfo=timezone.utc))

    def test_already_sent_18h_episode_keeps_original_contract(self):
        self.episode['episode_id'] = 'noticia-2026-11-10-noite-1'
        self.assertIsNone(policy_for_episode(self.episode, self.config))
        validate_production(self.episode, self.config, datetime(2026, 11, 10, 22, tzinfo=timezone.utc))

    def test_future_day_also_requires_minimum(self):
        self.episode.update(news_date='2026-11-11', episode_id='noticia-2026-11-11-manha')
        self.assertEqual(policy_for_episode(self.episode, self.config)['seconds'], 180)

    def test_developed_script_stamps_contract_for_measured_qa(self):
        self.episode['segments'][0]['narration'] = 'fixture ' * 650
        self.episode['editorial_quality']['review']['development_checks'] = dict.fromkeys((
            'logical_progression', 'substantive_context', 'no_padding_or_repetition', 'opening_question_answered'), True)
        require_developed_script(self.episode, self.config, stamp=True)
        self.assertEqual(self.episode['editorial_quality']['minimum_duration_seconds'], 180)
        require_developed_script(self.episode, self.config)

    def test_length_alone_does_not_approve_undeveloped_narrative(self):
        self.episode['segments'][0]['narration'] = 'fixture ' * 650
        with self.assertRaisesRegex(DevelopmentIncomplete, 'narrative development'):
            require_developed_script(self.episode, self.config, stamp=True)

    def test_planned_length_or_silence_cannot_hide_short_narration(self):
        for video, narration in ((44, 44), (300, 44), (300, 179.99), (179.99, 220)):
            qa = {'video': {'expected_seconds': 300, 'video_seconds': video}, 'scenes': [{'audio_seconds': narration}]}
            with self.subTest(video=video, narration=narration), self.assertRaises(ValueError):
                require_measured_duration(qa, 180)

    def test_real_three_minutes_pass_and_invalid_measurements_fail(self):
        require_measured_duration({'video': {'video_seconds': 180}, 'scenes': [{'audio_seconds': 90}, {'audio_seconds': 90}]}, 180)
        for value in (float('nan'), float('inf'), None, '200'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                require_measured_duration({'video': {'video_seconds': value}, 'scenes': [{'audio_seconds': 200}]}, 180)

    def test_completed_short_checkpoint_is_redeveloped_instead_of_skipped(self):
        episode = {'segments': [{'id': 'one', 'title': 'Opening', 'type': 'fact', 'narration': 'Short old draft', 'document_id': 'd1'}],
            'verified_facts': [], 'documentary_evidence': [{'id': 'd1', 'source_id': 'S1'}],
            'news_selection': {'opening_anchor': 'Short old draft'}, 'discovery_strategy': {'first_payoff': 'Short old draft'}}
        with patch('news_editorial_quality.parse_reply', return_value={'narration': 'fixture ' * 650}) as writer:
            develop(episode, {'S1': {'text': 'Fixture source'}}, completed_ids={'one'}, minimum_words=600)
        self.assertEqual(writer.call_count, 1)
        self.assertGreater(writer.call_args.kwargs['budget'], 1100)


if __name__ == '__main__':
    unittest.main()
