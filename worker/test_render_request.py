"""Offline checks preventing unintended regeneration on push or retry."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_request  # noqa: E402


class RenderRequestTests(unittest.TestCase):
    def test_manual_fresh_request_is_limited_to_first_attempt(self):
        self.assertTrue(render_request.force_fresh_audio("workflow_dispatch", "1", "true"))
        self.assertFalse(render_request.force_fresh_audio("workflow_dispatch", "2", "true"))
        self.assertFalse(render_request.force_fresh_audio("workflow_dispatch", "3", "true"))

    def test_push_or_missing_context_does_not_regenerate_audio(self):
        self.assertFalse(render_request.force_fresh_audio("push", "1", "true"))
        self.assertFalse(render_request.force_fresh_audio("", "1", "true"))
        self.assertFalse(render_request.force_fresh_audio("workflow_dispatch", "", "true"))

    def test_manual_request_defaults_to_resume(self):
        self.assertFalse(render_request.force_fresh_audio("workflow_dispatch", "1", "false"))
        self.assertFalse(render_request.force_fresh_audio("workflow_dispatch", "1", ""))
        self.assertFalse(render_request.force_fresh_audio("workflow_dispatch", "1", "1"))

    def test_environment_output_preserves_metadata_and_cache_version(self):
        values = render_request.environment_values({
            "project_id": "dolar\r\n2026",
            "title": "Título secundário",
            "packaging": {"titles": [{"text": "Dólar\r\n e eleição\0"}]},
        }, {})
        self.assertEqual(values["ODE_VIDEO_TITLE"], "Dólar   e eleição ")
        self.assertEqual(values["ODE_PROJECT_SLUG"], "dolar--2026")
        self.assertEqual(values["ODE_FORCE_FRESH_AUDIO"], "false")
        self.assertEqual(values["ODE_VOICE_POLICY_VERSION"], render_request.VOICE_POLICY_VERSION)
        self.assertEqual(values["ODE_VOICE_POLICY_CACHE_KEY"], render_request.VOICE_POLICY_CACHE_KEY)
        self.assertTrue(all("\n" not in value and "\r" not in value for value in values.values()))


if __name__ == "__main__":
    unittest.main()
