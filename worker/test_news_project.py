"""Offline checks for fact-checked multi-news editions and video engine adapter."""
import copy
import json
import unittest
from datetime import date
from pathlib import Path
from news_project import validate, transform

PATH = Path(__file__).resolve().parents[1] / "news/editions/pilot-2026-10-08-noite.json"


class NewsPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.edition = json.loads(PATH.read_text(encoding="utf-8"))

    def test_real_pilot_contains_three_distinct_stories(self):
        validate(self.edition, now=date(2026, 10, 9))
        self.assertEqual(len(self.edition["stories"]), 3)
        self.assertEqual(len(set(x["id"] for x in self.edition["stories"])), 3)

    def test_transform_reuses_roberto_and_official_remotion_stage(self):
        project = transform(self.edition)
        self.assertEqual(project["presenter"]["name"], "Roberto")
        self.assertEqual(len(project["scenes"]), 5)
        self.assertEqual(project["project_id"], self.edition["edition_id"])
        for s in project["scenes"]:
            self.assertEqual(s["visual"]["type"], "authored_stage")
            self.assertGreaterEqual(len(s["visual"]["beats"]), 3)
            text = s["narration"]
            anchors = [beat["anchor"] for beat in s["visual"]["beats"]]
            self.assertEqual(len(set(anchors)), len(anchors))
            self.assertTrue(all(text.count(a) == 1 for a in anchors))
            self.assertEqual(s["tts"]["delivery"], "explain")

    def test_no_one_story_bulletin(self):
        doc = copy.deepcopy(self.edition)
        doc["stories"] = doc["stories"][:1]
        with self.assertRaisesRegex(ValueError, "3 a 6"):
            validate(doc, now=date(2026, 10, 9))

    def test_no_single_source_bulletin(self):
        doc = copy.deepcopy(self.edition)
        doc["stories"][0]["sources"] = doc["stories"][0]["sources"][:1]
        with self.assertRaisesRegex(ValueError, "2 fontes"):
            validate(doc, now=date(2026, 10, 9))

    def test_no_identical_source_domains(self):
        doc = copy.deepcopy(self.edition)
        doc["stories"][0]["sources"][1]["url"] = "https://saladeimprensa.correios.com.br/outro"
        with self.assertRaisesRegex(ValueError, "publicadores diferentes"):
            validate(doc, now=date(2026, 10, 9))

    def test_editorial_rejection_blocks_production(self):
        doc = copy.deepcopy(self.edition)
        doc["editorial_status"] = "draft"
        with self.assertRaisesRegex(ValueError, "aprovação editorial"):
            validate(doc, now=date(2026, 10, 9))

    def test_future_news_blocked(self):
        doc = copy.deepcopy(self.edition)
        with self.assertRaisesRegex(ValueError, "notícia futura"):
            validate(doc, now=date(2026, 9, 1))


if __name__ == "__main__":
    unittest.main()
