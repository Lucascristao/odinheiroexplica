"""Offline research diagnostics: rejection reasons and sensitive-input omission."""
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

DRAFT = Path(__file__).resolve().parent

def dependency(name, **members):
    module = ModuleType(name)
    module.__dict__.update(members)
    sys.modules[name] = module

dependency("requests", get=Mock(side_effect=AssertionError("Network is forbidden")), RequestException=Exception)
dependency("news_scout", collect=Mock(side_effect=AssertionError("No live collection")))
dependency("news_source_corpus", collect_verified=Mock(), extract_article=Mock())
dependency("news_groq_client", complete=Mock(side_effect=AssertionError("Model is forbidden")))
dependency("news_single_project", validate=Mock(), transform=Mock())
dependency("build_youtube_package", validate_publication_fields=Mock())
spec = spec_from_file_location("diagnostic_editor", DRAFT / "news_autonomous_editor.py")
editor = module_from_spec(spec)
spec.loader.exec_module(editor)

class ResearchDiagnosticTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="diagnostic-unit-", dir=DRAFT)
        self.folder = Path(temp.name).resolve()
        self.assertTrue(self.folder.is_relative_to(DRAFT))
        self.addCleanup(temp.cleanup)
        self.path = self.folder / "diagnostic.json"
        self.body = "FULL_ARTICLE_BODY_MUST_NOT_BE_WRITTEN " * 30
        self.corpus = [{"category":"politics", "headline":"Fixture article headline",
                       "publisher_host":"example.com", "url":"https://example.com/current-article",
                       "feed_published_utc":"2026-10-13T15:00:00Z", "actual_article_text":self.body}]

    def call(self, report, path=True):
        with patch.object(editor, "collect_verified", return_value=self.corpus), patch.object(editor, "complete", return_value=report):
            return editor.research([], [], "2026-10-13T12:00:00-03:00", diagnostic_path=self.path if path else None)

    def test_marker_reason_is_preserved_before_gate_raises(self):
        with self.assertRaises(RuntimeError):
            self.call("EDITORIAL_INSUFFICIENT_EVIDENCE " + "Reason. " * 70)
        record = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(record["rejection_reasons"], ["marker"])
        self.assertFalse(record["factual_review_completed"])

    def test_short_report_is_distinct_from_marker(self):
        with self.assertRaises(RuntimeError):
            self.call("Resposta curta sem marcador.")
        record = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(record["rejection_reasons"], ["short_report"])
        self.assertEqual(record["model_report"]["characters"], 28)

    def test_full_article_and_labeled_credentials_are_not_saved(self):
        report = self.body + " GROQ_API_KEY=synthetic-sensitive-value Bearer synthetic-bearer-value " + "Context. " * 100
        self.assertEqual(self.call(report), report)
        saved = self.path.read_text(encoding="utf-8")
        for forbidden in (self.body, "FULL_ARTICLE_BODY_MUST_NOT_BE_WRITTEN", "actual_article_text", "synthetic-sensitive-value", "synthetic-bearer-value"):
            self.assertNotIn(forbidden, saved)
        record = json.loads(saved)
        self.assertEqual(record["corpus"][0]["article_characters"], len(self.body))
        self.assertLessEqual(len(record["model_report"]["preview"]), 1500)
        self.assertFalse(record["factual_review_completed"])

    def test_default_path_has_no_file_write_side_effect(self):
        with patch.object(editor.Path, "write_text", side_effect=AssertionError("Unexpected diagnostic write")):
            self.assertEqual(self.call("Fixture factual report. " * 25, path=False), "Fixture factual report. " * 25)
        self.assertFalse(self.path.exists())

    def test_model_exception_keeps_metadata_without_exception_body(self):
        with patch.object(editor, "collect_verified", return_value=self.corpus), patch.object(editor, "complete", side_effect=RuntimeError("synthetic-sensitive-value")):
            with self.assertRaises(RuntimeError):
                editor.research([], [], "2026-10-13T12:00:00-03:00", diagnostic_path=self.path)
        saved = self.path.read_text(encoding="utf-8")
        self.assertNotIn("synthetic-sensitive-value", saved)
        record = json.loads(saved)
        self.assertEqual(record["error_type"], "RuntimeError")
        self.assertIsNone(record["model_report"])

    def test_transport_keeps_counts_but_omits_credentials_and_payloads(self):
        report = "Fixture unverified report. " * 25
        def complete(prompt, *, diagnostics):
            diagnostics.update({"provider":"groq", "model":"openai/gpt-oss-120b",
                                "attempt":1, "http_status":200, "finish_reason":"length",
                                "usage":{"prompt_tokens":3000, "completion_tokens":1200,
                                         "total_tokens":4200, "reasoning_tokens":900,
                                         "private_extra":"synthetic-sensitive-value"},
                                "api_key":"synthetic-sensitive-value", "content":self.body,
                                "headers":{"Authorization":"Bearer synthetic-bearer-value"}})
            return report
        with patch.object(editor, "collect_verified", return_value=self.corpus), patch.object(editor, "complete", side_effect=complete):
            self.assertEqual(editor.research([], [], "2026-10-13T12:00:00-03:00", diagnostic_path=self.path), report)
        saved = self.path.read_text(encoding="utf-8")
        self.assertNotIn("synthetic-sensitive-value", saved)
        self.assertNotIn("synthetic-bearer-value", saved)
        self.assertNotIn(self.body, saved)
        transport = json.loads(saved)["transport"]
        self.assertEqual(transport["finish_reason"], "length")
        self.assertEqual(transport["usage"]["reasoning_tokens"], 900)
        self.assertEqual(transport["usage"]["completion_tokens"], 1200)
        self.assertNotIn("api_key", transport)
        self.assertNotIn("content", transport)
        self.assertNotIn("headers", transport)
        self.assertNotIn("private_extra", transport["usage"])

if __name__ == "__main__":
    unittest.main()
