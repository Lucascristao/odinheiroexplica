"""Integration regression for processed 24-bit WAV voice continuity output."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import process_voice_continuity as continuity  # noqa: E402


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
class VoiceContinuityIntegrationTests(unittest.TestCase):
    def make_tone(self, path: Path, frequency: int) -> None:
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i",
                f"sine=frequency={frequency}:sample_rate=48000:duration=7",
                "-ac", "1", "-b:a", "192k", str(path),
            ],
            check=True,
        )

    def test_pcm_s24le_output_is_validated_with_ffprobe_not_python_wave(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            output = root / "processed"
            source.mkdir()
            scenes = []
            specs = [
                ("scene-00", 330, continuity.PRIMARY_MODEL),
                ("scene-01", 390, continuity.PRIMARY_MODEL),
                ("scene-02", 440, continuity.SECONDARY_MODEL),
            ]
            for scene_id, frequency, model in specs:
                audio = source / f"{scene_id}.mp3"
                self.make_tone(audio, frequency)
                scenes.append({
                    "id": scene_id,
                    "file": audio.name,
                    "duration_seconds": 7.0,
                    "engine": "google-gemini-tts",
                    "model": model,
                    "voice": "Charon",
                    "voice_treatment": "none",
                    "fallback_reason": None if model == continuity.PRIMARY_MODEL else "test-fallback",
                    "beat_timings": [],
                })

            manifest = {
                "engine": "google-gemini-tts",
                "model": continuity.PRIMARY_MODEL,
                "fallback_model": continuity.SECONDARY_MODEL,
                "fallback_models": [continuity.SECONDARY_MODEL, continuity.FALLBACK_MODEL],
                "voice": "Charon",
                "scenes": scenes,
            }
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

            result = json.loads(manifest_out.read_text(encoding="utf-8"))
            self.assertEqual(result["postprocess"]["version"], continuity.VERSION)
            self.assertEqual(len(result["scenes"]), 3)
            fallback = next(scene for scene in result["scenes"] if scene["id"] == "scene-02")
            self.assertIn("slow-window-match-gemini-3.8-flash-lite-tts", fallback["postprocess"]["reason"])
            self.assertGreaterEqual(len(fallback["postprocess"]["adaptive_windows"]), 2)
            self.assertEqual(
                fallback["postprocess"]["normalization_type"],
                "static-gain-with-safety-limiter",
            )
            self.assertEqual(
                result["postprocess"]["normalization_type"],
                "static-gain-with-safety-limiter",
            )

            for scene in result["scenes"]:
                wav = output / scene["file"]
                metadata = continuity.probe_audio_format(shutil.which("ffprobe"), wav)
                self.assertEqual(metadata["codec_name"], "pcm_s24le")
                self.assertEqual(metadata["sample_rate"], 48000)
                self.assertEqual(metadata["channels"], 1)
                self.assertEqual(scene["postprocess"]["output_samples"], 7 * 48000)


if __name__ == "__main__":
    unittest.main()
