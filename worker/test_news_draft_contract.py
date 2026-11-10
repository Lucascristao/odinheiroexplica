import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent))
from news_draft_contract import episode_schema
import news_groq_client as groq


class StructuredNews(unittest.TestCase):
    def test_schema_forces_mechanical_shapes_without_factual_approval(self):
        schema = episode_schema()
        def inspect(node):
            if node.get('type') == 'object':
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
