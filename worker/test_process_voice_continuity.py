"""Integration regression for voice continuity v3."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import process_voice_continuity as continuity  # noqa: E402


class VoiceContinuitySafetyTests(unittest.TestCase):
    def reference_asset(self):
        profile = [-5.0, -4.0, -12.0, -25.0, -30.0]
        return {
            "schema_version": continuity.REFERENCE_SCHEMA, "reference_id": "test-primary-reference",
            "model": continuity.PRIMARY_MODEL, "voice": "Charon",
            "provenance_kind": "user-selected-primary-voice-sample",
            "profile_method": continuity.REFERENCE_PROFILE_METHOD,
            "bands_hz": [list(band) for band in continuity.BANDS], "profile_db": profile,
            "profile_sha256": continuity.profile_sha256(profile), "correction_confidence": .75,
            "sources": [{"filename": "unit-fixture.wav", "sha256": "a" * 64, "active_seconds": 8.0, "duration_seconds": 10.0}],
        }

    def test_primary_reference_is_reusable_without_extra_tts_and_never_for_another_voice(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reference.json"
            asset = self.reference_asset()
            path.write_text(json.dumps(asset), encoding="utf-8")
            profile, metadata = continuity.select_reference([], "Charon", path)
            self.assertEqual(metadata["reason"], "reusable-primary-reference")
            self.assertEqual(metadata["scene_ids"], [])
            self.assertEqual(metadata["sources"][0]["sha256"], "a" * 64)
            self.assertTrue(np.array_equal(profile, asset["profile_db"]))
            wrong_voice, rejected = continuity.select_reference([], "Autonoe", path)
            self.assertIsNone(wrong_voice)
            self.assertIn("voice-mismatch", rejected["reason"])
            current = [("a", np.ones(5) * -10, 6), ("b", np.ones(5) * -12, 6)]
            episode_profile, episode = continuity.select_reference(current, "Charon", path)
            self.assertEqual(episode["reason"], "episode-primary-profile")
            self.assertEqual(episode["scene_ids"], ["a", "b"])
            self.assertTrue(np.allclose(episode_profile, -11))
            asset["profile_db"][0] -= 1
            path.write_text(json.dumps(asset), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "hash"):
                continuity.load_reusable_reference(path, "Charon")

    def test_weak_and_phonetic_outlier_windows_reduce_correction_confidence(self):
        reference = np.array([-5., -4., -12., -25., -30.])
        scene = reference + np.array([2., -1., 0., .5, -.5])
        confident, _ = continuity._window_confidence(reference, scene, scene, {"active_seconds": 4., "activity_fraction": .9}, .75)
        weak, _ = continuity._window_confidence(reference, scene, scene, {"active_seconds": 1.3, "activity_fraction": .25}, .75)
        outlier = scene + np.array([10., -5., 2., 9., -9.])
        atypical, _ = continuity._window_confidence(reference, outlier, scene, {"active_seconds": 4., "activity_fraction": .9}, .75)
        self.assertGreater(confident, weak * 5)
        self.assertGreater(confident, atypical * 5)
        self.assertGreaterEqual(weak, 0)
        self.assertLessEqual(confident, .75)

    def test_warning_failure_thresholds_and_peak_metadata_are_consistent(self):
        self.assertFalse(continuity.loudness_assessment(.8)["loudness_warning"])
        self.assertTrue(continuity.loudness_assessment(.9)["loudness_warning"])
        self.assertTrue(continuity.loudness_assessment(1.5)["loudness_warning"])
        with self.assertRaisesRegex(RuntimeError, "failure tolerance"):
            continuity.loudness_assessment(1.51)
        gain, predicted = continuity.static_gain_with_peak_guard(4, -.2)
        self.assertAlmostEqual(gain, -1.02)
        self.assertAlmostEqual(predicted, -1.22)
        self.assertAlmostEqual(predicted, -.2 + gain)




@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "ffmpeg/ffprobe required",
)
class VoiceContinuityIntegrationTests(unittest.TestCase):
    def make_tone(
        self, path: Path, frequency: int, duration: float = 7.0
    ) -> None:
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i",
                f"sine=frequency={frequency}:sample_rate=48000:duration={duration}",
                "-ac", "1", "-b:a", "192k", str(path),
            ],
            check=True,
        )

    def run_worker(
        self, manifest: dict, source: Path, output: Path, root: Path
    ) -> dict:
        manifest_in = root / "tts.json"
        manifest_out = root / "processed.json"
        manifest_in.write_text(json.dumps(manifest), encoding="utf-8")
        argv = [
            "process_voice_continuity.py",
            "--input-manifest", str(manifest_in),
            "--source-dir", str(source),
            "--output-dir", str(output),
            "--output-manifest", str(manifest_out),
        ]
        with patch.object(sys, "argv", argv):
            continuity.main()
        return json.loads(manifest_out.read_text(encoding="utf-8"))

    def test_single_model_is_byte_identical_with_zero_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            output = root / "processed"
            source.mkdir()

            scenes = []
            for idx, frequency in enumerate((330, 390)):
                scene_id = f"scene-{idx:02d}"
                audio = source / f"{scene_id}.mp3"
                self.make_tone(audio, frequency)
                scenes.append({
                    "id": scene_id,
                    "file": audio.name,
                    "duration_seconds": 7.0,
                    "engine": "google-gemini-tts",
                    "model": continuity.PRIMARY_MODEL,
                    "voice": "Charon",
                    "voice_treatment": "none",
                    "fallback_reason": None,
                    "beat_timings": [],
                })

            manifest = {
                "engine": "google-gemini-tts",
                "model": continuity.PRIMARY_MODEL,
                "fallback_models": [
                    continuity.SECONDARY_MODEL,
                    continuity.FALLBACK_MODEL,
                ],
                "voice": "Charon",
                "model_transition_count": 0,
                "scenes": scenes,
            }
            result = self.run_worker(manifest, source, output, root)
            self.assertEqual(
                result["postprocess"]["mode"],
                "homogeneous-passthrough",
            )
            self.assertFalse(result["postprocess"]["effects_applied"])

            for scene in result["scenes"]:
                original = source / scene["file"]
                copied = output / scene["file"]
                self.assertEqual(
                    hashlib.sha256(original.read_bytes()).hexdigest(),
                    hashlib.sha256(copied.read_bytes()).hexdigest(),
                )
                self.assertTrue(scene["postprocess"]["byte_identical"])
                self.assertFalse(scene["postprocess"]["eq_applied"])
                self.assertFalse(scene["postprocess"]["gain_applied"])
                self.assertFalse(scene["postprocess"]["limiter_applied"])
                self.assertFalse(scene["postprocess"]["reencoded"])

    def test_mixed_model_processes_only_fallback_without_audible_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            output = root / "processed"
            source.mkdir()

            primary = source / "scene-00.mp3"
            fallback = source / "scene-01.mp3"
            self.make_tone(primary, 330)
            self.make_tone(fallback, 440)

            scenes = [
                {
                    "id": "scene-00",
                    "file": primary.name,
                    "duration_seconds": 7.0,
                    "engine": "google-gemini-tts",
                    "model": continuity.PRIMARY_MODEL,
                    "voice": "Charon",
                    "voice_treatment": "none",
                    "fallback_reason": None,
                    "beat_timings": [],
                },
                {
                    "id": "scene-01",
                    "file": fallback.name,
                    "duration_seconds": 7.0,
                    "engine": "google-gemini-tts",
                    "model": continuity.SECONDARY_MODEL,
                    "voice": "Charon",
                    "voice_treatment": "none",
                    "fallback_reason": "test",
                    "beat_timings": [{"audio_offset_seconds": 1.0}],
                    "model_transition": {
                        "from_model": continuity.PRIMARY_MODEL,
                        "to_model": continuity.SECONDARY_MODEL,
                        "marker_status": "disabled",
                    },
                },
            ]
            manifest = {
                "engine": "google-gemini-tts",
                "model": continuity.PRIMARY_MODEL,
                "fallback_models": [
                    continuity.SECONDARY_MODEL,
                    continuity.FALLBACK_MODEL,
                ],
                "voice": "Charon",
                "model_transition_count": 1,
                "scenes": scenes,
            }
            result = self.run_worker(manifest, source, output, root)
            self.assertEqual(
                result["postprocess"]["mode"],
                "mixed-model-fallback-only",
            )
            first, second = result["scenes"]
            self.assertTrue(first["postprocess"]["byte_identical"])
            self.assertFalse(first["postprocess"]["eq_applied"])
            self.assertFalse(first["postprocess"]["gain_applied"])
            self.assertTrue(second["postprocess"]["model_transition_recorded"])
            self.assertFalse(second["postprocess"]["audible_transition_marker"])
            self.assertAlmostEqual(second["duration_seconds"], 7.0, delta=0.1)
            self.assertAlmostEqual(
                second["beat_timings"][0]["audio_offset_seconds"],
                1.0,
                delta=0.01,
            )
            self.assertFalse(second["postprocess"]["limiter_applied"])
            self.assertEqual((output / first["file"]).suffix, ".mp3")
            self.assertEqual((output / second["file"]).suffix, ".wav")


if __name__ == "__main__":
    unittest.main()
