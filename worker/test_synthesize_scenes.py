"""Offline regression checks for Gemini Live narration policy and cache."""

import hashlib
import asyncio
import json
from pathlib import Path
import sys
import tempfile
import unittest
import types
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_render_input as render  # noqa: E402
import synthesize_scenes as synth  # noqa: E402
from tts_config import (  # noqa: E402
    PRIMARY_TTS_MODEL,
    TTS_MODEL_CASCADE,
    live_session_config,
    project_speech_fingerprint,
    scene_voice_direction, scene_direction_fingerprint, live_turn_text,
)


class GeminiLiveTests(unittest.TestCase):
    def test_live_config_uses_provider_default_temperature(self):
        config = live_session_config("Charon")
        self.assertNotIn("temperature", config)

    def test_retry_classifier_handles_1011_but_not_bad_script(self):
        self.assertTrue(
            synth.is_retryable_live_error(
                RuntimeError(
                    "received 1011 (internal error) Resource has been exhausted"
                )
            )
        )
        self.assertTrue(
            synth.is_retryable_live_error(
                synth.RetryableLiveError("primeiro áudio expirou")
            )
        )
        self.assertFalse(
            synth.is_retryable_live_error(
                RuntimeError("Gemini Live divergiu do roteiro")
            )
        )

    def test_pathological_audio_guard_is_generous_but_bounded(self):
        short = synth.max_allowed_audio_seconds("texto curto")
        long = synth.max_allowed_audio_seconds("palavra " * 200)
        self.assertGreaterEqual(short, 45)
        self.assertGreater(long, short)
        self.assertLess(long, 300)

    def test_scene_direction_is_separate_literal_and_cache_scoped(self):
        scene = {"narration": "A empresa não sai do Simples.", "tts": {"delivery": "contrast", "cues": [{"text": "não sai", "kind": "emphasis"}]}}
        direction = scene_voice_direction(scene)
        request = live_turn_text(scene["narration"], direction)
        self.assertTrue(request.endswith("ROTEIRO:\n" + scene["narration"]))
        self.assertIn("NÃO LEIA", request)
        self.assertNotEqual(scene_direction_fingerprint(scene), scene_direction_fingerprint({**scene, "tts": {"delivery": "explain"}}))
        self.assertIsNone(scene_direction_fingerprint({"narration": scene["narration"]}))
        for field in ("rate", "pitch"):
            with self.assertRaises(ValueError):
                scene_voice_direction({"narration": scene["narration"], "tts": {field: "+10%"}})

    def test_year_pronunciation_and_reference_bound_transcript_alias(self):
        scene = {"narration": "Essa escolha chega para 2027."}
        direction = scene_voice_direction(scene)
        self.assertEqual(
            direction["pronunciations"]["2027"],
            "dois mil e vinte e sete",
        )
        request = live_turn_text(scene["narration"], direction)
        self.assertIn(
            'Pronúncia: "2027" como "dois mil e vinte e sete".',
            request,
        )

        equivalent = synth.evaluate_transcription(
            "Essa escolha chega para 2027.",
            "Essa escolha chega para vinte vinte e sete.",
        )
        self.assertTrue(equivalent["passed"])
        self.assertEqual(equivalent["similarity"], 1.0)
        self.assertTrue(equivalent["numeric_equivalences"])

        wrong_year = synth.evaluate_transcription(
            "Essa escolha chega para 2027.",
            "Essa escolha chega para vinte vinte e oito.",
        )
        self.assertFalse(wrong_year["passed"])
        self.assertTrue(wrong_year["numeric_only_mismatch"])

        lexical_change = synth.evaluate_transcription(
            "A empresa não sai do Simples em 2027.",
            "A empresa sai do Simples em vinte vinte e sete.",
        )
        self.assertFalse(lexical_change["passed"])
        self.assertFalse(lexical_change["numeric_only_mismatch"])

    def test_live_turn_collects_final_audio_and_transcript_before_completion(self):
        def response(data=b"", text=None, complete=False, interrupted=False, usage=None, go_away=None):
            return types.SimpleNamespace(
                usage_metadata=usage,
                go_away=go_away,
                session_resumption_update=None,
                server_content=types.SimpleNamespace(
                    model_turn=types.SimpleNamespace(parts=[types.SimpleNamespace(inline_data=types.SimpleNamespace(data=data, mime_type="audio/pcm;rate=24000"))]),
                    output_transcription=types.SimpleNamespace(text=text),
                    turn_complete=complete,
                    generation_complete=complete,
                    interrupted=interrupted,
                ),
            )
        class Session:
            def __init__(self, events): self.events = events
            async def receive(self):
                for event in self.events: yield event
        diagnostics = {}
        audio, transcript = asyncio.run(synth._receive_live_turn(
            Session([
                response(
                    b"\x01\x00"*24000,
                    "A conta ",
                    usage=types.SimpleNamespace(prompt_token_count=8, total_token_count=20),
                    go_away=types.SimpleNamespace(time_left="30s"),
                ),
                response(b"\x02\x00"*24000, "não mudou.", True),
            ]),
            narration="A conta não mudou.",
            attempt_diagnostics=diagnostics,
        ))
        self.assertEqual(len(audio), 96000)
        self.assertEqual(transcript, "A conta não mudou.")
        self.assertTrue(diagnostics["usage_metadata"])
        self.assertTrue(diagnostics["go_away"])
        self.assertTrue(diagnostics["turn_complete_seen"])
        with self.assertRaisesRegex(RuntimeError, "interrompeu"):
            asyncio.run(synth._receive_live_turn(Session([response(b"\x00\x00"*24000, "A conta", True, True)])))
        with self.assertRaisesRegex(RuntimeError, "turn_complete"):
            asyncio.run(synth._receive_live_turn(Session([response(b"\x00\x00"*24000, "A conta")])))
        
        class HangingAfterGeneration:
            def __init__(self, event):
                self.event = event
                self.sent = False
            def __aiter__(self):
                return self
            async def __anext__(self):
                if not self.sent:
                    self.sent = True
                    return self.event
                await asyncio.sleep(3600)
            def receive(self):
                return self

        post_generation = response(
            b"\x03\x00"*24000,
            "A conta não mudou.",
            complete=False,
        )
        post_generation.server_content.generation_complete = True
        diagnostics_after_generation = {}
        with patch.object(synth, "LIVE_POST_GENERATION_GRACE_SECONDS", 0.01):
            audio2, transcript2 = asyncio.run(synth._receive_live_turn(
                HangingAfterGeneration(post_generation),
                narration="A conta não mudou.",
                attempt_diagnostics=diagnostics_after_generation,
            ))
        self.assertEqual(len(audio2), 48000)
        self.assertEqual(transcript2, "A conta não mudou.")
        self.assertTrue(
            diagnostics_after_generation[
                "accepted_generation_complete_without_turn_complete"
            ]
        )
        self.assertFalse(
            diagnostics_after_generation["turn_complete_seen"]
        )

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
                metadata["output_transcription"] = "IBS e CBS não ficam no DAS."
                metadata["output_transcription_similarity"] = 1.0
                audio.with_suffix(".tts.json").write_text(json.dumps(metadata), encoding="utf-8")
                self.assertIsNone(synth.cached_duration(audio, narration_hash, PRIMARY_TTS_MODEL, "Charon", "none", speech_fp, narration=narration, pronunciations=project["speech"]["pronunciations"]))

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
