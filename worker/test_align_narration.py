"""Offline alignment and final audio integrity checks; no ASR or provider."""

import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import align_narration as alignment  # noqa: E402
import build_render_input as render  # noqa: E402
from tts_config import TTS_MODEL_CASCADE, VOICE_POLICY_VERSION, voice_policy_fingerprint  # noqa: E402


def recognized_words(words, probability=0.95):
    return [
        {"word": word, "start": 0.3 + index * 0.5,
         "end": 0.6 + index * 0.5, "probability": probability}
        for index, word in enumerate(words)
    ]


class AnchorAlignmentTests(unittest.TestCase):
    def test_aliases_accents_and_numbers_share_spoken_tokens(self):
        self.assertEqual(
            alignment.tokens("A PTAX e o PIB chegam a 100.", {"PTAX": "pêtax"}),
            ["a", "petax", "e", "o", "pib", "chegam", "a", "cem"],
        )
        self.assertEqual(alignment.tokens("82,9"), alignment.tokens("oitenta e dois vírgula nove"))
        self.assertNotIn("faster_whisper", sys.modules)

    def test_brazilian_thousands_are_not_read_as_decimal_one(self):
        self.assertEqual(alignment.tokens("1.000"), ["mil"])
        normalized = alignment.tokens("1.000,50")
        self.assertEqual(normalized[0], "mil")
        self.assertTrue(all(not word[0].isdigit() for word in normalized))

    def test_unique_confident_anchors_use_word_start_and_keep_transcript(self):
        narration = "O dólar subiu antes de recuar."
        beats = [{"anchor": "dólar subiu"}, {"anchor": "recuar"}]
        recognized = recognized_words(["O", "dólar", "subiu", "antes", "de", "recuar"])
        before = copy.deepcopy((beats, recognized))
        accepted, report = alignment.locate_anchors(narration, beats, recognized, 6)
        self.assertEqual(set(accepted), {0, 1})
        self.assertEqual(accepted[0]["audio_offset_seconds"], 0.8)
        self.assertEqual(accepted[1]["audio_offset_seconds"], 2.8)
        self.assertEqual(accepted[0]["anchor"], beats[0]["anchor"])
        self.assertTrue(all(item["timing_source"] == "audio-word-alignment" for item in accepted.values()))
        self.assertEqual(report["transcript_coverage"], 1.0)
        self.assertEqual((beats, recognized), before)

    def test_low_confidence_or_low_transcript_coverage_is_not_measured_alignment(self):
        narration = "O dólar subiu antes de recuar."
        beats = [{"anchor": "dólar subiu"}]
        low_confidence = recognized_words(["O", "dólar", "subiu", "antes", "de", "recuar"], probability=0.4)
        accepted, report = alignment.locate_anchors(narration, beats, low_confidence, 6)
        self.assertEqual(accepted, {})
        self.assertEqual(report["beats"][0]["reason"], "low-confidence-or-coverage")
        accepted, report = alignment.locate_anchors(narration, beats, recognized_words(["dólar", "subiu"]), 6)
        self.assertEqual(accepted, {})
        self.assertLess(report["transcript_coverage"], 0.65)

    def test_repeated_spoken_anchor_is_rejected(self):
        narration = "O dólar subiu e o dólar recuou."
        accepted, report = alignment.locate_anchors(
            narration, [{"anchor": "o dólar"}],
            recognized_words(["O", "dólar", "subiu", "e", "o", "dólar", "recuou"]), 6,
        )
        self.assertEqual(accepted, {})
        self.assertEqual(report["beats"][0]["reason"], "anchor-not-unique")

    def test_invalid_recognizer_timestamps_are_not_accepted(self):
        words = [
            {"word": "dólar", "start": float("nan"), "end": 1, "probability": 0.99},
            {"word": "subiu", "start": -1, "end": 1, "probability": 0.99},
            {"word": "dólar", "start": 9, "end": 10, "probability": 0.99},
        ]
        accepted, report = alignment.locate_anchors("dólar subiu", [{"anchor": "dólar"}], words, 6)
        self.assertEqual(accepted, {})
        self.assertEqual(report["transcript_coverage"], 0.0)

    def test_estimates_remain_monotonic_between_fixed_audio_anchors(self):
        originals = {
            i: {"beat_index": i, "anchor": f"anchor-{i}", "audio_offset_seconds": value,
                "timing_source": "estimated-text-alignment"}
            for i, value in enumerate([0.1, 1, 2, 3, 4, 5, 6])
        }
        accepted = {
            i: {**originals[i], "audio_offset_seconds": value,
                "timing_source": "audio-word-alignment", "alignment_confidence": 0.95}
            for i, value in [(1, 1.5), (5, 3.1)]
        }
        before = copy.deepcopy((originals, accepted))
        merged = alignment.merge_timings(originals, accepted, 8)
        self.assertEqual(merged[1], accepted[1])
        self.assertEqual(merged[5], accepted[5])
        offsets = [item["audio_offset_seconds"] for item in merged]
        self.assertTrue(all(0 <= value <= 8 for value in offsets))
        self.assertTrue(all(right - left >= 0.3999 for left, right in zip(offsets, offsets[1:])))
        self.assertTrue(all(merged[i]["timing_source"] == "estimated-between-audio-anchors" for i in [0, 2, 3, 4, 6]))
        self.assertEqual((originals, accepted), before)

    def test_no_recognized_anchor_preserves_estimates(self):
        originals = {0: {"beat_index": 0, "audio_offset_seconds": 1.2, "timing_source": "estimated-text-alignment"}}
        self.assertEqual(alignment.merge_timings(originals, {}, 5), [originals[0]])


class FinalAudioIntegrityTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.directory = self.root / "processed"
        self.directory.mkdir()
        self.path = self.directory / "scene-00.wav"
        self.path.write_bytes(b"RIFF offline decoded-audio fixture")
        self.scene = {"narration": "  Uma peça custa cem dólares.  "}
        self.audio = {
            "id": "scene-00", "model": TTS_MODEL_CASCADE[0], "voice": "Charon",
            "file": self.path.name, "duration_seconds": 2.5,
            "narration_sha256": hashlib.sha256(self.scene["narration"].strip().encode("utf-8")).hexdigest(),
            "voice_policy_version": VOICE_POLICY_VERSION,
            "voice_policy_fingerprint": voice_policy_fingerprint(TTS_MODEL_CASCADE[0], "Charon"),
            "postprocess": {"output_sha256": hashlib.sha256(self.path.read_bytes()).hexdigest()},
        }

    def test_current_narration_policy_bytes_and_measured_duration_pass(self):
        with patch.object(render.subprocess, "run", return_value=types.SimpleNamespace(stdout="2.500000\n")) as probe:
            render.validate_audio_integrity(self.scene, self.audio, self.directory)
        self.assertEqual(probe.call_count, 1)
        self.assertEqual(probe.call_args.args[0][0], "ffprobe")
        self.assertEqual(Path(probe.call_args.args[0][-1]), self.path)

    def test_changed_narration_is_rejected_before_decoding(self):
        with patch.object(render.subprocess, "run") as probe:
            with self.assertRaisesRegex(RuntimeError, "narração atual"):
                render.validate_audio_integrity({"narration": "A peça custa duzentos dólares."}, self.audio, self.directory)
        probe.assert_not_called()

    def test_wrong_policy_version_or_fingerprint_is_rejected(self):
        for field, value in [("voice_policy_version", "legacy"), ("voice_policy_fingerprint", "0" * 64)]:
            with self.subTest(field=field), patch.object(render.subprocess, "run") as probe:
                with self.assertRaisesRegex(RuntimeError, "política vocal atual"):
                    render.validate_audio_integrity(self.scene, {**self.audio, field: value}, self.directory)
                probe.assert_not_called()

    def test_modified_bytes_are_rejected_before_decoding(self):
        self.path.write_bytes(b"adulterated fixture")
        with patch.object(render.subprocess, "run") as probe:
            with self.assertRaisesRegex(RuntimeError, "Hash do áudio processado"):
                render.validate_audio_integrity(self.scene, self.audio, self.directory)
        probe.assert_not_called()

    def test_outside_or_missing_audio_paths_are_rejected(self):
        outside = self.root / "outside.wav"
        outside.write_bytes(self.path.read_bytes())
        for filename in ["../outside.wav", "missing.wav"]:
            with self.subTest(filename=filename), patch.object(render.subprocess, "run") as probe:
                with self.assertRaisesRegex(RuntimeError, "caminho inválido"):
                    render.validate_audio_integrity(self.scene, {**self.audio, "file": filename}, self.directory)
                probe.assert_not_called()

    def test_invalid_or_different_measured_duration_is_rejected(self):
        for duration in ["nan", "0", "-1", "2.8"]:
            with self.subTest(duration=duration), patch.object(render.subprocess, "run", return_value=types.SimpleNamespace(stdout=duration)):
                with self.assertRaisesRegex(RuntimeError, "Duração do áudio processado"):
                    render.validate_audio_integrity(self.scene, self.audio, self.directory)

    def test_nan_duration_in_manifest_cannot_bypass_integrity(self):
        audio = {**self.audio, "duration_seconds": float("nan")}
        with patch.object(render.subprocess, "run", return_value=types.SimpleNamespace(stdout="2.5")):
            with self.assertRaisesRegex(RuntimeError, "Duração do áudio processado"):
                render.validate_audio_integrity(self.scene, audio, self.directory)


if __name__ == "__main__":
    unittest.main()
