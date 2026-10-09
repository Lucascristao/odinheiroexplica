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
        self.assertEqual(len(p["visual_assets"]), 5)
        self.assertEqual(len({a["id"] for a in p["visual_assets"]}), 5)
        self.assertEqual(sum(x["type"] == "source_excerpt" for x in p["visual_assets"]), 2)
        self.assertEqual(sum(x["type"] == "photo" for x in p["visual_assets"]), 3)
        self.assertEqual(sum(s["visual"]["stage"]["elements"][2]["kind"] == "source_excerpt" for s in p["scenes"]), 2)
        self.assertEqual(sum(s["visual"]["stage"]["elements"][2]["kind"] == "photo" for s in p["scenes"]), 3)
        self.assertEqual(sum(s["visual"]["stage"]["elements"][2]["kind"] in ("photo", "source_excerpt") for s in p["scenes"]), 5)
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

    def test_photos_must_have_approved_rights(self):
        d = copy.deepcopy(self.doc)
        d["context_photos"][0]["license"] = "Google Images"
        with self.assertRaisesRegex(ValueError, "licença"):
            validate(d, date(2026, 10, 9))

    def test_photo_count_is_not_a_fixed_quota(self):
        # Dê preferência à matéria comentada. Fotos licenciadas são opcionais;
        # não existe exigência artificial de três imagens genéricas por episódio.
        d = copy.deepcopy(self.doc)
        d["context_photos"] = d["context_photos"][:2]
        d["segments"][-1].pop("photo_id")
        validate(d, date(2026, 10, 9))

    def test_contextual_photo_requires_targeted_commentary(self):
        d = copy.deepcopy(self.doc)
        p = d["context_photos"][0]
        p.pop("license")
        p["rights_basis"] = "contextual_quotation"
        with self.assertRaisesRegex(ValueError, "alvo de crítica"):
            validate(d, date(2026, 10, 9))
        p["commentary_target"] = True
        p["quotation_justification"] = "O roteiro comenta esta imagem diretamente, em trecho curto e contextualizado."
        validate(d, date(2026, 10, 9))

    def test_image_is_primary_and_commentary_in_sidebar(self):
        project = transform(self.doc)
        doc_stage = project["scenes"][1]["visual"]["stage"]
        excerpt = next(e for e in doc_stage["elements"] if e["kind"] == "source_excerpt")
        headline = next(e for e in doc_stage["elements"] if e["id"] == "headline")
        self.assertGreaterEqual(excerpt["width"], 55)
        self.assertGreater(excerpt["x"], headline["x"] + headline["width"])
        self.assertEqual(excerpt["surface"], "none")
        self.assertFalse(doc_stage["captions"]["enabled"])

    def test_stable_documentary_while_short_commentary_updates(self):
        project = transform(self.doc)
        stages = [s["visual"]["stage"] for s in project["scenes"]]
        for index, side in ((0, "left"), (1, "right"), (2, "left"), (3, "right")):
            elements = stages[index]["elements"]
            media = next(e for e in elements if e["kind"] in ("photo", "source_excerpt"))
            headline = next(e for e in elements if e["id"] == "headline")
            if side == "left":
                self.assertLess(media["x"] + media["width"], headline["x"])
            else:
                self.assertLess(headline["x"] + headline["width"], media["x"])
            self.assertFalse(stages[index]["captions"]["enabled"])
            self.assertEqual(len(project["scenes"][index]["visual"]["beats"]),
                             min(4, len(self.doc["segments"][index]["visual_cards"])))
            if media["kind"] == "photo":
                self.assertEqual(media["image_motion"], "none")

    def test_separate_publishers_for_displayed_articles(self):
        doc = copy.deepcopy(self.doc)
        doc["documentary_evidence"][1]["source_id"] = doc["documentary_evidence"][0]["source_id"]
        with self.assertRaisesRegex(ValueError, "publicadores independentes"):
            validate(doc, date(2026, 10, 9))

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
        for source in d["sources"]:
            source["url"] = "https://mesmo-portal.example/noticia/" + source["id"]
        with self.assertRaisesRegex(ValueError, "publicadores diferentes"):
            validate(d, date(2026, 10, 9))


if __name__ == "__main__":
    unittest.main()
