"""Offline tests for transient navigation handling in source captures."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import auto_capture_sources as capture  # noqa: E402


class FakePage:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.evaluate_calls = 0
        self.load_waits = []

    def evaluate(self, _script, *_args):
        self.evaluate_calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def wait_for_load_state(self, state, timeout=None):
        self.load_waits.append((state, timeout))

    def wait_for_timeout(self, _milliseconds):
        return None


class AutoCaptureNavigationTests(unittest.TestCase):
    def test_retries_execution_context_destroyed(self):
        page = FakePage([
            Exception(
                "Page.evaluate: Execution context was destroyed, "
                "most likely because of a navigation"
            ),
            "conteúdo",
        ])
        result = capture.evaluate_with_navigation_retry(
            page,
            "() => document.body.innerText",
            operation_name="ler o conteúdo",
        )
        self.assertEqual(result, "conteúdo")
        self.assertEqual(page.evaluate_calls, 2)
        self.assertGreaterEqual(len(page.load_waits), 1)

    def test_does_not_retry_non_navigation_error(self):
        page = FakePage([Exception("JavaScript syntax error")])
        with self.assertRaisesRegex(Exception, "syntax error"):
            capture.evaluate_with_navigation_retry(
                page,
                "() => broken()",
                operation_name="executar script",
            )
        self.assertEqual(page.evaluate_calls, 1)

    def test_stops_after_three_transient_failures(self):
        error = Exception(
            "Page.evaluate: Execution context was destroyed, "
            "most likely because of a navigation"
        )
        page = FakePage([error, error, error])
        with self.assertRaisesRegex(Exception, "Execution context was destroyed"):
            capture.evaluate_with_navigation_retry(
                page,
                "() => document.body.innerText",
            )
        self.assertEqual(page.evaluate_calls, 3)


if __name__ == "__main__":
    unittest.main()
