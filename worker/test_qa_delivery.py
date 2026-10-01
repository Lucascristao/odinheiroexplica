"""Offline regressions for literal Live speech, raw bytes and MP4 coverage."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qa_delivery as qa
from gemini_live_fidelity import evaluate_transcription
from tts_config import PRIMARY_TTS_MODEL, VOICE_POLICY_VERSION, project_speech_fingerprint, voice_policy_fingerprint


class LiteralFidelityTests(unittest.TestCase):
    def test_small_number_or_negation_change_cannot_hide_in_long_similar_text(self):
        prefix = "A empresa compara clientes, custos e créditos antes de fazer sua escolha. " * 20
        for expected, spoken in [("A opção não mudou.", "A opção mudou."), ("O prazo termina em 30 de outubro.", "O prazo termina em 31 de outubro.")]:
            report = evaluate_transcription(prefix+expected, prefix+spoken)
            self.assertGreater(report["similarity"], .985)
            self.assertFalse(report["passed"])

    def test_numeric_acronym_and_date_equivalents_are_not_improvisation(self):
        aliases = {"IBS": "i bê ésse"}
        report = evaluate_transcription("IBS chega a 82,9% em 30/10/2026.", "I bê ésse chega a oitenta e dois vírgula nove por cento em trinta de outubro de dois mil e vinte e seis.", aliases)
        self.assertTrue(report["passed"], report)
        for expected, output in [("R$ 100,50", "cem reais e cinquenta centavos"), ("1º semestre", "primeiro semestre"), ("1ª decisão", "primeira decisão")]:
            report = evaluate_transcription(expected, output)
            self.assertTrue(report["passed"], report)

    def test_extra_greeting_and_missing_last_word_fail(self):
        for output in ["Olá. A conta não mudou.", "A conta não.", "A conta não mudou. Obrigado."]:
            self.assertFalse(evaluate_transcription("A conta não mudou.", output)["passed"])


class DeliveryGateTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.audio_dir = self.root / "public" / "processed-audio" / "daily"
        self.audio_dir.mkdir(parents=True)
        self.audio = self.audio_dir / "scene-00.wav"
        samples = (np.sin(np.arange(24000*3)*2*np.pi*300/24000)*3000).astype("<i2")
        with wave.open(str(self.audio), "wb") as wav:
            wav.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
            wav.writeframes(samples.tobytes())
        self.video = self.root / "video.mp4"
        self.video.write_bytes(b"offline fixture; ffmpeg probe/meter mocked")
        narration = "A empresa não deve decidir antes de comparar os dois cenários."
        self.project = {"presenter": {"gender": "male"}, "scenes": [{"id": "scene-00", "narration": narration}]}
        self.render = {"fps": 30, "duration_in_frames": 147, "scenes": [{"id": "scene-00", "start_frame": 0, "duration_frames": 147, "audio_file": "processed-audio/daily/scene-00.wav"}]}
        digest = hashlib.sha256(self.audio.read_bytes()).hexdigest()
        self.manifest = {"engine": "google-gemini-live", "model": PRIMARY_TTS_MODEL, "voice": "Charon", "voice_policy_version": VOICE_POLICY_VERSION,
                         "scenes": [{"id": "scene-00", "file": "scene-00.wav", "duration_seconds": 3.0, "engine": "google-gemini-live", "model": PRIMARY_TTS_MODEL, "voice": "Charon", "voice_treatment": "none", "fallback_reason": None,
                                     "voice_policy_version": VOICE_POLICY_VERSION, "voice_policy_fingerprint": voice_policy_fingerprint(PRIMARY_TTS_MODEL, "Charon"),
                                     "speech_profile_fingerprint": project_speech_fingerprint(self.project), "narration_sha256": hashlib.sha256(narration.encode()).hexdigest(),
                                     "audio_sha256": digest, "output_transcription": narration, "output_transcription_similarity": 1.0,
                                     "postprocess": {"source_sha256": digest, "output_sha256": digest, "byte_identical": True, "effects_applied": False}}]}
        self.probe = {"format": {"duration": "4.92"}, "streams": [{"codec_type": "video", "duration": "4.9"}, {"codec_type": "audio", "duration": "4.92", "channels": 2, "sample_rate": "48000"}]}
        self.meter = {"integrated_lufs": -17.8, "true_peak_dbtp": -1.23, "loudness_range_lu": 3.4, "channel_handling": "actual encoded channel layout; no downmix"}

    def analyze(self):
        with patch.object(qa, "probe_video", return_value=self.probe), patch.object(qa, "meter_video", return_value=self.meter):
            return qa.analyze_delivery(self.project, self.render, self.manifest, self.video, self.audio_dir)

    def test_valid_raw_bytes_literal_text_and_real_channel_peak_pass(self):
        result = self.analyze()
        self.assertEqual(result["status"], "pass", result)
        self.assertTrue(result["scenes"][0]["raw_bytes_verified"])
        self.assertFalse(result["subjective_listening_performed"])
        self.assertEqual(result["video"]["true_peak_dbtp"], -1.23)

    def test_changed_waveform_cannot_pass_even_with_same_narration(self):
        with self.audio.open("ab") as file:
            file.write(b"modified")
        result = self.analyze()
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("Hash" in f["message"] for f in result["failures"]))

    def test_faked_similarity_score_cannot_approve_missing_negation(self):
        self.manifest["scenes"][0]["output_transcription"] = self.project["scenes"][0]["narration"].replace("não ", "")
        result = self.analyze()
        self.assertEqual(result["status"], "fail")
        self.assertIn("literal-transcript-mismatch", [f["code"] for f in result["failures"]])

    def test_timeline_and_encoded_mp4_must_cover_audio(self):
        self.render["scenes"][0]["duration_frames"] = 60
        self.render["duration_in_frames"] = 60
        self.probe["streams"][0]["duration"] = "2"
        self.probe["streams"][1]["duration"] = "2"
        result = self.analyze()
        self.assertIn("timeline-cuts-raw-audio", [f["code"] for f in result["failures"]])

    def test_no_fallback_or_dsp_can_enter_live_delivery(self):
        self.manifest["scenes"][0]["model"] = "gemini-3.1-flash-tts-preview"
        self.assertEqual(self.analyze()["status"], "fail")
        self.manifest["scenes"][0]["model"] = PRIMARY_TTS_MODEL
        self.manifest["scenes"][0]["postprocess"]["gain_applied"] = True
        self.assertEqual(self.analyze()["status"], "fail")

    def test_positive_true_peak_is_warning_without_silent_normalization(self):
        self.meter["true_peak_dbtp"] = .12
        result = self.analyze()
        self.assertEqual(result["status"], "warn")
        self.assertEqual(result["failures"], [])
        self.assertIn("mp4-positive-true-peak", [w["code"] for w in result["warnings"]])


if __name__ == "__main__":
    unittest.main()
