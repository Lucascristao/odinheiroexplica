"""Recovery regressions: delayed cron completion must recover only live slots."""
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from news_schedule import load_config
from news_trigger_guard import EDITOR, plan_slot, run_watchdog


class Inventory:
    def __init__(self, editors=None, exists=False, upload=None, renders=None):
        self.editors = editors or []
        self.exists = exists
        self.upload = upload
        self.renders = renders or []
        self.dispatched = []

    def episode_exists(self, path):
        return self.exists

    def runs(self, workflow, day, zone):
        return self.editors if workflow == EDITOR else self.renders

    def upload_for_episode(self, runs, project_id):
        return self.upload

    def dispatch_editor(self, day, slot):
        self.dispatched.append((day, slot))
        # GitHub has accepted this run; the next slot sees the queued editor.
        self.editors.append({"id": 22, "status": "queued"})


class TriggerRecovery(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.now = datetime(2026, 11, 10, 18, 20, tzinfo=timezone.utc)
        self.delayed_morning = {"id": 11, "event": "schedule", "status": "completed",
            "conclusion": "success", "display_title": "ODE editor | automatico | 48 8 * * *",
            "created_at": "2026-11-10T16:36:57Z", "updated_at": "2026-11-10T16:37:10Z"}

    def test_delayed_morning_success_does_not_complete_missing_lunch(self):
        self.config.pop('recovery_policy')
        api = Inventory([self.delayed_morning])
        result = run_watchdog(api, self.config, self.now, dry_run=False)
        self.assertEqual(api.dispatched, [("2026-11-10", "meio-dia")])
        states = {row["slot"]: row["state"] for row in result["slots"]}
        self.assertEqual(states["manha"], "outside")
        self.assertEqual(states["manha-2"], "outside")
        self.assertEqual(states["meio-dia"], "dispatch")
        self.assertEqual(states["tarde"], "deferred")

    def test_unlimited_old_failure_does_not_starve_untried_lunch(self):
        failed = {'id': 12, 'status': 'completed', 'conclusion': 'failure', 'run_attempt': 12,
                  'display_title': 'ODE editor | 2026-11-10 | manha-2', 'created_at': '2026-11-10T15:00:00Z'}
        api = Inventory([self.delayed_morning, failed])
        run_watchdog(api, self.config, self.now, dry_run=False)
        self.assertEqual(api.dispatched, [('2026-11-10', 'meio-dia')])

    def test_no_new_editor_after_remaining_production_budget(self):
        self.config.pop('recovery_policy')  # Archived policy stays unchanged.
        late = self.now.replace(hour=18, minute=41)
        result = plan_slot(Inventory(), self.config, "meio-dia", late)
        self.assertEqual(result["state"], "outside")

    def test_active_editor_never_duplicates_work(self):
        result = plan_slot(Inventory([{"id": 33, "status": "in_progress"}]),
                           self.config, "meio-dia", self.now)
        self.assertEqual(result["state"], "active")

    def test_render_of_other_identified_edition_does_not_block_next_editor(self):
        render = {'id': 44, 'status': 'in_progress',
                  'display_title': 'ODE render | news/episodes/2026-11-10-noite-1.json'}
        result = plan_slot(Inventory(renders=[render]), self.config, 'meio-dia', self.now)
        self.assertEqual(result['state'], 'missing')

    def test_own_or_unknown_render_still_prevents_duplicate_editor(self):
        for title in ('ODE render | news/episodes/2026-11-10-meio-dia.json', 'ODE render | legacy-sha'):
            render = {'id': 44, 'status': 'in_progress', 'display_title': title}
            self.assertEqual(plan_slot(Inventory(renders=[render]), self.config, 'meio-dia', self.now)['state'], 'active')

    def test_committed_episode_is_delegated_without_new_editor(self):
        result = plan_slot(Inventory(exists=True), self.config, "meio-dia", self.now)
        self.assertEqual(result["state"], "delegated_to_render")

    def test_existing_upload_cannot_be_replaced(self):
        result = plan_slot(Inventory(upload={"video_id": "original123", "run_id": 5}),
                           self.config, "meio-dia", self.now)
        self.assertEqual(result["reason"], "exact_episode_upload_receipt")

    def test_event_recovery_cannot_bypass_retry_limit(self):
        self.config.pop('recovery_policy')
        failed = {"status": "completed", "conclusion": "failure", "id": 5,
            "display_title": "ODE editor | 2026-11-10 | meio-dia",
            "created_at": "2026-11-10T15:00:00Z", "run_attempt": 3}
        self.assertEqual(plan_slot(Inventory([failed]), self.config, "meio-dia", self.now)["state"], "maxattempt")

    def test_current_policy_recovers_late_lunch_after_many_failures(self):
        failed = {"status": "completed", "conclusion": "failure", "id": 5,
            "display_title": "ODE editor | 2026-11-10 | meio-dia",
            "created_at": "2026-11-10T15:00:00Z", "run_attempt": 12}
        late = self.now.replace(hour=23, minute=20)  # 20:20 Fortaleza
        result = plan_slot(Inventory([failed]), self.config, "meio-dia", late)
        self.assertEqual(result['state'], 'missing')
        self.assertEqual(result['attempts'], 12)

    def test_unlimited_attempts_still_keep_cooldown(self):
        failed = {"status": "completed", "conclusion": "failure", "id": 5,
            "display_title": "ODE editor | 2026-11-10 | meio-dia",
            "created_at": "2026-11-10T18:15:00Z", "run_attempt": 12}
        self.assertEqual(plan_slot(Inventory([failed]), self.config, 'meio-dia', self.now)['state'], 'cooldown')

    def test_workflow_completion_is_independent_of_cron_and_dry_run(self):
        import yaml
        root = Path(__file__).parents[1]
        path = root / ".github/workflows/news-trigger-watchdog.yml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        triggers = data.get("on", data.get(True))
        completed = triggers["workflow_run"]
        self.assertEqual(completed["branches"], ["main"])
        self.assertEqual(completed["types"], ["completed"])
        self.assertNotIn(data["name"], completed["workflows"])
        for filename in ("news-autonomous-editor.yml", "render-news-single.yml"):
            source = yaml.safe_load((path.parent / filename).read_text(encoding="utf-8"))
            self.assertIn(source["name"], completed["workflows"])
        step = next(s for s in data["jobs"]["guard"]["steps"] if "EXECUTE" in s.get("env", {}))
        self.assertIn("github.event_name == 'workflow_run'", step["env"]["EXECUTE"])
        self.assertIn("head_repository.full_name == github.repository", data["jobs"]["guard"]["if"])


if __name__ == "__main__":
    unittest.main()
