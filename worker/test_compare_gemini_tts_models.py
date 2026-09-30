import base64
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import wave

from worker import compare_gemini_tts_models as comparison


def wav_sample() -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(b"\x00\x00" * 24000)
    return output.getvalue()


def response_with_audio(audio: bytes, mime_type: str) -> bytes:
    return json.dumps({
        "candidates": [{"content": {"parts": [{"inlineData": {
            "data": base64.b64encode(audio).decode("ascii"),
            "mimeType": mime_type,
        }}]}}]
    }).encode("utf-8")


class CompareGeminiTtsModelsTests(unittest.TestCase):
    def test_same_text_and_charon_across_all_three_models(self):
        for model in comparison.MODELS:
            payload = comparison.payload_for(model)
            self.assertEqual(payload["contents"][0]["parts"][0]["text"], comparison.TEXT)
            voice_config = payload["generationConfig"]["speechConfig"]["voiceConfig"]
            self.assertEqual(voice_config["prebuiltVoiceConfig"]["voiceName"], "Charon")

    def test_one_attempt_per_model_and_22_second_spacing_even_on_429(self):
        wav_bytes = wav_sample()
        responses = [
            (429, b'{"error":{"status":"RESOURCE_EXHAUSTED"}}'),
            (200, response_with_audio(wav_bytes, "audio/wav")),
            (200, response_with_audio(wav_bytes[44:], "audio/L16;rate=24000")),
        ]
        clock = [0.0]
        waits = []

        def sleep(seconds):
            waits.append(seconds)
            clock[0] += seconds

        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(comparison, "post_once", side_effect=responses) as post:
                with mock.patch.object(comparison.time, "monotonic", side_effect=lambda: clock[0]):
                    with mock.patch.object(comparison.time, "sleep", side_effect=sleep):
                        manifest = comparison.run(Path(folder), "test-key")
            self.assertEqual(post.call_count, 3)
            self.assertEqual([call.args[0] for call in post.call_args_list], list(comparison.MODELS))
            self.assertEqual(waits, [22.0, 22.0])
            self.assertEqual([item["attempts"] for item in manifest["results"]], [1, 1, 1])
            self.assertEqual([item["status"] for item in manifest["results"]], ["error", "ok", "ok"])
            self.assertEqual(manifest["results"][0]["http_status"], 429)
            for item in manifest["results"][1:]:
                self.assertEqual(item["duration_seconds"], 1.0)
                self.assertTrue((Path(folder) / item["file"]).is_file())
            self.assertTrue((Path(folder) / "manifest.json").is_file())

    def test_no_key_writes_manifest_without_requests(self):
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(comparison, "post_once") as post:
                manifest = comparison.run(Path(folder), "")
            post.assert_not_called()
            self.assertEqual({item["status"] for item in manifest["results"]}, {"not_attempted"})
            self.assertTrue((Path(folder) / "manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
