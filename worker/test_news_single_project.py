"""Single-story editorial contract and documentary-first Remotion output, offline."""
import copy
import hashlib
from datetime import date
import json
from pathlib import Path
import unittest
from tempfile import TemporaryDirectory

from news_single_project import validate, transform, normalize_documentary_metadata

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

    def test_short_real_documentary_credit_does_not_need_rights_boilerplate(self):
        for credit in ("BBC", "UOL", "Agência Brasil"):
            with self.subTest(credit=credit):
                doc = copy.deepcopy(self.doc)
                evidence = doc["documentary_evidence"][0]
                evidence["attribution"] = credit
                evidence.pop("rights_review", None)
                self.assertIs(validate(doc, date(2026, 10, 9)), doc)
                asset = next(a for a in transform(doc)["visual_assets"] if a["id"] == evidence["id"])
                self.assertEqual(asset["attribution"], credit)

    def test_missing_documentary_metadata_comes_only_from_existing_source(self):
        doc = copy.deepcopy(self.doc)
        evidence = doc["documentary_evidence"][0]
        source = next(s for s in doc["sources"] if s["id"] == evidence["source_id"])
        source["title"] = "Título de fixture da matéria, não uma nova apuração"
        for field in ("kind", "source_page_url", "capture_file", "attribution", "rights_review"):
            evidence.pop(field, None)
        original = copy.deepcopy(doc)
        result = validate(doc, date(2026, 10, 9))
        normalized = result["documentary_evidence"][0]
        self.assertEqual(normalized["kind"], "source_excerpt")
        self.assertEqual(normalized["source_page_url"], source["url"])
        self.assertEqual(normalized["capture_file"], f"research/captures/{evidence['id']}.png")
        self.assertEqual(normalized["attribution"], source["publisher"] + "; " + source["title"])
        self.assertNotIn("rights_review", normalized)
        self.assertEqual(normalized["expected_text"], original["documentary_evidence"][0]["expected_text"])
        self.assertEqual(doc, original)
        self.assertTrue(transform(doc)["visual_assets"][0]["attribution"])

    def test_metadata_never_fills_an_unknown_source_or_missing_source_url(self):
        for field in ("source_id", "url"):
            with self.subTest(field=field):
                doc = copy.deepcopy(self.doc)
                evidence = doc["documentary_evidence"][0]
                evidence.pop("source_page_url", None)
                evidence.pop("attribution", None)
                if field == "source_id":
                    evidence["source_id"] = "absent-source"
                else:
                    source = next(s for s in doc["sources"] if s["id"] == evidence["source_id"])
                    source.pop("url")
                self.assertNotIn("source_page_url", normalize_documentary_metadata(doc)["documentary_evidence"][0])
                with self.assertRaises(ValueError):
                    validate(doc, date(2026, 10, 9))

    def test_metadata_cannot_replace_a_missing_quote_or_mismatched_url(self):
        doc = copy.deepcopy(self.doc)
        doc["documentary_evidence"][0].pop("expected_text")
        with self.assertRaisesRegex(ValueError, "texto verificável"):
            validate(doc, date(2026, 10, 9))
        doc = copy.deepcopy(self.doc)
        doc["documentary_evidence"][0]["source_page_url"] = "https://example.com/unrelated-document"
        with self.assertRaisesRegex(ValueError, "URL da fonte vinculada"):
            validate(doc, date(2026, 10, 9))

    def test_missing_credit_and_unknown_publisher_remain_actionable_error(self):
        doc = copy.deepcopy(self.doc)
        evidence = doc["documentary_evidence"][0]
        evidence.pop("attribution")
        source = next(s for s in doc["sources"] if s["id"] == evidence["source_id"])
        source.pop("publisher")
        with self.assertRaisesRegex(ValueError, "attribution ou publisher real"):
            validate(doc, date(2026, 10, 9))

    def test_historical_transform_hash_and_input_are_unchanged(self):
        doc = copy.deepcopy(self.doc)
        self.assertIs(normalize_documentary_metadata(doc), doc)
        payload = json.dumps(transform(doc), ensure_ascii=False, sort_keys=True).encode()
        self.assertEqual(hashlib.sha256(payload).hexdigest(),
                         "31ecb47781c1078b3a90c06ae5dee00383d84c200c5d47e562c9d9c0fcb4bb18")
        self.assertEqual(doc, self.doc)

    def current_selection_fixture(self):
        # Contract fixture only; these edits are never saved as a news episode.
        doc = copy.deepcopy(self.doc)
        doc.update(episode_id="noticia-2026-10-11-selection-fixture", news_date="2026-10-11",
                   event_date="2026-10-11", editorial_status="autonomous_fact_checked",
                   reviewed_at="2026-10-11T18:00:00-03:00")
        fact = doc["verified_facts"][0]
        fact.update(event_date="2026-10-11", status="confirmed",
                    source_ids=list(dict.fromkeys(fact["source_ids"]
                                                  + [source["id"] for source in doc["sources"][:2]])))
        for source in doc["sources"][:2]:
            source["published_at"] = "2026-10-11"
        for asset in doc["documentary_evidence"]:
            if asset.get("editorial_reconstruction"):
                source = next(s for s in doc["sources"] if s["id"] == asset["source_id"])
                asset["editorial_reconstruction"]["published_at"] = source["published_at"]
        doc["news_selection"] = {
            "topic_area": "politics",
            "new_fact": fact["claim"],
            "why_today": "A decisão foi divulgada hoje; o documento e a reportagem confirmam a mudança.",
            "opening_anchor": doc["segments"][0]["narration"][:100],
        }
        return doc

    def test_new_autonomous_review_requires_dated_selection(self):
        doc = self.current_selection_fixture()
        del doc["news_selection"]
        with self.assertRaisesRegex(ValueError, "news_selection"):
            validate(doc, date(2026, 10, 11))

    def test_today_article_does_not_refresh_an_old_event(self):
        doc = self.current_selection_fixture()
        doc["event_date"] = "2026-10-08"
        with self.assertRaisesRegex(ValueError, "reportagem recente não renova fato antigo"):
            validate(doc, date(2026, 10, 11))
        doc["event_date"] = "2026-10-11"
        doc["verified_facts"][0]["event_date"] = "2026-10-08"
        with self.assertRaisesRegex(ValueError, "data do acontecimento"):
            validate(doc, date(2026, 10, 11))

    def test_new_event_needs_current_evidence_from_two_publishers(self):
        doc = self.current_selection_fixture()
        for source in doc["sources"]:
            source["published_at"] = "2026-10-08"
        with self.assertRaisesRegex(ValueError, "fonte publicada no dia"):
            validate(doc, date(2026, 10, 11))
        doc = self.current_selection_fixture()
        doc["verified_facts"][0]["source_ids"] = [doc["sources"][0]["id"]]
        with self.assertRaisesRegex(ValueError, "dois publicadores"):
            validate(doc, date(2026, 10, 11))

    def test_selection_cannot_use_unlinked_fact_or_missing_opening(self):
        doc = self.current_selection_fixture()
        doc["news_selection"]["new_fact"] = "Uma novidade declarada sem nenhum fato verificado correspondente."
        with self.assertRaisesRegex(ValueError, "único verified_fact"):
            validate(doc, date(2026, 10, 11))
        doc = self.current_selection_fixture()
        doc["news_selection"]["opening_anchor"] = "A novidade ficou fora da abertura do vídeo."
        with self.assertRaisesRegex(ValueError, "abertura"):
            validate(doc, date(2026, 10, 11))

    def test_politics_with_current_development_keeps_older_context(self):
        doc = self.current_selection_fixture()
        # A dated central development can use yesterday's primary document and
        # today's reporting; background remains available within its old window.
        doc["sources"][0]["published_at"] = "2026-10-10"
        for asset in doc["documentary_evidence"]:
            if asset.get("editorial_reconstruction") and asset["source_id"] == doc["sources"][0]["id"]:
                asset["editorial_reconstruction"]["published_at"] = "2026-10-10"
        validate(doc, date(2026, 10, 11))
        self.assertEqual(transform(doc)["editorial"]["news_selection"], doc["news_selection"])

    def test_historical_review_keeps_its_contract_when_resumed_later(self):
        doc = self.current_selection_fixture()
        del doc["news_selection"]
        doc["reviewed_at"] = "2026-10-11T17:59:59-03:00"
        doc["event_date"] = "2026-10-08"
        validate(doc, date(2026, 10, 15))
        self.assertNotIn("news_selection", transform(doc)["editorial"])

    def test_context_and_expression_cutover_preserve_reviewed_historical_project(self):
        root=Path(__file__).resolve().parents[1]
        historical=json.loads((root/'news/episodes/2026-10-11-melhorias-producao.json').read_text(encoding='utf-8'))
        approved=json.loads((root/'production/noticia-2026-10-11-melhorias-producao/thumbnail-audit.json').read_text(encoding='utf-8'))
        project=transform(historical)
        serialized=(json.dumps(project,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        self.assertEqual(hashlib.sha256(serialized).hexdigest(),approved['project_sha256'])
        future=copy.deepcopy(historical)
        future['reviewed_at']='2026-10-11T02:05:00-03:00'
        updated=transform(future)
        self.assertEqual(updated['packaging']['thumbnails'][0]['contract']['presenter_identity']['id'],'roberto-v1-engaged')
        self.assertEqual(updated['packaging']['thumbnails'][0]['concept'],
                         future['thumbnail_primary'] + ' ' + future['thumbnail_tension'])
        self.assertTrue(all(a['capture_scope']=='desktop_context' for a in updated['visual_assets'] if a['type']=='source_excerpt'))
        self.assertTrue(all(s['visual']['stage']['elements'][0]['document_context_seconds']==1.6 for s in updated['scenes']))

    def test_authored_cues_require_literal_order_and_pinned_capture(self):
        doc=copy.deepcopy(self.doc)
        segment=doc["segments"][1]
        literal=segment["narration"][:45]
        segment["visual_cues"]=[{"anchor":literal,"view":{"x":0,"y":0,"width":100,"height":100}}]
        with self.assertRaisesRegex(ValueError,"captura autêntica"):
            validate(doc,date(2026,10,9))
        asset=next(d for d in doc["documentary_evidence"] if d["id"]==segment["document_id"])
        asset["capture_sha256"]="a"*64
        project=transform(doc)
        self.assertEqual(project["scenes"][1]["visual"]["beats"][0]["anchor"],literal)
        self.assertEqual(next(a for a in project["visual_assets"] if a["id"]==asset["id"])["capture_sha256"],"a"*64)
        segment["visual_cues"][0]["anchor"]="Fala inventada que não existe no roteiro."
        with self.assertRaisesRegex(ValueError,"trecho literal"):
            validate(doc,date(2026,10,9))

    def test_titles_must_be_distinct_and_chosen_from_highest_ranked_option(self):
        base = copy.deepcopy(self.doc)
        validate(base, date(2026, 10, 9))
        duplicates = copy.deepcopy(base)
        duplicates["title_options"][1]["text"] = duplicates["title_options"][0]["text"]
        with self.assertRaisesRegex(ValueError, "diferentes"):
            validate(duplicates, date(2026, 10, 9))
        missing = copy.deepcopy(base)
        missing["title"] = "Imposto seletivo anunciado com outro título que não foi avaliado"
        with self.assertRaisesRegex(ValueError, "não corresponde"):
            validate(missing, date(2026, 10, 9))
        not_best = copy.deepcopy(base)
        not_best["title_options"][1]["editorial_quality"] = 5
        not_best["title_options"][0]["editorial_quality"] = 4
        with self.assertRaisesRegex(ValueError, "melhor alternativa"):
            validate(not_best, date(2026, 10, 9))

    def test_ambiguous_audio_anchors_fail_before_synthesis(self):
        # These are literal, case-sensitive matches once, but audio alignment
        # normalizes their other occurrence. Reject before spending on voice.
        for repeated in ("ATENÇÃO AO PREÇO", "Atencao ao preco", "Atenção   ao preço"):
            with self.subTest(repeated=repeated):
                doc = copy.deepcopy(self.doc)
                segment = doc["segments"][1]
                segment["narration"] += " Atenção ao preço. " + repeated + " pode variar."
                segment["visual_cues"] = [{"anchor": "Atenção ao preço"}]
                with self.assertRaisesRegex(ValueError, "normalização"):
                    validate(doc, date(2026, 10, 9))
                segment["visual_cues"] = [{"anchor": "Atenção ao preço."}]
                validate(doc, date(2026, 10, 9))

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
        self.assertIn("CTR", strategy["verification_limits"])
        self.assertGreaterEqual(len(strategy["viewer_intent"]), 30)
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
        second["source_page_url"] = publisher["url"]
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
                self.assertEqual(image.getpixel((10, 6)), (255, 189, 25))
                self.assertEqual(image.getpixel((10, 110)), (246, 245, 240))
                self.assertEqual(image.getpixel((1900, 1045)), (246, 245, 240))
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
