"""Offline regression coverage for seven slots and source-backed longer news."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
from news_schedule import load_config, slots, nominal_occurrence, editorial_window
from news_production_gate import validate_production
from news_editorial_quality import validate_review, develop
from news_editorial_quality import reference_passages, bind_review_passages
from news_editorial_quality import apply_editorial_corrections
from news_trigger_guard import editor_identity
from news_render_dispatch import eligible
from news_quality_contract import editorial_fingerprint
from news_single_project import build_scene
from news_editor_state import read_state, save_state, discard_state
import news_groq_client as groq
import tempfile
from unittest.mock import Mock


class SevenSlots(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_distribution_and_unique_targets(self):
        schedule = slots(self.config)
        self.assertEqual(len(schedule), 7)
        self.assertEqual([sum(row["period"] == period for row in schedule.values())
                          for period in ("manha", "tarde", "noite")], [2, 2, 3])
        self.assertEqual(len({row["publication"] for row in schedule.values()}), 7)

    def test_every_cron_and_delayed_run_keep_exact_slot(self):
        for name, row in slots(self.config).items():
            for cron in row["crons_utc"]:
                minute, hour = map(int, cron.split()[:2])
                nominal = datetime(2026, 11, 10, hour, minute, tzinfo=timezone.utc)
                from datetime import timedelta
                for delay in (0, 75, 260):
                    created = (nominal + timedelta(minutes=delay)).isoformat()
                    self.assertEqual(nominal_occurrence(cron, created, self.config), ("2026-11-10", name))
                    run = {"display_title": "ODE editor | automatico | " + cron,
                           "event": "schedule", "created_at": created}
                    self.assertEqual(editor_identity(run, self.config), ("2026-11-10", name))

    def test_late_editor_is_refused_before_api_spend(self):
        late = datetime(2026, 11, 10, 23, 30, tzinfo=timezone.utc)
        active, _, _ = editorial_window(self.config, "2026-11-10", "manha", late)
        self.assertFalse(active)

    def test_render_dispatch_understands_all_seven_paths(self):
        from zoneinfo import ZoneInfo
        for slot, row in slots(self.config).items():
            now = datetime.fromisoformat("2026-11-10T" + row["production"]).replace(tzinfo=ZoneInfo(self.config["timezone"]))
            ep = {"episode_id": "noticia-2026-11-10-" + slot, "news_date": "2026-11-10",
                  "editorial_status": "autonomous_fact_checked",
                  "publication_target_local": "2026-11-10T" + row["publication"] + ":00-03:00"}
            self.assertIsNone(eligible("news/episodes/2026-11-10-" + slot + ".json", ep, self.config, now))

    def test_workflow_and_config_crons_cannot_drift(self):
        import yaml
        root = Path(__file__).parents[1]
        workflow = yaml.safe_load((root / ".github/workflows/news-autonomous-editor.yml").read_text(encoding="utf-8"))
        triggers = workflow.get("on", workflow.get(True))
        self.assertEqual({item["cron"] for item in triggers["schedule"]},
                         {cron for row in slots(self.config).values() for cron in row["crons_utc"]})
        self.assertEqual(set(triggers["workflow_dispatch"]["inputs"]["slot"]["options"]), set(slots(self.config)))


class SourceReview(unittest.TestCase):
    def setUp(self):
        self.ep = {"verified_facts": [{"claim": "Fixture test claim", "source_ids": ["S1"]}]}
        self.corpus = {"S1": {"text": "Na data de hoje o órgão publicou o resultado com condições expressas."}}
        quote = self.corpus["S1"]["text"]
        self.review = {"approved": True, "issues": [], "same_day_event_supported": True,
                       "title_opening_delivered": True, "event_date_evidence": {"source_id": "S1", "quote": quote},
                       "claim_checks": [{"claim_index": 0, "supported": True,
                                         "evidence": [{"source_id": "S1", "quote": quote}]}]}

    def test_complete_literal_support_can_pass(self):
        validate_review(self.review, self.ep, self.corpus)

    def test_positive_model_verdict_cannot_override_yesterdays_event(self):
        quote = 'Na petição, protocolada nesta segunda-feira, 9, a defesa fez o pedido.'
        self.ep['news_date'] = '2026-11-10'
        self.corpus['S1']['text'] += ' ' + quote
        self.review['event_date_evidence']['quote'] = quote
        with self.assertRaisesRegex(ValueError, 'contradicts'):
            validate_review(self.review, self.ep, self.corpus)
        self.assertIs(self.review['same_day_event_supported'], False)
        self.assertIs(self.review['approved'], False)

    def test_facts_list_approval_does_not_cover_unreviewed_narration(self):
        self.ep['segments'] = [{'id': 'seg-1', 'type': 'opinion', 'narration': 'Na minha análise, um recurso ao CNJ muda a decisão.'}]
        with self.assertRaisesRegex(ValueError, 'Every narration'):
            validate_review(self.review, self.ep, self.corpus)
        self.review['narration_checks'] = [{'segment_id': 'seg-1', 'supported': False,
            'has_factual_assertions': True, 'unsupported_assertions': ['um recurso ao CNJ muda a decisão.'], 'evidence': []}]
        with self.assertRaisesRegex(ValueError, 'Unsupported assertion'):
            validate_review(self.review, self.ep, self.corpus)

    def test_supported_narration_and_pure_opinion_have_distinct_source_needs(self):
        self.ep['segments'] = [{'id': 'fact', 'type': 'fact'}, {'id': 'opinion', 'type': 'opinion'}]
        self.review['narration_checks'] = [
            {'segment_id': 'fact', 'supported': True, 'has_factual_assertions': True,
             'unsupported_assertions': [], 'evidence': self.review['claim_checks'][0]['evidence']},
            {'segment_id': 'opinion', 'supported': True, 'has_factual_assertions': False,
             'unsupported_assertions': [], 'evidence': []}]
        validate_review(self.review, self.ep, self.corpus)
        self.review['narration_checks'][0]['evidence'] = []
        with self.assertRaisesRegex(ValueError, 'need source evidence'):
            validate_review(self.review, self.ep, self.corpus)

    def test_review_can_add_support_from_another_fetched_source(self):
        self.corpus["S2"] = {"text": "Outra fonte consultada confirma o resultado e suas condições."}
        self.review["claim_checks"][0]["evidence"] = [{"source_id": "S2", "quote": self.corpus["S2"]["text"]}]
        validate_review(self.review, self.ep, self.corpus)
        self.assertEqual(self.ep["verified_facts"][0]["source_ids"], ["S1", "S2"])

    def test_unfetched_source_cannot_be_added_by_review(self):
        self.review["claim_checks"][0]["evidence"][0]["source_id"] = "S99"
        with self.assertRaisesRegex(ValueError, "absent"):
            validate_review(self.review, self.ep, self.corpus)

    def test_approving_model_cannot_invent_quote(self):
        self.review["claim_checks"][0]["evidence"][0]["quote"] = "Um texto parecido mas nunca publicado nesta fonte."
        with self.assertRaisesRegex(ValueError, "absent"):
            validate_review(self.review, self.ep, self.corpus)

    def test_central_event_date_cannot_be_publication_date_only(self):
        self.review["same_day_event_supported"] = False
        with self.assertRaisesRegex(ValueError, "Recency"):
            validate_review(self.review, self.ep, self.corpus)

    def test_missing_date_pointer_is_a_recoverable_validation_error_not_a_crash(self):
        self.review['event_date_evidence'] = None
        with self.assertRaisesRegex(ValueError, 'Event date'):
            validate_review(bind_review_passages(self.review, {}), self.ep, self.corpus)

    def test_missing_claim_review_fails_closed(self):
        self.review["claim_checks"] = []
        with self.assertRaisesRegex(ValueError, "Every"):
            validate_review(self.review, self.ep, self.corpus)

    def test_passage_ids_can_be_strings_without_retyping_source_quotes(self):
        _, lookup = reference_passages(self.corpus)
        result = {"approved": "true", "issues": [], "same_day_event_supported": True,
                  "title_opening_delivered": True, "event_date_evidence": "S1-P1",
                  "claim_checks": [{"claim_index": "0", "supported": "true", "evidence": ["S1-P1"]}]}
        validate_review(bind_review_passages(result, lookup), self.ep, self.corpus)

    def test_review_issues_block_even_when_model_sets_approved(self):
        self.review["issues"] = ["Fixture number lacks comparable denominator"]
        with self.assertRaisesRegex(ValueError, "rejected"):
            validate_review(self.review, self.ep, self.corpus)

    def test_style_warnings_do_not_block_supported_reporting(self):
        self.review["warnings"] = ["Fixture: roteiro poderia ser mais longo ou usar outro enquadramento"]
        validate_review(self.review, self.ep, self.corpus)

    def test_word_target_is_not_a_publication_block(self):
        episode = {"episode_id": "noticia-2026-11-10-manha", "news_date": "2026-11-10",
                   "editorial_status": "autonomous_fact_checked", "segments": [{"narration": "fixture " * 420}]}
        episode["editorial_quality"] = {"version": "2026-11-10.1", "narration_word_count": 420,
            "reviewed_content_sha256": editorial_fingerprint(episode), "review": {"approved": True, "issues": []}}
        validate_production(episode, load_config(), datetime(2026, 11, 10, 9, tzinfo=timezone.utc))

    def test_short_script_cannot_enter_new_production(self):
        ep = {"episode_id": "noticia-2026-11-10-manha", "news_date": "2026-11-10",
              "editorial_status": "autonomous_fact_checked", "segments": [{"narration": "palavra " * 180}]}
        with self.assertRaisesRegex(ValueError, "developed"):
            validate_production(ep, load_config(), datetime(2026, 11, 10, 9, tzinfo=timezone.utc))

    def test_archive_keeps_existing_contract(self):
        validate_production({"news_date": "2026-10-12", "editorial_status": "autonomous_fact_checked"},
                            load_config(), datetime(2026, 11, 10, tzinfo=timezone.utc))

    def test_review_binding_changes_with_narration_or_packaging(self):
        ep = {"title": "Fixture title", "segments": [{"narration": "Texto de teste"}]}
        original = editorial_fingerprint(ep)
        ep["segments"][0]["narration"] += " alterado"
        self.assertNotEqual(original, editorial_fingerprint(ep))
        original = editorial_fingerprint(ep)
        ep["title"] += " alterado"
        self.assertNotEqual(original, editorial_fingerprint(ep))

    def test_long_scene_has_cues_throughout_its_narration(self):
        # Distinct test tokens ensure every cue remains unique after alignment normalization.
        narration = " ".join("termo" + str(i) for i in range(120))
        segment = {"narration": narration, "title": "Fixture", "type": "fact", "label": "Prova",
                   "headline": "Fixture documental", "metric": "Dado", "document_id": "doc-1",
                   "visual_cards": ["Destaque inicial", "Destaque central", "Destaque final"]}
        old = build_scene(0, segment)
        developed = build_scene(0, segment, developed=True)
        self.assertEqual(len(old["visual"]["beats"]), 3)
        self.assertGreater(len(developed["visual"]["beats"]), 8)
        self.assertIn("termo110", developed["visual"]["beats"][-1]["anchor"])

    def test_brief_supported_scene_uses_real_cue_without_artificial_padding(self):
        segment = {'narration': 'Esse é o limite do dado apurado.', 'title': 'Limite', 'type': 'fact',
                   'document_id': 'doc-1', 'visual_cards': ['Prova real']}
        scene = build_scene(0, segment, developed=True)
        self.assertEqual(len(scene['visual']['beats']), 1)
        self.assertIn(scene['visual']['beats'][0]['anchor'], segment['narration'])


class AutonomousRecovery(unittest.TestCase):
    def test_scene_development_resumes_without_rewriting_completed_voice_text(self):
        ep = {"segments": [{"id": "one", "type": "opening", "title": "Abertura", "narration": "Preservado", "document_id": "doc1"},
                           {"id": "two", "type": "fact", "title": "Detalhe", "narration": "Rascunho", "document_id": "doc1"}],
              "verified_facts": [], "documentary_evidence": [{"id": "doc1", "source_id": "S1"}],
              "news_selection": {"opening_anchor": "Preservado"}, "discovery_strategy": {"first_payoff": "Preservado"}}
        with patch("news_editorial_quality.parse_reply", return_value={"narration": "Explicação desenvolvida com respaldo."}) as writer:
            develop(ep, {"S1": {"text": "Fonte real de teste."}}, completed_ids={"one"})
        self.assertEqual(writer.call_count, 1)
        self.assertEqual(ep["segments"][0]["narration"], "Preservado")
        self.assertEqual(ep["segments"][1]["narration"], "Explicação desenvolvida com respaldo.")

    def test_editorial_repair_cannot_fake_dates_or_sources(self):
        ep = {"title": "Fixture", "thumbnail_headline": "Fixture", "segments": [],
              "verified_facts": [{"claim": "Central"}, {"claim": "Secondary"}], "news_selection": {"new_fact": "Central"}}
        with self.assertRaisesRegex(ValueError, "dates, sources"):
            apply_editorial_corrections(ep, {"corrections": [{"field": "event_date", "replacement": "2026-11-10"}]})
        self.assertIsNone(apply_editorial_corrections(ep, {"remove_fact_indexes": [0]}))
        fixed = apply_editorial_corrections(ep, {"corrections": [{"field": "thumbnail_headline", "replacement": "Fato comprovado"}]})
        self.assertEqual(fixed["thumbnail_headline"], "Fato comprovado")
        self.assertNotIn("editorial_quality", fixed)

    def test_unverified_checkpoint_never_crosses_edition_or_day(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / "state.json"
            save_state(path, "2026-11-10", "manha", "Fixture unverified report", {"title": "Fixture"}, {"scene-1"})
            state = read_state(path, "2026-11-10", "manha")
            self.assertIs(state["factual_approval"], False)
            self.assertEqual(state["developed_segment_ids"], ["scene-1"])
            self.assertIsNone(read_state(path, "2026-11-11", "manha"))
            self.assertIsNone(read_state(path, "2026-11-10", "noite"))
            legacy = json.loads(path.read_text(encoding='utf-8'))
            legacy['version'] = '1.0'
            path.write_text(json.dumps(legacy), encoding='utf-8')
            self.assertIsNone(read_state(path, '2026-11-10', 'manha'))
            discard_state(path)
            self.assertIsNone(read_state(path, "2026-11-10", "manha"))

    def test_primary_quota_uses_editorial_backup_without_google(self):
        limited = Mock(status_code=429, headers={"retry-after": "900"})
        success = Mock(status_code=200, headers={})
        success.json.return_value = {"choices": [{"finish_reason": "stop", "message": {"content": '{"ok":true}'}}], "usage": {}}
        diag = {}
        with patch.dict(groq.os.environ, {"GROQ_API_KEY": "unit-test-fixture", "ODE_NEWS_GROQ_MODEL": groq.MODEL,
                "ODE_NEWS_GROQ_FALLBACK_MODELS": "openai/gpt-oss-20b", "ODE_NEWS_GROQ_MIN_INTERVAL_SECONDS": "0"}), \
             patch.object(groq.requests, "post", side_effect=[limited, success]) as post, \
             patch.object(groq.time, "sleep"):
            self.assertEqual(json.loads(groq.complete("Fixture transport test", json_mode=True, diagnostics=diag)), {"ok": True})
        self.assertEqual(post.call_args_list[0].kwargs["json"]["model"], groq.MODEL)
        self.assertEqual(post.call_args_list[1].kwargs["json"]["model"], "openai/gpt-oss-20b")
        self.assertEqual(diag["fallback_from"], groq.MODEL)
        messages = post.call_args_list[0].kwargs["json"]["messages"]
        self.assertIn("json", " ".join(message["content"] for message in messages).lower())


if __name__ == "__main__":
    unittest.main()
