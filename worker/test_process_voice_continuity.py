"""Regression test: Gemini Live delivery must be byte-identical passthrough."""

import hashlib
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


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "ffmpeg/ffprobe required",
)
class LivePassthroughTests(unittest.TestCase):
    def test_wav_is_copied_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            output = root / "processed"
            source.mkdir()
            audio = source / "scene-00.wav"
            subprocess.run(
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i",
                    "sine=frequency=330:sample_rate=24000:duration=3",
                    "-ac", "1", "-c:a", "pcm_s16le", str(audio),
                ],
                check=True,
            )
            duration = continuity.duration_seconds(audio)
            manifest = {
                "engine": continuity.ENGINE,
                "model": continuity.PRIMARY_TTS_MODEL,
                "voice": "Charon",
                "model_transition_count": 0,
                "scenes": [{
                    "id": "scene-00",
                    "file": audio.name,
                    "duration_seconds": duration,
                    "engine": continuity.ENGINE,
                    "model": continuity.PRIMARY_TTS_MODEL,
                    "voice": "Charon",
                    "voice_treatment": "none",
                    "beat_timings": [],
                }],
            }
            input_manifest = root / "input.json"
            output_manifest = root / "output.json"
            input_manifest.write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            argv = [
                "process_voice_continuity.py",
                "--input-manifest", str(input_manifest),
                "--source-dir", str(source),
                "--output-dir", str(output),
                "--output-manifest", str(output_manifest),
            ]
            with patch.object(sys, "argv", argv):
                continuity.main()

            result = json.loads(
                output_manifest.read_text(encoding="utf-8")
            )
            delivered = output / "scene-00.wav"
            self.assertEqual(
                hashlib.sha256(audio.read_bytes()).hexdigest(),
                hashlib.sha256(delivered.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                result["postprocess"]["version"],
                continuity.VERSION,
            )
            self.assertFalse(
                result["postprocess"]["effects_applied"]
            )
            self.assertTrue(
                result["scenes"][0]["postprocess"]["byte_identical"]
            )


if __name__ == "__main__":
    unittest.main()
