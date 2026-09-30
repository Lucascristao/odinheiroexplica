"""Offline regression checks for TTS quota handling, resume, and beat timing."""

import base64
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


# CI does not install worker/requirements.txt. The tests replace the only
# requests method used by the module, so importing the real package is needless.
sys.modules["requests"] = types.ModuleType("requests")
sys.modules["requests"].exceptions = types.SimpleNamespace(Timeout=type("RequestTimeout", (Exception,), {}))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_render_input as render  # noqa: E402
import synthesize_scenes as synth  # noqa: E402


class FakeResponse:
    def __init__(self, status_code: int, *, retry_after: str = "", error: dict | None = None) -> None:
        self.status_code = status_code
        self.headers = {"Retry-After": retry_after}
        self.text = "quota exhausted" if status_code == 429 else ""
        self.error = error

    def json(self) -> dict:
        if self.status_code == 429:
            return {"error": self.error} if self.error is not None else {}
        return {
            "candidates": [{
                "content": {
                    "parts": [{
                        "inlineData": {
                            "mimeType": "audio/mp3",
                            "data": base64.b64encode(b"ID3" + b"a" * 2048).decode("ascii"),
                        }
                    }]
                }
            }]
        }


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.waits: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        assert seconds >= 0
        self.waits.append(seconds)
        self.now += seconds


class SynthesizeScenesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.output_dir = self.folder / "audio"
        self.manifest_path = self.folder / "manifest.json"
        self.project_path = self.folder / "project.json"
        self.project_path.write_text(json.dumps({
            "presenter": {"gender": "male"},
            "scenes": [
                {"id": "scene-00", "narration": "Um dólar sobe."},
                {"id": "scene-01", "narration": "Depois recua."},
            ],
        }), encoding="utf-8")
        self.argv = [
            "synthesize_scenes.py", "--input", str(self.project_path),
            "--output-dir", str(self.output_dir),
            "--manifest", str(self.manifest_path),
        ]

    def test_429_fails_without_azure_and_resume_reuses_completed_scene(self) -> None:
        requests_made = []
        clock = FakeClock()
        ffprobe_calls = []
        phase = "fail_second"

        def fake_post(url, **_kwargs):
            scene_index = 0 if phase == "fail_second" and not requests_made else 1
            requests_made.append("scene-00" if scene_index == 0 else "scene-01")
            if phase == "fail_second" and scene_index == 1:
                return FakeResponse(429, retry_after="22")
            if phase == "cached_only":
                raise AssertionError("Cached audio must not request Gemini")
            return FakeResponse(200)

        def fake_run(command, **_kwargs):
            self.assertEqual(command[0], "ffprobe")
            ffprobe_calls.append(Path(command[-1]).name)
            return types.SimpleNamespace(stdout="3.0\n")

        with (
            patch.dict(os.environ, {
                "GEMINI_API_KEY": "dummy-test-key",
                "GEMINI_TTS_MODEL": synth.PRIMARY_TTS_MODEL,
                "GEMINI_TTS_FALLBACK_MODEL": "",
                "AZURE_SPEECH_KEY": "must-not-be-used",
            }),
            patch.object(sys, "argv", self.argv),
            patch.object(synth.requests, "post", fake_post, create=True),
            patch.object(synth.time, "sleep", clock.sleep),
            patch.object(synth.time, "monotonic", clock.monotonic),
            patch.object(synth.subprocess, "run", fake_run),
        ):
            with self.assertRaisesRegex(RuntimeError, "Gemini TTS falhou"):
                synth.main()
            self.assertFalse(self.manifest_path.exists())
            first_sidecar = self.output_dir / "scene-00.tts.json"
            self.assertTrue(first_sidecar.is_file())
            self.assertEqual(requests_made.count("scene-00"), 1)
            self.assertEqual(requests_made.count("scene-01"), 3)
            self.assertEqual(clock.waits, [22, 22, 30])

            phase = "complete_second"
            requests_made.clear()
            synth.main()
            self.assertEqual(requests_made, ["scene-01"])

            phase = "cached_only"
            requests_made.clear()
            synth.main()
            self.assertEqual(requests_made, [])

            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["engine"], "google-gemini-tts")
            self.assertEqual(manifest["voice"], "Charon")
            self.assertEqual(manifest["model"], synth.PRIMARY_TTS_MODEL)
            self.assertEqual({scene["engine"] for scene in manifest["scenes"]}, {"google-gemini-tts"})
            self.assertEqual({scene["voice"] for scene in manifest["scenes"]}, {"Charon"})
            render.require_gemini_manifest(manifest)
            mixed_manifest = json.loads(json.dumps(manifest))
            mixed_manifest["scenes"][-1]["engine"] = "azure-speech"
            with self.assertRaisesRegex(RuntimeError, "outro motor"):
                render.require_gemini_manifest(mixed_manifest)
            self.assertTrue(ffprobe_calls)

            audio = self.output_dir / "scene-00.mp3"
            narration_hash = hashlib.sha256("Um dólar sobe.".encode("utf-8")).hexdigest()
            self.assertIsNone(synth.cached_duration(audio, "different-narration", "gemini-test-model", "Charon"))
            self.assertIsNone(synth.cached_duration(audio, narration_hash, "different-model", "Charon"))
            self.assertIsNone(synth.cached_duration(audio, narration_hash, synth.PRIMARY_TTS_MODEL, "Autonoe"))
            audio.write_bytes(b"corrupted" * 300)
            self.assertIsNone(synth.cached_duration(audio, narration_hash, synth.PRIMARY_TTS_MODEL, "Charon"))

    def test_structured_429_reports_rpm_and_retry_without_echoing_secrets(self) -> None:
        secret = "AIza-secret-test-key"
        response = FakeResponse(429, retry_after="19", error={
            "status": "RESOURCE_EXHAUSTED",
            "message": f"Quota exhausted for https://example.test/?key={secret}",
            "details": [
                {"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{
                    "quotaMetric": "generativelanguage.googleapis.com/generate_content_free_tier_requests",
                    "quotaId": "GenerateRequestsPerMinutePerProjectPerModel-FreeTier",
                    "quotaValue": "3",
                }, {
                    "quotaMetric": secret,
                    "quotaId": f"https://example.test/?key={secret}",
                    "quotaValue": "",
                }]},
                {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "28s"},
                {"@type": "type.googleapis.com/google.rpc.Help", "links": [{
                    "url": f"https://example.test/?key={secret}",
                }]},
            ],
        })
        diagnostic, retry_delay, daily = synth.gemini_429_diagnostic(response, secret)
        self.assertIn("status=RESOURCE_EXHAUSTED", diagnostic)
        self.assertIn("tipo=RPM", diagnostic)
        self.assertIn("cota=GenerateRequestsPerMinutePerProjectPerModel-FreeTier", diagnostic)
        self.assertIn("limite=3", diagnostic)
        self.assertIn("Retry-After=19.0s", diagnostic)
        self.assertIn("RetryInfo=28.0s", diagnostic)
        self.assertEqual(retry_delay, 28)
        self.assertFalse(daily)
        self.assertNotIn(secret, diagnostic)
        self.assertNotIn("https://", diagnostic)

    def test_rpd_switches_to_flash_lite_and_resume_reuses_audio(self) -> None:
        project = json.loads(self.project_path.read_text(encoding="utf-8"))
        project["scenes"].append({"id": "scene-02", "narration": "O preço muda."})
        self.project_path.write_text(json.dumps(project), encoding="utf-8")
        rpd = FakeResponse(429, error={
            "status": "RESOURCE_EXHAUSTED",
            "details": [{"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{
                "quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier",
            }]}],
        })
        schedule = [
            (synth.PRIMARY_TTS_MODEL, FakeResponse(200)),
            (synth.PRIMARY_TTS_MODEL, rpd),
            (synth.SECONDARY_TTS_MODEL, FakeResponse(200)),
            (synth.SECONDARY_TTS_MODEL, FakeResponse(200)),
            (synth.SECONDARY_TTS_MODEL, FakeResponse(200)),  # transition marker
        ]
        calls = []

        def fake_post(url, **_kwargs):
            expected_model, response = schedule.pop(0)
            self.assertIn(f"/{expected_model}:generateContent", url)
            calls.append(expected_model)
            return response

        def fake_run(command, **_kwargs):
            self.assertEqual(command[0], "ffprobe")
            return types.SimpleNamespace(stdout="3.0\n")

        with (
            patch.dict(os.environ, {
                "GEMINI_API_KEY": "dummy-test-key",
                "GEMINI_TTS_MODEL": synth.PRIMARY_TTS_MODEL,
            }, clear=False),
            patch.object(sys, "argv", self.argv),
            patch.object(synth.requests, "post", fake_post, create=True),
            patch.object(synth.subprocess, "run", fake_run),
            patch.object(synth.time, "sleep", lambda _seconds: None),
        ):
            os.environ.pop("GEMINI_TTS_FALLBACK_MODEL", None)
            os.environ.pop("GEMINI_TTS_FALLBACK_MODELS", None)
            synth.main()
            self.assertEqual(schedule, [])
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["fallback_models"], [
                synth.SECONDARY_TTS_MODEL, synth.FALLBACK_TTS_MODEL,
            ])
            self.assertEqual(manifest["fallback_scene_ids"], ["scene-01", "scene-02"])
            self.assertEqual(manifest["model_transition_count"], 1)
            transition = manifest["scenes"][1]["model_transition"]
            self.assertEqual(transition["from_model"], synth.PRIMARY_TTS_MODEL)
            self.assertEqual(transition["to_model"], synth.SECONDARY_TTS_MODEL)
            self.assertEqual(transition["marker_model"], synth.SECONDARY_TTS_MODEL)
            self.assertEqual(transition["marker_voice"], "Charon")
            self.assertEqual(manifest["scenes"][1]["voice_treatment"], "none")
            self.assertEqual({scene["voice"] for scene in manifest["scenes"]}, {"Charon"})
            render.require_gemini_manifest(manifest)
            marker = self.output_dir / "scene-01.transition.mp3"
            self.assertTrue(marker.is_file())
            self.assertTrue(marker.with_suffix(".transition.json").is_file())
            synth.main()
            self.assertEqual(len(calls), 5, "Reexecução com cache e marcador não deve chamar a API")

    def test_flash_lite_failure_cascades_to_raw_3_1_without_transition_marker(self) -> None:
        rpd = FakeResponse(429, error={
            "status": "RESOURCE_EXHAUSTED",
            "details": [{"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{
                "quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier",
            }]}],
        })
        schedule = [
            (synth.PRIMARY_TTS_MODEL, rpd),
            (synth.SECONDARY_TTS_MODEL, rpd),
            (synth.FALLBACK_TTS_MODEL, FakeResponse(200)),
            (synth.FALLBACK_TTS_MODEL, FakeResponse(200)),
        ]

        def fake_post(url, **_kwargs):
            expected_model, response = schedule.pop(0)
            self.assertIn(f"/{expected_model}:generateContent", url)
            return response

        def fake_run(command, **_kwargs):
            self.assertEqual(command[0], "ffprobe")
            return types.SimpleNamespace(stdout="3.0\n")

        with (
            patch.dict(os.environ, {
                "GEMINI_API_KEY": "dummy-test-key",
                "GEMINI_TTS_MODEL": synth.PRIMARY_TTS_MODEL,
            }, clear=False),
            patch.object(sys, "argv", self.argv),
            patch.object(synth.requests, "post", fake_post, create=True),
            patch.object(synth.subprocess, "run", fake_run),
            patch.object(synth.time, "sleep", lambda _seconds: None),
        ):
            os.environ.pop("GEMINI_TTS_FALLBACK_MODEL", None)
            os.environ.pop("GEMINI_TTS_FALLBACK_MODELS", None)
            synth.main()

        self.assertEqual(schedule, [])
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual({scene["model"] for scene in manifest["scenes"]}, {synth.FALLBACK_TTS_MODEL})
        self.assertTrue(all(
            scene["voice_treatment"] == synth.NO_VOICE_TREATMENT
            for scene in manifest["scenes"]
        ))
        self.assertEqual(manifest["model_transition_count"], 0)
        self.assertFalse((self.output_dir / "scene-00.transition.mp3").exists())
        self.assertIn(synth.PRIMARY_TTS_MODEL + ":rpd", manifest["scenes"][0]["fallback_reason"])
        self.assertIn(synth.SECONDARY_TTS_MODEL + ":rpd", manifest["scenes"][0]["fallback_reason"])
        render.require_gemini_manifest(manifest)

    def test_persistent_server_error_eligible_for_fallback_but_404_is_not(self) -> None:
        responses = [FakeResponse(500), FakeResponse(502), FakeResponse(503)]
        with (
            patch.object(synth.requests, "post", lambda _url, **_kwargs: responses.pop(0), create=True),
            patch.object(synth.time, "sleep", lambda _seconds: None),
        ):
            outcome = synth.synthesize_gemini_audio(
                "Teste", "Charon", self.folder / "server.mp3", "test-key", synth.PRIMARY_TTS_MODEL,
            )
        self.assertIsNone(outcome.model)
        self.assertEqual(outcome.failure, "server-unavailable")
        with patch.object(synth.requests, "post", lambda _url, **_kwargs: FakeResponse(404), create=True):
            outcome = synth.synthesize_gemini_audio(
                "Teste", "Charon", self.folder / "not-found.mp3", "test-key", synth.PRIMARY_TTS_MODEL,
            )
        self.assertEqual(outcome.failure, "other")

    def test_model_identifier_cannot_inject_url_into_logs(self) -> None:
        with self.assertRaisesRegex(ValueError, "modelo Gemini inválido"):
            synth.synthesize_gemini_audio(
                "Narration", "Charon", self.folder / "invalid.mp3", "test-key",
                "https://example.test/?key=test-key",
            )

    def test_persistent_timeout_reports_failure_for_fallback(self) -> None:
        with (
            patch.object(synth.requests, "post", side_effect=synth.requests.exceptions.Timeout, create=True) as post,
            patch.object(synth.time, "sleep", lambda _seconds: None),
        ):
            outcome = synth.synthesize_gemini_audio(
                "Teste", "Charon", self.folder / "timeout.mp3", "test-key", synth.PRIMARY_TTS_MODEL,
                synth.GeminiRequestPacer(minimum_interval_seconds=0),
            )
        self.assertEqual(post.call_count, 3)
        self.assertIsNone(outcome.model)
        self.assertEqual(outcome.failure, "request-timeout")
        self.assertEqual(post.call_args.kwargs["timeout"], 180)

    def test_rpd_429_stops_immediately_and_reports_daily_quota(self) -> None:
        secret = "AIza-secret-test-key"
        response = FakeResponse(429, error={
            "status": "RESOURCE_EXHAUSTED",
            "message": f"https://example.test/?key={secret}",
            "details": [{"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{
                "quotaMetric": "generativelanguage.googleapis.com/generate_content_free_tier_requests",
                "quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier",
                "quotaValue": "10",
            }]}],
        })
        calls = []
        output = io.StringIO()
        with (
            patch.object(synth.requests, "post", lambda url, **kwargs: calls.append(url) or response, create=True),
            patch.object(synth.time, "sleep", side_effect=AssertionError("RPD must not retry")),
            redirect_stdout(output),
        ):
            result = synth.synthesize_gemini_audio(
                "Narration", "Charon", self.folder / "rpd.mp3", secret, "gemini-3.8-flash-tts"
            )
        self.assertIsNone(result.model)
        self.assertEqual(result.failure, "rpd")
        self.assertEqual(len(calls), 1)
        log = output.getvalue()
        self.assertIn("tipo=RPD", log)
        self.assertIn("limite=10", log)
        self.assertIn("Limite diário (RPD) atingido", log)
        self.assertNotIn(secret, log)
        self.assertNotIn("https://", log)

    def test_pacing_applies_to_retries_and_next_scene(self) -> None:
        clock = FakeClock()
        starts = []
        responses = [FakeResponse(429, retry_after="1"), FakeResponse(200), FakeResponse(200)]

        def fake_post(_url, **_kwargs):
            starts.append(clock.now)
            return responses.pop(0)

        pacer = synth.GeminiRequestPacer()
        with (
            patch.object(synth.requests, "post", fake_post, create=True),
            patch.object(synth.time, "sleep", clock.sleep),
            patch.object(synth.time, "monotonic", clock.monotonic),
        ):
            self.assertEqual(synth.synthesize_gemini_audio(
                "First", "Charon", self.folder / "first.mp3", "test-key", "gemini-test-model", pacer
            ).model, "gemini-test-model")
            self.assertEqual(synth.synthesize_gemini_audio(
                "Second", "Charon", self.folder / "second.mp3", "test-key", "gemini-test-model", pacer
            ).model, "gemini-test-model")
        self.assertEqual(starts, [0.0, 22.0, 44.0])
        self.assertEqual(clock.waits, [15, 7, 22])

    def test_estimated_timings_and_legacy_manifest(self) -> None:
        narration = "O dólar subiu. Depois recuou."
        timings = synth.compute_beat_timings(
            narration, [{"anchor": "dólar subiu"}, {"anchor": "inexistente"}], 8.0
        )
        self.assertEqual(
            [item["timing_source"] for item in timings],
            ["estimated-text-alignment", "estimated-distributed"],
        )

        scene = {"narration": narration, "visual": {"beats": [
            {"anchor": "dólar subiu"}, {"anchor": "Depois recuou"},
        ]}}
        audio = {"duration_seconds": 8.0, "beat_timings": [
            {"beat_index": 0, "audio_offset_seconds": 1.0, "timing_source": "gemini-bookmark"},
            {"beat_index": 1, "audio_offset_seconds": 4.0, "timing_source": "estimated-text-alignment"},
        ]}
        resolved = render.resolve_visual_beats(scene, audio)
        self.assertEqual(resolved[0]["timing_source"], "estimated-text-alignment")
        render.validate_stage_timing(scene, resolved, "test")
        self.assertEqual(render.FINAL_SCENE_TAIL_SECONDS, 1.9)


if __name__ == "__main__":
    unittest.main()
