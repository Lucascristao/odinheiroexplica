"""Offline integrity tests for editorial thumbnail attestations."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from thumbnail_contract import contract_sha256, normalized_project_sha256, validate_thumbnail_audit

CONTRACT = {
 "version":"1.0","exact_headline":"DESLIGOU. PAGOU.",
 "primary_subject":"Medidor de energia em close",
 "secondary_subject":"Fatura de luz simbólica ao fundo",
 "composition":"Texto à esquerda, medidor à direita",
 "visual_tension":"Quase sem consumo, mas conta chegou",
 "forbidden_elements":["rostos e pessoas","valores fictícios"],
 "palette":{"base":"#101114","accent":"#FFBD19","text":"#F6F7F8"},
 "format":{"width":1280,"height":720},"no_extra_text":True
}

class ThumbnailAuditTest(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.root=Path(self.temp.name)
  self.project={"project_id":"test-episode","packaging":{"thumbnails":[{"headline":"DESLIGOU. PAGOU.","concept":"Desligou e recebeu a cobrança","contract":CONTRACT}]}}
  (self.root/"video/data").mkdir(parents=True)
  (self.root/"video/data/daily.json").write_text(json.dumps(self.project),encoding="utf-8")
  self.directory=self.root/"production/test-episode"
  self.directory.mkdir(parents=True)
  self.image=self.directory/"thumbnail.jpg"
  self.image.write_bytes(b"fictional-jpeg-byte-payload")
  self.data={
   "version":"1.0","project_id":"test-episode",
   "project_sha256":normalized_project_sha256(self.root/"video/data/daily.json"),
   "contract_sha256":contract_sha256(CONTRACT),
   "image_sha256":hashlib.sha256(self.image.read_bytes()).hexdigest(),
   "headline":"DESLIGOU. PAGOU.","approval_status":"approved",
   "reviewer":"agent-visual-inspection","reviewed_at":"2026-10-08T20:30:00-03:00",
   "checks":{key:True for key in ("headline_exact","primary_subject","secondary_subject","forbidden_absent","identity_and_mobile","no_fabricated_data","unique_composition")},
   "observations":{key:f"Observei no quadro final: {key} conferido visualmente." for key in ("headline","primary_subject","secondary_subject","forbidden_absent","identity_and_mobile","no_fabricated_data","unique_composition")},
   "checked_forbidden_elements":list(CONTRACT["forbidden_elements"]),
   "observed_forbidden_elements":[]
  }
  self.save()
 def tearDown(self):self.temp.cleanup()
 def save(self):(self.directory/"thumbnail-audit.json").write_text(json.dumps(self.data),encoding="utf-8")
 def check(self):return validate_thumbnail_audit(self.root,self.project,self.image)
 def test_approved_matching(self):self.assertEqual(self.check()["contract_sha256"],contract_sha256(CONTRACT))
 def test_missing_review_blocks_upload(self):
  (self.directory/"thumbnail-audit.json").unlink()
  with self.assertRaisesRegex(ValueError,"ausente"):self.check()
 def test_swapped_image_blocks_upload(self):
  self.image.write_bytes(b"changed image")
  with self.assertRaisesRegex(ValueError,"capa alterada"):self.check()
 def test_changed_project_blocks_upload(self):
  (self.root/"video/data/daily.json").write_text(json.dumps({**self.project,"title":"changed"}),encoding="utf-8")
  with self.assertRaisesRegex(ValueError,"roteiro alterado"):self.check()
 def test_changed_contract_blocks_upload(self):
  self.project["packaging"]["thumbnails"][0]["contract"]={**CONTRACT,"primary_subject":"Um outro protagonista"}
  with self.assertRaisesRegex(ValueError,"contrato alterado"):self.check()
 def test_missing_exclusions_blocks_upload(self):
  self.data["checked_forbidden_elements"]=[];self.save()
  with self.assertRaisesRegex(ValueError,"exclusões"):self.check()
 def test_detected_prohibited_subject_blocks_upload(self):
  self.data["observed_forbidden_elements"]=["rosto"];self.save()
  with self.assertRaisesRegex(ValueError,"elemento proibido"):self.check()
 def test_false_check_blocks_upload(self):
  self.data["checks"]["forbidden_absent"]=False;self.save()
  with self.assertRaisesRegex(ValueError,"critérios"):self.check()
 def test_empty_visual_observation_blocks_upload(self):
  self.data["observations"]["primary_subject"]="ok";self.save()
  with self.assertRaisesRegex(ValueError,"evidência observada"):self.check()
 def test_different_project_path_blocks_upload(self):
  other=self.root/"production/another/thumbnail.jpg";other.parent.mkdir(parents=True);other.write_bytes(self.image.read_bytes())
  with self.assertRaisesRegex(ValueError,"canônico"):validate_thumbnail_audit(self.root,self.project,other)

if __name__=="__main__":unittest.main()
