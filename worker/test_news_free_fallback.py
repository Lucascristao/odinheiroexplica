"""No paid routing, credential leakage, or provider-switching after a verdict."""
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent))
import news_groq_client as groq
import news_free_fallback as free


def reply(content='{"ok":true}', status=200, **extra):
    response = Mock(status_code=status, headers={'retry-after': '900'})
    response.json.return_value = {'model': 'fixture/model:free',
        'choices': [{'finish_reason': 'stop', 'message': {'content': content}}],
        'usage': {'total_tokens': 40, 'cost': 0}, **extra}
    return response


class FreeFallback(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(free.os.environ, {'OPENROUTER_API_KEY': 'free-key-fixture',
            'GROQ_API_KEY': 'groq-key-fixture', 'ODE_NEWS_FREE_FALLBACK': 'openrouter',
            'ODE_NEWS_GROQ_FALLBACK_MODELS': 'openai/gpt-oss-20b',
            'ODE_NEWS_GROQ_MODEL': groq.MODEL, 'ODE_NEWS_FREE_MIN_INTERVAL_SECONDS': '0',
            'ODE_NEWS_GROQ_MIN_INTERVAL_SECONDS': '0'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.cooldowns = patch.dict(groq.__dict__, {'_model_cooldowns': {}})
        self.cooldowns.start()
        self.addCleanup(self.cooldowns.stop)
        self.sleep = patch.object(free.time, 'sleep')
        self.sleep.start()
        self.addCleanup(self.sleep.stop)

    def test_success_retains_schema_and_locks_zero_cost_router(self):
        schema = {'type': 'object', 'properties': {'ok': {'type': 'boolean'}}}
        diag = {}
        with patch.object(free.requests, 'post', return_value=reply()) as post:
            self.assertEqual(json.loads(free.complete_free('Fixture', json_mode=True,
                response_schema=schema, max_output_tokens=100, diagnostics=diag)), {'ok': True})
        args, kwargs = post.call_args
        self.assertEqual(args[0], free.ENDPOINT)
        self.assertEqual(kwargs['json']['model'], 'openrouter/free')
        self.assertNotIn('models', kwargs['json'])
        self.assertEqual(kwargs['json']['provider']['max_price'], {'prompt': 0, 'completion': 0})
        self.assertEqual(kwargs['json']['response_format']['json_schema']['schema'], schema)
        self.assertEqual(diag['provider'], 'openrouter')
        self.assertEqual(diag['model'], 'fixture/model:free')
        self.assertNotIn('key-fixture', json.dumps(diag))

    def test_exhausted_groq_models_use_external_provider(self):
        diag = {}
        with patch.object(groq.requests, 'post', side_effect=[reply(status=429), reply(status=429), reply()]) as post:
            self.assertEqual(json.loads(groq.complete('Fixture', json_mode=True, diagnostics=diag)), {'ok': True})
        self.assertEqual([call.args[0] for call in post.call_args_list], [groq.ENDPOINT, groq.ENDPOINT, free.ENDPOINT])
        self.assertEqual(post.call_args.kwargs['headers']['Authorization'], 'Bearer free-key-fixture')
        self.assertEqual(diag['provider'], 'openrouter')

    def test_negative_factual_verdict_never_switches_provider(self):
        with patch.object(groq.requests, 'post', return_value=reply('{"approved":false}')) as post:
            self.assertIs(json.loads(groq.complete('Fixture', json_mode=True))['approved'], False)
        self.assertEqual(post.call_count, 1)

    def test_missing_key_never_calls_other_host(self):
        with patch.dict(free.os.environ, {'OPENROUTER_API_KEY': ''}), patch.object(free.requests, 'post') as post:
            with self.assertRaisesRegex(RuntimeError, 'credential unavailable'):
                free.complete_free('Fixture')
            post.assert_not_called()

    def test_paid_model_setting_cannot_change_fixed_router(self):
        with patch.dict(free.os.environ, {'ODE_NEWS_OPENROUTER_MODEL': 'paid/model'}), \
             patch.object(free.requests, 'post', return_value=reply()) as post:
            free.complete_free('Fixture')
            self.assertEqual(post.call_args.kwargs['json']['model'], free.MODEL)

    def test_nonzero_cost_response_cannot_be_accepted_as_free(self):
        with patch.object(free.requests, 'post', return_value=reply(usage={'cost': .01})):
            with self.assertRaisesRegex(RuntimeError, 'invalid response'):
                free.complete_free('Fixture')

    def test_quota_error_never_emits_provider_body_or_routes_to_paid(self):
        diag = {}
        with patch.object(free.requests, 'post', return_value=reply(status=429,
             error={'message': 'PRIVATE-provider-content'})) as post, contextlib.redirect_stdout(io.StringIO()) as out:
            with self.assertRaisesRegex(RuntimeError, 'http_429') as error:
                free.complete_free('PRIVATE-prompt', diagnostics=diag)
        self.assertEqual(post.call_count, 1)
        self.assertNotIn('PRIVATE', str(error.exception) + out.getvalue() + json.dumps(diag))


if __name__ == '__main__':
    unittest.main()
