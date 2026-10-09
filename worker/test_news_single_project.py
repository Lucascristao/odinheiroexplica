"""Single-story editorial contract and documentary-first Remotion output, offline."""
import copy
from datetime import date
import json
from pathlib import Path
import unittest

from news_single_project import validate, transform

PILOT = Path(__file__).resolve().parents[1] / "news/episodes/2026-10-09-imposto-seletivo.json"


class SingleNewsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(PILOT.read_text(encoding="utf-8"))

    def test_single_event_with_two_independent_news_sources(self):
        validate(self.doc, date(2026, 10, 9))
        self.assertEqual(self.doc["format"], "ode-news-single")
        self.assertEqual(len(set(s["id"] for s in self.doc["sources"])), len(self.doc["sources"]))
        self.assertGreaterEqual(len(self.doc["sources"]), 2)
        self.assertEqual(self.doc["editorial_status"], "approved_for_private_pilot")

    def test_retains_real_documentary_excerpts_and_distinct_persona(self):
        p = transform(self.doc)
        self.assertEqual(len(p["scenes"]), len(self.doc["segments"]))
        self.assertEqual(p["presenter"]["name"], "Roberto")
        self.assertEqual(len(p["visual_assets"]), 2)
        self.assertTrue(all(x["type"] == "source_excerpt" for x in p["visual_assets"]))
        self.assertEqual(sum(s["visual"]["stage"]["elements"][2]["kind"] == "source_excerpt" for s in p["scenes"]), 2)
        self.assertEqual(p["packaging"]["thumbnails"][0]["headline"], self.doc["thumbnail_headline"])
        for scene in p["scenes"]:
            self.assertTrue(scene["narration"])
            self.assertGreaterEqual(len(scene["visual"]["beats"]), 3)
            self.assertTrue(all(scene["narration"].count(b["anchor"]) == 1 for b in scene["visual"]["beats"]))

    def test_no_roundup_or_missing_documents(self):
        d = copy.deepcopy(self.doc)
        d["documentary_evidence"] = []
        with self.assertRaisesRegex(ValueError, "duas referências"):
            validate(d, date(2026, 10, 9))

    def test_opinion_must_be_signposted(self):
        d = copy.deepcopy(self.doc)
        for s in d["segments"]:
            s["type"] = "fact"
        with self.assertRaisesRegex(ValueError, "opinião"):
            validate(d, date(2026, 10, 9))

    def test_only_one_story_identity(self):
        d = copy.deepcopy(self.doc)
        d["format"] = "ode-news-roundup"
        with self.assertRaisesRegex(ValueError, "uma matéria"):
            validate(d, date(2026, 10, 9))

    def test_no_laundered_forecast(self):
        d = copy.deepcopy(self.doc)
        d["verified_facts"][2]["status"] = "observed_revenue"
        with self.assertRaisesRegex(ValueError, "tipo factual"):
            validate(d, date(2026, 10, 9))

    def test_no_sources_same_domain(self):
        d = copy.deepcopy(self.doc)
        d["sources"] = d["sources"][::2]
        with self.assertRaisesRegex(ValueError, "publicadores diferentes"):
            validate(d, date(2026, 10, 9))


if __name__ == "__main__":
    unittest.main()
