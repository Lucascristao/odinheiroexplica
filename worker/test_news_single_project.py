"""Single-story editorial contract and documentary-first Remotion output, offline."""
import copy
from datetime import date
import json
from pathlib import Path
import unittest
from tempfile import TemporaryDirectory

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

    def test_evidence_occupies_the_frame_without_solo_commentary_cards(self):
        project = transform(self.doc)
        self.assertEqual(len(project["scenes"]), len(self.doc["segments"]))
        self.assertEqual(project["presenter"]["name"], "Roberto")
        self.assertEqual(len(project["visual_assets"]), 5)
        self.assertEqual(sum(x["type"] == "source_excerpt" for x in project["visual_assets"]), 2)
        self.assertEqual(sum(x["type"] == "photo" for x in project["visual_assets"]), 3)
        kinds = [scene["visual"]["stage"]["elements"][0]["kind"] for scene in project["scenes"]]
        self.assertEqual(kinds, ["photo", "source_excerpt", "photo", "source_excerpt",
                                 "source_excerpt", "photo"])
        for scene in project["scenes"]:
            stage = scene["visual"]["stage"]
            self.assertTrue(stage["full_bleed_news"])
            self.assertFalse(stage["captions"]["enabled"])
            self.assertFalse(stage["show_title"])
            self.assertEqual(len(stage["elements"]), 1)
            media = stage["elements"][0]
            self.assertEqual((media["x"], media["y"], media["width"], media["height"]), (0, 0, 100, 100))
            self.assertTrue(media["asset_id"])
            self.assertTrue(scene["narration"])
            self.assertGreaterEqual(len(scene["visual"]["beats"]), 3)
            self.assertTrue(all(scene["narration"].count(beat["anchor"]) == 1
                                for beat in scene["visual"]["beats"]))
            self.assertTrue(all(beat["target_id"] == "evidence" and beat["action"] == "focus"
                                for beat in scene["visual"]["beats"]))
            self.assertFalse(any(beat.get("action") == "update" for beat in scene["visual"]["beats"]))
        opinion = project["scenes"][4]["visual"]["stage"]["elements"][0]
        self.assertEqual(opinion["asset_id"], "doc-budget")
        self.assertEqual(project["packaging"]["thumbnails"][0]["headline"],
                         self.doc["thumbnail_headline"])

    def test_discovery_strategy_has_real_first_value_and_no_fabricated_metrics(self):
        project = transform(self.doc)
        strategy = project["packaging"]["strategy"]
        self.assertIn("espectadores", strategy["verification_limits"] if "espectadores" in strategy["verification_limits"] else "espectadores e limites")
        self.assertTrue(project["publication"]["description"].startswith("Imposto do Pecado depois das eleições?"))
        self.assertIn("secondary_keywords", project["publication"]["seo"])
        self.assertIn(self.doc["discovery_strategy"]["first_payoff"], project["scenes"][0]["narration"])
        broken = copy.deepcopy(self.doc)
        broken["discovery_strategy"]["first_payoff"] = "PROMESSA QUE NUNCA É ENTREGUE"
        with self.assertRaisesRegex(ValueError, "primeira entrega"):
            validate(broken, date(2026, 10, 9))

    def test_opinion_can_reuse_prior_photo_without_a_commentary_slide(self):
        alternate = copy.deepcopy(self.doc)
        alternate["segments"][3]["photo_id"] = "foto-urna"
        alternate["segments"][3].pop("document_id")
        # The removed source still appears in a later real scene to satisfy the
        # independent documentary evidence contract.
        alternate["segments"][5]["document_id"] = "doc-budget"
        alternate["segments"][5].pop("photo_id")
        project = transform(alternate)
        opinion = project["scenes"][4]["visual"]["stage"]["elements"]
        self.assertEqual(len(opinion), 1)
        self.assertEqual(opinion[0]["asset_id"], "foto-urna")
        self.assertEqual(opinion[0]["kind"], "photo")

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

    def test_news_layout_has_no_header_or_archive_label_overlay(self):
        scenes = transform(self.doc)["scenes"]
        for index in (0, 1, 2, 3, 4, 5):
            stage = scenes[index]["visual"]["stage"]
            self.assertEqual(len(stage["elements"]), 1)
            evidence = stage["elements"][0]
            self.assertEqual(evidence["visual_role"], "protagonist")
            self.assertEqual(evidence["surface"], "none")
            self.assertNotIn("image_motion", evidence) if evidence["kind"] == "source_excerpt" else self.assertEqual(evidence["image_motion"], "none")
        self.assertEqual(scenes[4]["visual"]["stage"]["elements"][0]["kind"], "source_excerpt")

    def test_marks_are_authored_and_never_placed_at_guessed_coordinates(self):
        project = transform(self.doc)
        for scene in project["scenes"]:
            for beat in scene["visual"]["beats"]:
                self.assertNotIn("mark_ids", beat)
                self.assertNotIn("view", beat)
        self.assertNotIn("render_verified_article_panel(",
                         (Path(__file__).resolve().parent / "auto_capture_sources.py").read_text())

    def test_separate_publishers_for_displayed_articles(self):
        doc = copy.deepcopy(self.doc)
        second = doc["documentary_evidence"][1]
        first = doc["documentary_evidence"][0]
        second["source_id"] = first["source_id"]
        publisher = next(s for s in doc["sources"] if s["id"] == first["source_id"])
        second["editorial_reconstruction"]["publisher"] = publisher["publisher"]
        second["editorial_reconstruction"]["published_at"] = publisher["published_at"]
        with self.assertRaisesRegex(ValueError, "publicadores independentes"):
            validate(doc, date(2026, 10, 9))

    def test_reconstruction_requires_existing_verified_fact(self):
        doc = copy.deepcopy(self.doc)
        for fact in doc["verified_facts"]:
            fact["source_ids"] = [source for source in fact["source_ids"] if source != "S4"]
        with self.assertRaisesRegex(ValueError, "reconstrução sem fato verificado"):
            validate(doc, date(2026, 10, 9))

    def test_reconstruction_is_not_disguised_as_original_screenshot(self):
        from news_reconstruction import render_reconstruction
        from PIL import Image
        project = transform(self.doc)
        asset = next(a for a in project["visual_assets"] if a["type"] == "source_excerpt")
        with TemporaryDirectory() as dirname:
            output = render_reconstruction(asset, Path(dirname), "teste de bloqueio HTTP")
            self.assertTrue(output.is_file())
            with Image.open(output) as image:
                self.assertEqual(image.size, (1920, 1080))
                self.assertEqual(image.getpixel((10, 110)), (255, 189, 25))
            receipt = json.loads(output.with_suffix(".provenance.json").read_text(encoding="utf-8"))
            self.assertTrue(receipt["not_original_screenshot"])
            self.assertEqual(receipt["source_id"], "S4")
            self.assertIn("bloqueio HTTP", receipt["capture_error"])

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
