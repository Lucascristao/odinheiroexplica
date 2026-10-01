"""Offline regression checks for Gemini Live narration policy and cache."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_render_input as render  # noqa: E402
import synthesize_scenes as synth  # noqa: E402
from tts_config import (  # noqa: E402
    PRIMARY_TTS_MODEL,
    TTS_MODEL_CASCADE,
    project_speech_fingerprint,
)


class GeminiLiveTests(unittest.TestCase):
    def test_single_model_policy_has_no_fallback(self):
        self.assertEqual(TTS_MODEL_CASCADE, ("gemini-3.8-live",))
        self.assertEqual(
            synth.configured_fallback_models(PRIMARY_TTS_MODEL), []
        )
        self.assertEqual(
            synth.voice_treatment_for_model(PRIMARY_TTS_MODEL, "Charon"),
            "none",
        )

    def test_transcription_similarity_ignores_punctuation_and_accents(self):
        reference = "A lógica mudou: IBS e CBS ficam no DAS."
        transcript = "A logica mudou, IBS e CBS ficam no DAS"
        self.assertEqual(
            synth.transcription_similarity(reference, transcript), 1.0
        )
        self.assertLess(
            synth.transcription_similarity(reference, "Outro texto."),
            0.5,
        )

    def test_cache_requires_current_speech_profile_and_literal_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "scene-00.wav"
            audio.write_bytes(b"RIFF" + b"x" * 3000)
            narration = "IBS e CBS ficam no DAS."
            narration_hash = hashlib.sha256(
                narration.encode("utf-8")
            ).hexdigest()
            project = {
                "speech": {
                    "pronunciations": {
                        "IBS": "i bê ésse",
                        "CBS": "cê bê ésse",
                    }
                }
            }
            speech_fp = project_speech_fingerprint(project)
            with (
                patch.object(synth, "audio_sha256", return_value="a" * 64),
                patch.object(synth, "duration_seconds", return_value=3.0),
            ):
                metadata = {
                    "engine": synth.ENGINE,
                    "model": PRIMARY_TTS_MODEL,
                    "voice": "Charon",
                    "voice_treatment": "none",
                    "fallback_reason": None,
                    "voice_policy_version": synth.VOICE_POLICY_VERSION,
                    "voice_policy_fingerprint":
                        synth.voice_policy_fingerprint(
                            PRIMARY_TTS_MODEL, "Charon"
                        ),
                    "speech_profile_fingerprint": speech_fp,
                    "speech_endpoint": "live-websocket",
                    "narration_sha256": narration_hash,
                    "audio_sha256": "a" * 64,
                    "duration_seconds": 3.0,
                    "output_transcription": narration,
                    "output_transcription_similarity": 1.0,
                }
                audio.with_suffix(".tts.json").write_text(
                    json.dumps(metadata), encoding="utf-8"
                )
                self.assertEqual(
                    synth.cached_duration(
                        audio,
                        narration_hash,
                        PRIMARY_TTS_MODEL,
                        "Charon",
                        "none",
                        speech_fp,
                    ),
                    3.0,
                )
                self.assertIsNone(
                    synth.cached_duration(
                        audio,
                        narration_hash,
                        PRIMARY_TTS_MODEL,
                        "Charon",
                        "none",
                        "0" * 64,
                    )
                )

    def test_estimated_timings_stay_compatible_with_render(self):
        narration = "O Simples mudou. Depois vem a escolha."
        timings = synth.compute_beat_timings(
            narration,
            [{"anchor": "Simples mudou"}, {"anchor": "vem a escolha"}],
            8.0,
        )
        self.assertEqual(len(timings), 2)
        scene = {
            "narration": narration,
            "visual": {
                "beats": [
                    {"anchor": "Simples mudou"},
                    {"anchor": "vem a escolha"},
                ]
            },
        }
        audio = {
            "duration_seconds": 8.0,
            "beat_timings": timings,
        }
        resolved = render.resolve_visual_beats(scene, audio)
        render.validate_stage_timing(scene, resolved, "test")


if __name__ == "__main__":
    unittest.main()
