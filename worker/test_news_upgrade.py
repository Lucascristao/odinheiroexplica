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
from news_trigger_guard import editor_identity
from news_render_dispatch import eligible
from news_quality_contract import editorial_fingerprint
from news_single_project import build_scene


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

    def test_approving_model_cannot_invent_quote(self):
        self.review["claim_checks"][0]["evidence"][0]["quote"] = "Um texto parecido mas nunca publicado nesta fonte."
        with self.assertRaisesRegex(ValueError, "absent"):
            validate_review(self.review, self.ep, self.corpus)

    def test_central_event_date_cannot_be_publication_date_only(self):
        self.review["same_day_event_supported"] = False
        with self.assertRaisesRegex(ValueError, "Recency"):
            validate_review(self.review, self.ep, self.corpus)

    def test_missing_claim_review_fails_closed(self):
        self.review["claim_checks"] = []
        with self.assertRaisesRegex(ValueError, "Every"):
            validate_review(self.review, self.ep, self.corpus)

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


if __name__ == "__main__":
    unittest.main()
