"""Offline recovery guards: no network, synthesis, DSP or encoding."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

try:
    import requests
except ModuleNotFoundError:
    # Network is always mocked below; the guard suite needs only the stdlib.
    sys.modules["requests"] = types.SimpleNamespace(RequestException=RuntimeError)

import restore_completed_render as recovery


class RecoveryGuards(unittest.TestCase):
    def setUp(self):
        task_work = Path(__file__).resolve().parents[1] / "work"
        task_work.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=task_work)
        self.root = Path(self.temp.name).resolve()
        self.artifact = self.root / "work/completed-render"
        self.artifact.mkdir(parents=True)
        self.project = {"project_id": "fixture", "scenes": [{"id": "scene-01", "narration": "Teste."}],
                        "visual_assets": [{"id": "source-rule", "type": "source_excerpt",
                                           "source_url": "https://example.com/rule", "expected_text": "Regra literal."}]}
        self.put("video/data/daily.json", self.project)
        self.put("video/generated/daily-project.json", self.project)
        self.audio, self.master, self.video = b"fixture-raw", b"fixture-master", b"fixture-mp4"
        sha = lambda data: hashlib.sha256(data).hexdigest()
        self.put("video/generated/daily-render-input.json",
                 {"fps": 30, "duration_in_frames": 30, "scenes": [{"id": "scene-01"}],
                  "narration_master_audio": "processed-audio/daily/master.wav",
                  "voice_master": {"master_sha256": sha(self.master)}})
        self.put("video/generated/daily-aligned-tts-manifest.json",
                 {"scenes": [{"id": "scene-01", "file": "scene-01.wav", "audio_sha256": sha(self.audio)}]})
        self.put("video/generated/daily-delivery-qa.json",
                 {"status": "warn", "failures": [], "scenes": [{"id": "scene-01"}],
                  "video": {"sha256": sha(self.video)}})
        for path, value in [("public/generated-audio/daily/scene-01.wav", self.audio),
                            ("public/processed-audio/daily/scene-01.wav", self.audio),
                            ("public/processed-audio/daily/master.wav", self.master),
                            ("render-output/daily-video.mp4", self.video),
                            ("render-output/daily-youtube.json", {"title": "Fixture"}),
                            ("render-output/daily-youtube.txt", b"Fixture")]:
            self.put(path, value)
        self.source = self.root / "video/data/daily.json"
        self.source.parent.mkdir(parents=True)
        self.source.write_text(json.dumps(self.project), encoding="utf-8")
        self.original = self.source.read_bytes()

    def tearDown(self):
        self.temp.cleanup()

    def put(self, relative, value):
        path = self.artifact / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else json.dumps(value).encode())

    def invoke(self):
        def fake_git(root, *args):
            if args[0] == "show":
                return json.dumps(self.project)
            return "b" * 40 if args[0] == "rev-parse" else ""
        with patch.object(recovery, "verify_source_run", return_value=(
                {"head_sha": "a" * 40}, {"id": 12, "digest": "sha256:" + "c" * 64})), \
                patch.object(recovery, "git", side_effect=fake_git):
            return recovery.restore(self.root, self.artifact, "owner/repo", "mock-token", "123")

    def test_restore_preserves_source_and_excludes_code(self):
        self.put("video/src/evil.ts", b"never execute")
        receipt = self.invoke()
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertEqual((self.root / "render-output/daily-video.mp4").read_bytes(), self.video)
        self.assertFalse((self.root / "video/src/evil.ts").exists())
        self.assertFalse(receipt["new_render"])
        self.assertFalse(receipt["new_synthesis"])

    def test_accepts_only_derived_capture_metadata(self):
        generated = copy.deepcopy(self.project)
        generated["visual_assets"][0].update(captured_at="2026-10-07T07:00:00Z",
                                             capture_file="research/captures/source-rule.png")
        self.put("video/generated/daily-project.json", generated)
        self.invoke()
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_rejects_changed_capture_path(self):
        generated = copy.deepcopy(self.project)
        generated["visual_assets"][0]["capture_file"] = "research/captures/another-source.png"
        self.put("video/generated/daily-project.json", generated)
        with self.assertRaisesRegex(RuntimeError, "captura automática"):
            self.invoke()

    def test_rejects_changed_literal_evidence(self):
        generated = copy.deepcopy(self.project)
        generated["visual_assets"][0]["expected_text"] = "Regra inventada."
        self.put("video/generated/daily-project.json", generated)
        with self.assertRaisesRegex(RuntimeError, "divergem"):
            self.invoke()

    def test_mp4_tamper_refused_before_copy(self):
        self.put("render-output/daily-video.mp4", b"changed")
        with self.assertRaisesRegex(RuntimeError, "QA original"):
            self.invoke()
        self.assertFalse((self.root / "render-output").exists())

    def test_project_tamper_refused_before_copy(self):
        self.put("video/generated/daily-project.json", {"scenes": [{"id": "other"}]})
        with self.assertRaisesRegex(RuntimeError, "divergem"):
            self.invoke()
        self.assertFalse((self.root / "render-output").exists())

    def test_raw_audio_tamper_refused_before_copy(self):
        self.put("public/generated-audio/daily/scene-01.wav", b"changed")
        with self.assertRaisesRegex(RuntimeError, "byte-id"):
            self.invoke()
        self.assertFalse((self.root / "render-output").exists())

    def test_destination_traversal_refused(self):
        with self.assertRaisesRegex(RuntimeError, "fora"):
            recovery.safe_destination(self.root, "../escape.mp4")

    def test_downloaded_link_refused(self):
        original_method = Path.is_symlink
        with patch.object(Path, "is_symlink", lambda p: True if p == self.artifact else original_method(p)):
            with self.assertRaisesRegex(RuntimeError, "simb"):
                recovery.safe_tree(self.artifact)

    def test_invalid_run_does_not_contact_api(self):
        with patch.object(recovery, "github") as request:
            with self.assertRaisesRegex(RuntimeError, "ID positivo"):
                recovery.verify_source_run("owner/repo", "mock-token", "../123")
            request.assert_not_called()

    def test_fork_refused(self):
        run = {"id": 123, "status": "completed", "head_branch": "main", "conclusion": "failure",
               "path": ".github/workflows/render-daily.yml", "head_sha": "a" * 40,
               "repository": {"full_name": "owner/repo", "id": 1},
               "head_repository": {"full_name": "fork/repo", "id": 2}}
        with patch.object(recovery, "github", return_value=run):
            with self.assertRaisesRegex(RuntimeError, "fork"):
                recovery.verify_source_run("owner/repo", "mock-token", "123")

    def test_api_provenance_real_metadata_shape(self):
        run = {"id": 123, "status": "completed", "head_branch": "main", "conclusion": "failure",
               "path": ".github/workflows/render-daily.yml", "head_sha": "a" * 40, "run_attempt": 1,
               "repository": {"full_name": "owner/repo", "id": 1},
               "head_repository": {"full_name": "owner/repo", "id": 1}}
        jobs = {"jobs": [{"steps": [{"name": name, "conclusion": "success"} for name in
                ["Render video with live progress", "Verify delivery before Drive", "Upload production review artifact"]]}]}
        artifacts = {"artifacts": [{"id": 12, "name": "daily-production-review", "expired": False,
                                   "size_in_bytes": 12345, "digest": "sha256:" + "c" * 64,
                                   "workflow_run": {"id": 123, "head_sha": "a" * 40}}]}
        with patch.object(recovery, "github", side_effect=[run, jobs, artifacts]):
            proven_run, artifact = recovery.verify_source_run("owner/repo", "mock-token", "123")
            self.assertEqual(proven_run["head_sha"], "a" * 40)
            self.assertEqual(artifact["id"], 12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
