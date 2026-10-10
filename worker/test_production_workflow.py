"""Offline guards for fail-fast layout gates and useful retry diagnostics."""

from pathlib import Path
import re
import unittest


WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"


def read_steps(filename: str) -> list[str]:
    workflow = (WORKFLOWS / filename).read_text(encoding="utf-8")
    return re.split(r"(?m)^      - name: ", workflow)[1:]


def step_index(steps: list[str], marker: str) -> int:
    matches = [index for index, step in enumerate(steps) if marker in step]
    if len(matches) != 1:
        raise AssertionError(f"Expected one step containing {marker!r}, got {len(matches)}")
    return matches[0]


class ProductionWorkflowTests(unittest.TestCase):
    def test_shell_blocks_do_not_join_commands_with_literal_newline_text(self):
        for path in WORKFLOWS.glob("*.yml"):
            with self.subTest(workflow=path.name):
                self.assertIsNone(re.search(
                    r"\\n[ \t]+(?:python|npm|npx|gh)\s", path.read_text(encoding="utf-8")
                ), "Uma quebra de linha literal uniu dois comandos de produção")

    def test_ci_checks_the_current_episode_before_audio_dependencies(self):
        steps = read_steps("ci.yml")
        geometry = step_index(steps, "--mode geometry-only")
        self.assertLess(step_index(steps, "--require-explanation"), geometry)
        self.assertLess(geometry, step_index(steps, "pip install"))
        self.assertIn("--project video/generated/daily-project.json", steps[geometry])
        self.assertNotIn("continue-on-error", steps[geometry])

    def test_production_blocks_early_and_checks_assets_before_paid_synthesis(self):
        steps = read_steps("render-daily.yml")
        geometry = step_index(steps, "--mode geometry-only")
        assets = step_index(steps, "id: layout_assets")
        synthesis = step_index(steps, "python worker/synthesize_scenes.py")
        final = step_index(steps, "id: layout_final")
        self.assertLess(geometry, step_index(steps, "Install system dependencies"))
        self.assertLess(geometry, step_index(steps, "pip install"))
        self.assertLess(step_index(steps, "python worker/prepare_visual_assets.py"), assets)
        self.assertLess(assets, synthesis)
        self.assertLess(synthesis, final)
        self.assertIn("--visual-assets-manifest", steps[assets])
        self.assertIn("--render-input", steps[final])
        for index in (geometry, assets, final):
            self.assertNotIn("continue-on-error", steps[index])

    def test_early_failure_reports_are_uploaded_even_when_the_gate_fails(self):
        for filename in ("ci.yml", "render-daily.yml"):
            with self.subTest(workflow=filename):
                steps = read_steps(filename)
                uploads = [step for step in steps if "actions/upload-artifact@v4" in step
                           and "daily-layout-geometry.json" in step]
                self.assertTrue(uploads)
                self.assertTrue(all("always()" in step for step in uploads))
                self.assertTrue(all("render-output/layout-geometry/" in step for step in uploads))

    def test_runner_tools_are_reused_and_capture_browser_is_conditional(self):
        for filename in ("ci.yml", "render-daily.yml"):
            with self.subTest(workflow=filename):
                steps = read_steps(filename)
                system = next(step for step in steps if "apt-get install" in step)
                self.assertIn("command -v ffmpeg", system)
                self.assertIn("command -v ffprobe", system)
                self.assertNotIn('echo "$MEDIA_BIN" >> "$GITHUB_PATH"', system)
                self.assertIn("full pipeline needs stock FFmpeg", system)
                self.assertLess(system.index("command -v ffmpeg"), system.index("apt-get update"))
                self.assertNotIn("--no-cache-dir", "\n".join(steps))
        production = read_steps("render-daily.yml")
        browser = production[step_index(production, "python -m playwright install chromium")]
        self.assertIn("steps.capture.outputs.required == 'true'", browser)
        self.assertNotIn("--with-deps", browser)


if __name__ == "__main__":
    unittest.main()
