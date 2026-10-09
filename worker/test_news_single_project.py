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

    def test_documentary_is_primary_in_full_screen_layout(self):
        project = transform(self.doc)
        stage = project["scenes"][1]["visual"]["stage"]
        media = next(e for e in stage["elements"] if e["kind"] == "source_excerpt")
        strip = next(e for e in stage["elements"] if e["id"] == "headline")
        self.assertGreaterEqual(media["width"] * media["height"] / 10000, .84)
        self.assertTrue(stage["full_bleed_news"])
        self.assertGreaterEqual(media["width"], 95)
        self.assertLessEqual(strip["y"] + strip["height"], media["y"])
        self.assertEqual(media["surface"], "none")
        self.assertFalse(stage["captions"]["enabled"])

    def test_documentary_remains_stable_with_light_camera_and_header_updates(self):
        project = transform(self.doc)
        for index in (0, 1, 2, 3):
            scene = project["scenes"][index]
            stage = scene["visual"]["stage"]
            media = next(e for e in stage["elements"] if e["kind"] in ("photo", "source_excerpt"))
            strip = next(e for e in stage["elements"] if e["id"] == "headline")
            self.assertLessEqual(strip["y"] + strip["height"], media["y"])
            self.assertFalse(stage["captions"]["enabled"])
            self.assertEqual(len(scene["visual"]["beats"]),
                             min(4, len(self.doc["segments"][index]["visual_cards"])))
            self.assertTrue(all(b["camera"]["zoom"] <= 1.05 for b in scene["visual"]["beats"]))
            if media["kind"] == "photo":
                self.assertEqual(media["image_motion"], "push")

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

    def test_wide_authentic_excerpt_is_preserved_inside_editorial_page(self):
        from news_reconstruction import render_verified_article_panel
        from PIL import Image, ImageDraw
        project = transform(self.doc)
        asset = next(a for a in project["visual_assets"] if a["type"] == "source_excerpt")
        with TemporaryDirectory() as temp:
            root = Path(temp)
            original = Image.new("RGB", (1000, 190), "#ffffff")
            draw = ImageDraw.Draw(original)
            draw.text((40, 45), "NOTICIA DA FONTE", fill="#222222")
            path = root / Path(asset["capture_file"]).name
            original.save(path)
            result = render_verified_article_panel(asset, root)
            self.assertEqual(result, path)
            with Image.open(result) as image:
                self.assertEqual(image.size, (1920, 1080))
            authentic = result.with_name(result.stem + ".authentic.png")
            self.assertTrue(authentic.exists())
            with Image.open(authentic) as untouched:
                self.assertEqual(untouched.size, (1000, 190))
            receipt = json.loads(result.with_suffix(".provenance.json").read_text())
            self.assertEqual(receipt["kind"], "editorial_presentation_with_authentic_excerpt")
            self.assertEqual(receipt["source_id"], asset["source_id"])

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
