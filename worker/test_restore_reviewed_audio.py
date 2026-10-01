"""Offline provenance checks for restoring reviewed audio without synthesis."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile


requests_stub = types.ModuleType("requests")
requests_stub.Response = object
requests_stub.RequestException = type("OfflineRequestError", (Exception,), {})
requests_stub.exceptions = types.SimpleNamespace(Timeout=type("OfflineTimeout", (Exception,), {}))


def forbid_network(*_args, **_kwargs):
    raise AssertionError("Audio restore regression must never call a provider or GitHub.")


requests_stub.get = forbid_network
requests_stub.post = forbid_network
sys.modules["requests"] = requests_stub
sys.path.insert(0, str(Path(__file__).resolve().parent))
import restore_reviewed_audio as restore  # noqa: E402
import synthesize_scenes as synth  # noqa: E402
from tts_config import project_speech_fingerprint, voice_policy_fingerprint  # noqa: E402


class ReviewedAudioRestoreTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.output = self.root / "audio"
        self.project = {
            "project_id": "reviewed-project",
            "presenter": {"gender": "male"},
            "scenes": [{"index": 0, "narration": "O dólar pode subir."}],
        }
        self.audio = b"RIFF" + b"reviewed-original-audio" * 100
        self.scene = {
            "id": "scene-00", "file": "scene-00.wav", "duration_seconds": 2.5,
            "engine": "google-gemini-live", "model": synth.PRIMARY_TTS_MODEL,
            "voice": "Charon", "voice_treatment": "none", "fallback_reason": None,
            "narration_sha256": hashlib.sha256(b"O d\xc3\xb3lar pode subir.").hexdigest(),
            "audio_sha256": hashlib.sha256(self.audio).hexdigest(),
            "voice_policy_fingerprint": voice_policy_fingerprint(synth.PRIMARY_TTS_MODEL, "Charon"),
            "speech_profile_fingerprint": project_speech_fingerprint(self.project),
            "output_transcription": "O dólar pode subir.",
            "output_transcription_similarity": 1.0,
        }
        self.provenance = {"artifact_id": 1, "run_id": 2, "archive_sha256": "a" * 64}

    def archive(self, scene):
        path = self.root / "review.zip"
        manifest = {"engine": "google-gemini-live", "voice": "Charon", "scenes": [scene]}
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("video/generated/daily-tts-manifest.json", json.dumps(manifest))
            archive.writestr("video/generated/daily-render-input.json", json.dumps(self.project))
            archive.writestr("public/generated-audio/daily/scene-00.wav", self.audio)
        return path

    def test_matching_policy_restores_original_bytes_and_provenance(self):
        archive = self.archive(self.scene)
        with (
            patch.object(restore, "duration_seconds", return_value=2.5),
            patch.object(synth, "duration_seconds", return_value=2.5),
        ):
            self.assertEqual(restore.restore(self.project, archive, self.output, self.provenance), (1, 0))
        audio = self.output / "scene-00.wav"
        self.assertEqual(audio.read_bytes(), self.audio)
        sidecar = json.loads(audio.with_suffix(".tts.json").read_text(encoding="utf-8"))
        self.assertEqual(sidecar["voice_policy_fingerprint"], self.scene["voice_policy_fingerprint"])
        self.assertEqual(sidecar["audio_sha256"], self.scene["audio_sha256"])
        self.assertEqual(sidecar["restored_from_artifact"], self.provenance)

    def test_legacy_without_policy_is_not_reclassified_as_current(self):
        scene = dict(self.scene)
        scene.pop("voice_policy_fingerprint")
        with patch.object(restore, "save_audio_sidecar", side_effect=AssertionError("Legacy must be skipped")):
            self.assertEqual(restore.restore(self.project, self.archive(scene), self.output, self.provenance), (0, 1))
        self.assertFalse((self.output / "scene-00.wav").exists())

    def test_legacy_fixed_eq_is_skipped_without_blocking_new_synthesis(self):
        scene = {
            **self.scene, "model": synth.FALLBACK_TTS_MODEL,
            "voice_treatment": "charon-3.1-to-3.8-eq-v1",
        }
        scene.pop("voice_policy_fingerprint")
        with patch.object(restore, "save_audio_sidecar", side_effect=AssertionError("Legacy EQ must be skipped")):
            self.assertEqual(restore.restore(self.project, self.archive(scene), self.output, self.provenance), (0, 1))

    def test_different_policy_is_not_reused(self):
        scene = {**self.scene, "voice_policy_fingerprint": "0" * 64}
        with patch.object(restore, "save_audio_sidecar", side_effect=AssertionError("Different policy must be skipped")):
            self.assertEqual(restore.restore(self.project, self.archive(scene), self.output, self.provenance), (0, 1))

    def test_changed_narration_is_left_pending(self):
        archive = self.archive(self.scene)
        current = {**self.project, "scenes": [{"index": 0, "narration": "A cotação mudou."}]}
        self.assertEqual(restore.restore(current, archive, self.output, self.provenance), (0, 1))
        self.assertFalse((self.output / "scene-00.wav").exists())

    def test_zip_traversal_is_rejected(self):
        archive = self.archive(self.scene)
        with zipfile.ZipFile(archive, "a") as payload:
            payload.writestr("../outside.wav", self.audio)
        with self.assertRaisesRegex(RuntimeError, "caminho inseguro"):
            restore.restore(self.project, archive, self.output, self.provenance)


if __name__ == "__main__":
    unittest.main()
