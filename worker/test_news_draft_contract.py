import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent))
from news_draft_contract import episode_schema, normalize_draft_metadata, object_encoding
import news_groq_client as groq


class StructuredNews(unittest.TestCase):
    def test_metadata_repair_does_not_invent_or_change_sources_facts_or_event_dates(self):
        original = {'news_date': '2026-11-10', 'event_date': '2026-11-09',
            'verified_facts': [{'claim': 'Fixture fact from yesterday', 'event_date': '2026-11-09'}],
            'sources': [{'url': 'https://example.org/original', 'published_at': '2026-11-10'}],
            'news_selection': {'topic_area': 'Economia / Empresas', 'new_fact': 'Fixture fact from yesterday',
                'opening_anchor': 'Este trecho literal apresenta o fato real.'},
            'segments': [{'narration': 'Este trecho literal apresenta o fato real.'}],
            'scorecard': [], 'pronunciations': [], 'discovery_strategy': []}
        facts = json.loads(json.dumps({k: original[k] for k in ('verified_facts', 'sources', 'event_date')}))
        repaired = normalize_draft_metadata(original)
        self.assertIsInstance(repaired['scorecard'], dict)
        self.assertEqual(repaired['pronunciations'], {})
        self.assertEqual(repaired['discovery_strategy']['first_payoff'], repaired['news_selection']['opening_anchor'])
        self.assertEqual({k: repaired[k] for k in facts}, facts)
        self.assertNotIn('editorial_quality', repaired)

    def test_object_encoding_never_discards_duplicate_factual_keys(self):
        self.assertEqual(object_encoding([{'a': 1}, {'b': 2}]), {'a': 1, 'b': 2})
        self.assertIsNone(object_encoding([{'event_date': '2026-11-09'}, {'event_date': '2026-11-10'}]))

    def test_schema_failure_can_preserve_json_candidate_without_approving_facts(self):
        bad = Mock(status_code=400)
        bad.json.return_value = {'error': {'failed_generation': '{"scorecard":[],"news_date":"2026-11-09"}'}}
        with patch.dict(groq.__dict__, {'_model_cooldowns': {}}), patch.dict(groq.os.environ,
                {'GROQ_API_KEY': 'unit-test-fixture', 'ODE_NEWS_GROQ_MIN_INTERVAL_SECONDS': '0'}), \
             patch.object(groq.requests, 'post', return_value=bad) as post:
            raw = json.loads(groq.complete('JSON fixture', json_mode=True, response_schema=episode_schema()))
        self.assertEqual(raw['news_date'], '2026-11-09')
        self.assertNotIn('editorial_quality', raw)
        self.assertEqual(post.call_count, 1)

    def test_schema_forces_mechanical_shapes_without_factual_approval(self):
        schema = episode_schema()
        def inspect(node):
            if node.get('type') == 'object':
                self.assertTrue(node['properties'], 'Groq rejects empty object schemas even with properties={}')
                self.assertIs(node['additionalProperties'], False)
                self.assertEqual(set(node['properties']), set(node['required']))
                for child in node['properties'].values():
                    inspect(child)
            if node.get('type') == 'array':
                inspect(node['items'])
        inspect(schema)
        self.assertEqual(schema['properties']['scorecard']['type'], 'object')
        self.assertIn('insufficient_evidence', schema['properties'])
        self.assertEqual(schema['properties']['news_selection']['properties']['topic_area']['enum'],
                         ['politics', 'economy', 'personal_finance', 'business', 'international'])

    def test_transport_keeps_schema_on_availability_backup(self):
        limited = Mock(status_code=429, headers={'retry-after': '999'})
        success = Mock(status_code=200)
        success.json.return_value = {'choices': [{'finish_reason': 'stop', 'message': {'content': '{"ok":true}'}}]}
        with patch.dict(groq.__dict__, {'_model_cooldowns': {}}), patch.dict(groq.os.environ,
                {'GROQ_API_KEY': 'unit-test-fixture', 'ODE_NEWS_GROQ_MODEL': groq.MODEL,
                 'ODE_NEWS_GROQ_FALLBACK_MODELS': 'openai/gpt-oss-20b', 'ODE_NEWS_GROQ_MIN_INTERVAL_SECONDS': '0'}), \
             patch.object(groq.requests, 'post', side_effect=[limited, success]) as post:
            groq.complete('JSON fixture', json_mode=True, response_schema=episode_schema())
        for call in post.call_args_list:
            self.assertEqual(call.kwargs['json']['response_format']['type'], 'json_schema')
            self.assertTrue(call.kwargs['json']['response_format']['json_schema']['strict'])

    def test_schema_service_error_can_fall_back_to_plain_json_without_changing_model(self):
        bad = Mock(status_code=400)
        good = Mock(status_code=200)
        good.json.return_value = {'choices': [{'finish_reason': 'stop', 'message': {'content': '{"ok":true}'}}]}
        with patch.dict(groq.__dict__, {'_model_cooldowns': {}}), patch.dict(groq.os.environ,
                {'GROQ_API_KEY': 'unit-test-fixture', 'ODE_NEWS_GROQ_MIN_INTERVAL_SECONDS': '0'}), \
             patch.object(groq.requests, 'post', side_effect=[bad, good]) as post:
            groq.complete('JSON fixture', json_mode=True, response_schema=episode_schema())
        self.assertEqual(post.call_args_list[0].kwargs['json']['model'], post.call_args_list[1].kwargs['json']['model'])
        self.assertEqual(post.call_args_list[1].kwargs['json']['response_format']['type'], 'json_object')


if __name__ == '__main__':
    unittest.main()
