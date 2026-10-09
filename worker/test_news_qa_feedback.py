"""Regression: news QA warnings become reviewable lessons, not release blockers."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import news_qa_feedback as feedback


class QaFeedbackTests(unittest.TestCase):
    def test_warnings_saved_with_actionable_recommendations(self):
        qa = {
            "status": "warn", "failures": [],
            "warnings": [
                {"code": "asr-low-coverage", "scene_id": "scene-01", "coverage": .82},
                {"code": "estimated-visual-anchors", "scene_id": "scene-01", "count": 3},
                {"code": "asr-low-coverage", "scene_id": "scene-02", "coverage": .74},
            ],
        }
        result = feedback.summarize(qa, {"episode_id": "noticia-2026-10-09-meio-dia"})
        self.assertEqual(result["warning_count"], 3)
        self.assertEqual(result["failure_count"], 0)
        self.assertEqual(result["warning_counts_by_code"]["asr-low-coverage"], 2)
        self.assertEqual(result["next_cycle_actions"][0]["code"], "asr-low-coverage")
        self.assertIn("próxima pauta", result["next_cycle_actions"][0]["suggestion"])
        self.assertEqual(result["learning_status"], "pending_next_edition_review")
        self.assertEqual(result["warnings"], qa["warnings"])

    def test_failures_remain_visible_without_false_approval(self):
        qa = {"status": "fail", "warnings": [{"code": "unknown-warning"}],
              "failures": [{"code": "mp4-timeline-coverage"}]}
        result = feedback.summarize(qa, {"episode_id": "noticia-2026-10-09-noite"})
        self.assertEqual(result["qa_status"], "fail")
        self.assertEqual(result["failure_count"], 1)
        self.assertIn("não presumir causa", result["next_cycle_actions"][0]["suggestion"])

    def test_cli_persists_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            qa_path, episode_path, output = (directory / x for x in ("qa.json", "episode.json", "feedback.json"))
            qa_path.write_text(json.dumps({"status": "pass", "failures": [], "warnings": []}), encoding="utf-8")
            episode_path.write_text(json.dumps({"episode_id": "noticia-2026-10-09-manha"}), encoding="utf-8")
            with patch.object(sys, "argv", ["feedback", "--qa", str(qa_path),
                                             "--episode", str(episode_path), "--output", str(output)]):
                feedback.main()
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["learning_status"], "no_warning_follow_up")
            self.assertEqual(result["warning_count"], 0)


if __name__ == "__main__":
    unittest.main()
