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

    def test_expression_is_fixed_and_old_contract_stays_unchanged(self):
        path = self.root / "worker/presenter-identity.json"
        policy = json.loads(path.read_text())
        policy.update(expressions_enabled_after_utc="2026-10-11T05:00:00+00:00", default_new_news_presenter="roberto-v1-engaged")
        variant = {**self.identity, "id": "roberto-v1-engaged", "reference_path": "video/public/presenters/roberto/roberto-v1-engaged.png"}
        expression_path = self.root / variant["reference_path"]
        expression_path.write_bytes(b"reviewed expression of the same Roberto")
        variant["reference_sha256"] = hashlib.sha256(expression_path.read_bytes()).hexdigest()
        policy["identities"][variant["id"]] = {k:v for k,v in variant.items() if k != "id"}
        path.write_text(json.dumps(policy))
        self.assertEqual(news_presenter_contract("2026-10-11", self.root, reviewed_at="2026-10-11T04:06:34+00:00"), self.identity)
        self.assertEqual(news_presenter_contract("2026-10-11", self.root, reviewed_at="2026-10-11T02:30:00-03:00"), variant)
        self.assertEqual(validate_locked_portrait(self.root, variant), expression_path)
        expression_path.write_bytes(b"substituted face")
        with self.assertRaisesRegex(ValueError, "retrato oficial alterado"):
            validate_locked_portrait(self.root, variant)
        with self.assertRaisesRegex(ValueError, "catálogo"):
            news_presenter_contract("2026-10-11", self.root, expression="unknown-face")


    def test_wardrobe_variants_preserve_history_and_rotate_stably_by_window(self):
        path = self.root / "worker/presenter-identity.json"
        policy = json.loads(path.read_text())
        variants = ["roberto-left", "roberto-right", "roberto-front"]
        policy.update(variants_enabled_after_utc="2026-10-11T22:00:00+00:00", news_variant_ids=variants)
        for variant in variants:
            policy["identities"][variant] = {k: v for k, v in self.identity.items() if k != "id"}
        path.write_text(json.dumps(policy))
        before = "2026-10-11T21:59:59Z"
        after = "2026-10-11T19:00:00-03:00"
        selected = []
        for slot in ("manha", "meio-dia", "noite"):
            key = "noticia-2026-10-11-" + slot
            self.assertEqual(news_presenter_contract("2026-10-11", self.root, reviewed_at=before, variant_key=key), self.identity)
            actual = news_presenter_contract("2026-10-11", self.root, reviewed_at=after, variant_key=key)
            self.assertEqual(actual, news_presenter_contract("2026-10-11", self.root, reviewed_at=after, variant_key=key))
            selected.append(actual["id"])
        self.assertEqual(set(selected), set(variants))
        self.assertEqual(news_presenter_contract("2026-10-11", self.root, reviewed_at=after, expression=variants[0], variant_key="noticia-2026-10-11-noite")["id"], variants[0])
        with self.assertRaisesRegex(ValueError, "catálogo"):
            news_presenter_contract("2026-10-11", self.root, reviewed_at=before, expression=variants[0])
        with self.assertRaisesRegex(ValueError, "catálogo"):
            news_presenter_contract("2026-10-11", self.root, expression=variants[0])
        with self.assertRaisesRegex(ValueError, "catálogo"):
            news_presenter_contract("2026-10-11", self.root, reviewed_at=after, expression="unknown-face")


if __name__ == "__main__":
    unittest.main()
