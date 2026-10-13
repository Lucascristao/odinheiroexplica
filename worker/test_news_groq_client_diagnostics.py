"""Offline transport metadata checks. All provider responses and keys are fixtures."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class RequestException(Exception):
    pass


REQUESTS = types.ModuleType("requests")
REQUESTS.RequestException = RequestException
REQUESTS.post = Mock()
SPEC = importlib.util.spec_from_file_location(
    "diagnostic_news_groq_client", Path(__file__).with_name("news_groq_client.py")
)
CLIENT = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"requests": REQUESTS}):
    SPEC.loader.exec_module(CLIENT)


class Response:
    def __init__(self, data=None, status=200, headers=None):
        self.status_code = status
        self.headers = headers or {}
        self._data = data or {}

    def json(self):
        return self._data


def success(content="Factual report fixture", finish="stop", usage=None):
    return Response({
        "choices": [{
            "finish_reason": finish,
            "message": {
                "content": content,
                "reasoning": "DO_NOT_COPY_PRIVATE_REASONING_FIXTURE",
            },
        }],
        "usage": usage if usage is not None else {
            "prompt_tokens": 3236, "completion_tokens": 1200, "total_tokens": 4436,
            "completion_tokens_details": {"reasoning_tokens": 850},
        },
        "api_key": "DO_NOT_COPY_PROVIDER_KEY_FIXTURE",
    })


class DiagnosticTransport(unittest.TestCase):
    def setUp(self):
        REQUESTS.post.reset_mock(return_value=True, side_effect=True)
        self.env = patch.dict(CLIENT.os.environ, {
            "GROQ_API_KEY": "DO_NOT_COPY_REQUEST_KEY_FIXTURE",
            "ODE_NEWS_GROQ_MODEL": CLIENT.MODEL,
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.sleep = patch.object(CLIENT.time, "sleep", Mock())
        self.sleep.start()
        self.addCleanup(self.sleep.stop)

    def call(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return CLIENT.complete("DO_NOT_COPY_PROMPT_FIXTURE", **kwargs)

    def test_success_captures_only_transport_and_token_metadata(self):
        REQUESTS.post.return_value = success()
        diag = {}
        self.assertEqual(self.call(diagnostics=diag), "Factual report fixture")
        self.assertEqual(diag, {
            "provider": "groq", "model": "openai/gpt-oss-120b",
            "attempt": 1, "http_status": 200, "finish_reason": "stop",
            "usage": {
                "prompt_tokens": 3236, "completion_tokens": 1200,
                "total_tokens": 4436, "reasoning_tokens": 850,
            },
        })
        serialized = json.dumps(diag)
        self.assertNotIn("DO_NOT_COPY", serialized)
        self.assertNotIn("Factual report fixture", serialized)

    def test_length_finish_is_reported_without_rejecting_the_returned_text(self):
        REQUESTS.post.return_value = success(content="short fixture", finish="length")
        diag = {}
        self.assertEqual(self.call(diagnostics=diag), "short fixture")
        self.assertEqual(diag["finish_reason"], "length")
        self.assertEqual(diag["usage"]["total_tokens"], 4436)

    def test_factual_insufficiency_and_truncation_are_distinguishable(self):
        REQUESTS.post.return_value = success(
            content="EDITORIAL_INSUFFICIENT_EVIDENCE", finish="stop"
        )
        diag = {}
        self.assertEqual(self.call(diagnostics=diag), "EDITORIAL_INSUFFICIENT_EVIDENCE")
        self.assertEqual(diag["finish_reason"], "stop")
        self.assertNotIn("EDITORIAL_INSUFFICIENT_EVIDENCE", json.dumps(diag))

    def test_legacy_call_and_diagnostic_call_use_identical_model_and_budget(self):
        REQUESTS.post.return_value = success()
        self.assertEqual(self.call(), "Factual report fixture")
        legacy_payload = REQUESTS.post.call_args.kwargs["json"]
        self.assertEqual(self.call(diagnostics={}), "Factual report fixture")
        diagnostic_payload = REQUESTS.post.call_args.kwargs["json"]
        self.assertEqual(legacy_payload, diagnostic_payload)
        self.assertEqual(diagnostic_payload["max_completion_tokens"], 2000)
        self.assertEqual(diagnostic_payload["model"], "openai/gpt-oss-120b")
        self.assertEqual(diagnostic_payload["reasoning_effort"], "low")

    def test_json_mode_budget_and_return_are_preserved(self):
        REQUESTS.post.return_value = success(content='{"fixture":true}')
        diag = {}
        self.assertEqual(self.call(json_mode=True, diagnostics=diag), '{"fixture":true}')
        payload = REQUESTS.post.call_args.kwargs["json"]
        self.assertEqual(payload["max_completion_tokens"], 5800)
        self.assertEqual(payload["response_format"], {"type": "json_object"})

    def test_missing_usage_and_finish_are_unavailable_instead_of_zero(self):
        REQUESTS.post.return_value = Response({
            "choices": [{"message": {"content": "usable fixture"}}]
        })
        diag = {}
        self.assertEqual(self.call(diagnostics=diag), "usable fixture")
        self.assertIsNone(diag["finish_reason"])
        self.assertEqual(diag["usage"], {
            "prompt_tokens": None, "completion_tokens": None,
            "total_tokens": None, "reasoning_tokens": None,
        })

    def test_top_level_reasoning_count_is_supported_without_copying_other_usage(self):
        REQUESTS.post.return_value = success(usage={
            "prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25,
            "reasoning_tokens": 7, "reasoning": "DO_NOT_COPY_REASONING_TEXT",
        })
        diag = {}
        self.call(diagnostics=diag)
        self.assertEqual(diag["usage"]["reasoning_tokens"], 7)
        self.assertEqual(set(diag["usage"]), {
            "prompt_tokens", "completion_tokens", "total_tokens", "reasoning_tokens",
        })

    def test_nested_reasoning_count_has_priority_and_zero_is_real(self):
        REQUESTS.post.return_value = success(usage={
            "prompt_tokens": 0, "completion_tokens": 1, "total_tokens": 1,
            "reasoning_tokens": 9,
            "completion_tokens_details": {"reasoning_tokens": 0},
        })
        diag = {}
        self.call(diagnostics=diag)
        self.assertEqual(diag["usage"]["reasoning_tokens"], 0)
        self.assertEqual(diag["usage"]["prompt_tokens"], 0)

    def test_unexpected_finish_reason_and_non_numeric_counts_are_sanitized(self):
        REQUESTS.post.return_value = success(
            finish="DO_NOT_COPY_MODEL_TEXT_FIXTURE",
            usage={
                "prompt_tokens": "DO_NOT_COPY_TOKENS_TEXT",
                "completion_tokens": True, "total_tokens": -1,
                "completion_tokens_details": {"reasoning_tokens": "unknown"},
            },
        )
        diag = {}
        self.call(diagnostics=diag)
        self.assertEqual(diag["finish_reason"], "unknown")
        self.assertTrue(all(value is None for value in diag["usage"].values()))
        self.assertNotIn("DO_NOT_COPY", json.dumps(diag))

    def test_retry_records_final_status_and_one_based_attempt_without_waiting(self):
        REQUESTS.post.side_effect = [
            Response(status=429, headers={"retry-after": "5"}),
            success(),
        ]
        diag = {}
        self.assertEqual(self.call(diagnostics=diag), "Factual report fixture")
        self.assertEqual(diag["attempt"], 2)
        self.assertEqual(diag["http_status"], 200)
        self.assertEqual(REQUESTS.post.call_count, 2)
        CLIENT.time.sleep.assert_called_once_with(5)

    def test_http_failure_preserves_status_but_no_provider_error_text(self):
        REQUESTS.post.return_value = Response(
            {"error": {"message": "DO_NOT_COPY_PROVIDER_ERROR_FIXTURE"}}, status=403
        )
        diag = {}
        with self.assertRaises(RuntimeError):
            self.call(diagnostics=diag)
        self.assertEqual(diag["http_status"], 403)
        self.assertEqual(diag["attempt"], 1)
        self.assertIsNone(diag["finish_reason"])
        self.assertNotIn("DO_NOT_COPY", json.dumps(diag))

    def test_connection_failure_clears_previous_response_status(self):
        REQUESTS.post.side_effect = [
            Response(status=429),
            RequestException("DO_NOT_COPY_EXCEPTION_FIXTURE"),
        ]
        diag = {}
        with self.assertRaises(RuntimeError):
            self.call(diagnostics=diag, max_retries=2)
        self.assertEqual(diag["attempt"], 2)
        self.assertIsNone(diag["http_status"])
        self.assertIsNone(diag["finish_reason"])
        self.assertNotIn("DO_NOT_COPY", json.dumps(diag))


if __name__ == "__main__":
    unittest.main()
