"""Offline checks for authored acting cues and literal script preservation."""

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tts_config import (  # noqa: E402
    live_session_config,
    live_turn_text,
    scene_direction_fingerprint,
    scene_voice_direction,
)
import synthesize_scenes as synth  # noqa: E402


class AuthoredVoiceDirectionTests(unittest.TestCase):
    def scene(self):
        return {
            "narration": "Parece contraditório? A empresa continua no Simples.",
            "tts": {
                "delivery": "hook",
                "cues": [{
                    "text": "Parece contraditório?",
                    "kind": "emphasis",
                    "intent": "curiosity",
                    "arc": "question",
                    "emphasis_word": "contraditório",
                }],
            },
        }

    def test_authored_cue_reaches_portuguese_instructions_and_keeps_script_literal(self):
        scene = self.scene()
        before = copy.deepcopy(scene)
        direction = scene_voice_direction(scene)
        prompt = live_turn_text(scene["narration"], direction)
        instructions, script = prompt.split("\n\nROTEIRO:\n")
        self.assertEqual(script, scene["narration"])
        self.assertEqual(scene, before)
        self.assertIn("Intenção: curiosidade", instructions)
        self.assertIn("Arco: abra a pergunta", instructions)
        self.assertIn('Apoie a palavra "contraditório"', instructions)
        self.assertNotIn("aproximadamente 0 ms", instructions)

        legacy = {
            "narration": "A conta muda.",
            "tts": {"cues": [{"text": "A conta muda.", "kind": "number"}]},
        }
        old_prompt = live_turn_text(legacy["narration"], scene_voice_direction(legacy))
        self.assertIn("Articule o número com clareza", old_prompt)
        self.assertTrue(old_prompt.endswith("ROTEIRO:\nA conta muda."))

    def test_no_authored_cues_are_inferred_and_voice_presets_stay_fixed(self):
        scene = {"narration": "O que muda? A resposta depende da empresa."}
        self.assertEqual(scene_voice_direction(scene), {})
        self.assertIsNone(scene_direction_fingerprint(scene))
        self.assertEqual(live_turn_text(scene["narration"], {}), "ROTEIRO:\n" + scene["narration"])
        for voice in ("Charon", "Autonoe"):
            config = live_session_config(voice)
            self.assertEqual(config["speech_config"]["voice_config"]["prebuilt_voice_config"]["voice_name"], voice)
            self.assertNotIn("temperature", config)
            self.assertIn("output_audio_transcription", config)

    def test_invalid_acting_fields_fail_before_a_provider_request(self):
        for field, value in (
            ("intent", "invented"), ("intent", None),
            ("arc", "sing"), ("arc", []),
            ("emphasis_word", "contradi"),
            ("emphasis_word", "Contraditório"),
            ("emphasis_word", "não está"),
            ("emphasis_word", "contradi-tório"),
            ("emphasis_word", ""), ("emphasis_word", None),
        ):
            with self.subTest(field=field, value=value):
                scene = self.scene()
                scene["tts"]["cues"][0][field] = value
                with self.assertRaises(ValueError):
                    scene_voice_direction(scene)
        repeated = {"narration": "A conta muda a conta.", "tts": {"cues": [{"text": "A conta muda a conta.", "kind": "emphasis", "emphasis_word": "conta"}]}}
        with self.assertRaisesRegex(ValueError, "uma vez"):
            scene_voice_direction(repeated)

    def test_cue_does_not_cross_a_sentence_and_accepts_a_literal_decimal(self):
        crossing = self.scene()
        crossing["tts"]["cues"][0]["text"] = crossing["narration"]
        with self.assertRaisesRegex(ValueError, "atravessar frases"):
            scene_voice_direction(crossing)
        decimal = {"narration": "O valor é 1.000 reais.", "tts": {"cues": [{"text": "1.000 reais.", "kind": "number", "emphasis_word": "reais"}]}}
        self.assertEqual(scene_voice_direction(decimal)["cues"][0]["emphasis_word"], "reais")

    def test_each_authored_change_invalidates_direction_but_visual_changes_do_not(self):
        original = self.scene()
        fingerprint = scene_direction_fingerprint(original)
        for field, value in (
            ("intent", "discovery"),
            ("arc", "build"),
            ("emphasis_word", "Parece"),
            ("pause_before_ms", 180),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(original)
                changed["tts"]["cues"][0][field] = value
                self.assertNotEqual(fingerprint, scene_direction_fingerprint(changed))
        visual_only = copy.deepcopy(original)
        visual_only["visual"] = {"camera": {"zoom": 1.2}}
        self.assertEqual(fingerprint, scene_direction_fingerprint(visual_only))

    def test_cached_audio_requires_the_current_authored_direction(self):
        scene = self.scene()
        narration = scene["narration"]
        narration_hash = hashlib.sha256(narration.encode("utf-8")).hexdigest()
        fingerprint = scene_direction_fingerprint(scene)
        with tempfile.TemporaryDirectory() as tmp:
            audio = Path(tmp) / "scene-00.wav"
            audio.write_bytes(b"RIFF" + b"x" * 3000)
            audio.with_suffix(".tts.json").write_text(json.dumps({
                "engine": synth.ENGINE,
                "narration_sha256": narration_hash,
                "model": synth.PRIMARY_TTS_MODEL,
                "voice": "Charon",
                "voice_treatment": "none",
                "voice_policy_fingerprint": synth.voice_policy_fingerprint(synth.PRIMARY_TTS_MODEL, "Charon"),
                "speech_profile_fingerprint": None,
                "scene_direction_fingerprint": fingerprint,
                "output_transcription": narration,
                "output_transcription_similarity": 1.0,
                "audio_sha256": synth.audio_sha256(audio),
                "duration_seconds": 3.0,
            }), encoding="utf-8")
            with patch.object(synth, "duration_seconds", return_value=3.0):
                self.assertEqual(synth.cached_duration(audio, narration_hash, synth.PRIMARY_TTS_MODEL, "Charon", narration=narration, direction_fingerprint=fingerprint), 3.0)
                changed = copy.deepcopy(scene)
                changed["tts"]["cues"][0]["intent"] = "discovery"
                self.assertIsNone(synth.cached_duration(audio, narration_hash, synth.PRIMARY_TTS_MODEL, "Charon", narration=narration, direction_fingerprint=scene_direction_fingerprint(changed)))


if __name__ == "__main__":
    unittest.main()
