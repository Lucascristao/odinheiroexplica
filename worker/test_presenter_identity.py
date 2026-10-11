"""A new face, stale composition or missing reference must not reach publication."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from presenter_identity import news_presenter_contract, validate_locked_portrait, validate_presenter_composition


class LockedIdentityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.portrait = self.root / "video/public/presenters/roberto/roberto-v1.png"
        self.portrait.parent.mkdir(parents=True)
        self.portrait.write_bytes(b"approved portrait pixels")
        self.identity = {"id": "roberto-v1", "mode": "locked_asset",
                         "reference_path": "video/public/presenters/roberto/roberto-v1.png",
                         "reference_sha256": hashlib.sha256(self.portrait.read_bytes()).hexdigest()}
        (self.root / "worker").mkdir()
        policy = {"version": "1.0", "news_enabled_since": "2026-10-11", "default_news_presenter": "roberto-v1",
                  "identities": {"roberto-v1": {k:v for k,v in self.identity.items() if k != "id"}}}
        (self.root / "worker/presenter-identity.json").write_text(json.dumps(policy), encoding="utf-8")
        self.directory = self.root / "production/noticia-test"
        self.directory.mkdir(parents=True)
        self.background = self.directory / "thumbnail-background.png"
        self.background.write_bytes(b"reviewed story background")
        self.receipt = {"version": "locked-presenter-cover-v1", "project_id": "noticia-test",
                        "contract_sha256": "contract", "identity_id": "roberto-v1",
                        "portrait_sha256": self.identity["reference_sha256"], "image_sha256": "image",
                        "background_path": "production/noticia-test/thumbnail-background.png",
                        "background_sha256": hashlib.sha256(self.background.read_bytes()).hexdigest(), "portrait_side": "right",
                        "headline_position": "middle", "portrait_size": "compact"}
        self.save()

    def save(self):
        (self.directory / "thumbnail-composition.json").write_text(json.dumps(self.receipt), encoding="utf-8")

    def check(self):
        return validate_presenter_composition(self.root, self.identity, "noticia-test", "contract", "image")

    def tearDown(self):
        self.tmp.cleanup()

    def test_old_episodes_keep_contract(self):
        self.assertIsNone(news_presenter_contract("2026-10-10", self.root))
        self.assertEqual(news_presenter_contract("2026-10-11", self.root), self.identity)

    def test_approved_asset_and_composition(self):
        self.assertEqual(validate_locked_portrait(self.root, self.identity), self.portrait)
        self.assertTrue(self.check().is_file())

    def test_new_face_rejected(self):
        self.portrait.write_bytes(b"another person's face")
        with self.assertRaisesRegex(ValueError, "retrato oficial alterado"):
            self.check()

    def test_unregistered_reference_rejected(self):
        changed = {**self.identity, "id": "another-person"}
        with self.assertRaisesRegex(ValueError, "identidade oficial"):
            validate_locked_portrait(self.root, changed)

    def test_missing_composition_rejected(self):
        (self.directory / "thumbnail-composition.json").unlink()
        with self.assertRaisesRegex(ValueError, "falta recibo"):
            self.check()

    def test_stale_receipt_rejected(self):
        for key in ("project_id", "contract_sha256", "portrait_sha256", "image_sha256"):
            with self.subTest(key=key):
                old = copy.deepcopy(self.receipt)
                self.receipt[key] = "changed"; self.save()
                with self.assertRaisesRegex(ValueError, "não corresponde"):
                    self.check()
                self.receipt = old; self.save()

    def test_changed_background_rejected(self):
        self.background.write_bytes(b"changed story")
        with self.assertRaisesRegex(ValueError, "fundo alterado"):
            self.check()


if __name__ == "__main__":
    unittest.main()
