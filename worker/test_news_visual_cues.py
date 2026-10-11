"""Pinned authentic pixels must survive capture; stale marks must fail closed."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from auto_capture_sources import capture_asset


class PinnedCaptureTests(unittest.TestCase):
    def test_desktop_context_requires_the_bound_companion_pixels(self):
        from PIL import Image
        with TemporaryDirectory() as dirname:
            directory=Path(dirname)
            path=directory/'proof.png'
            Image.new('RGB',(1360,900),'white').save(path)
            asset={'id':'proof','type':'source_excerpt','source_page_url':'https://example.org/news/verified-document',
                   'expected_text':'Verified proof','capture_file':'research/captures/proof.png',
                   'capture_scope':'desktop_context','capture_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            context=directory/'proof.context.png'
            Image.new('RGB',(960,900),'blue').save(context)
            proof={'mode':'authentic_page_capture','image_sha256':asset['capture_sha256'],
                   'source_page_url':asset['source_page_url'],'expected_text':asset['expected_text'],
                   'captured_at':'2026-10-11T05:10:00+00:00','capture_scope':'desktop_context',
                   'context_image_sha256':hashlib.sha256(context.read_bytes()).hexdigest()}
            path.with_suffix('.provenance.json').write_text(json.dumps(proof),encoding='utf-8')
            self.assertTrue(capture_asset(asset,directory,None))
            context.write_bytes(b'altered context pixels')
            with self.assertRaisesRegex(RuntimeError,'manchete ausente ou alterada'):
                capture_asset(asset,directory,None)
            context.unlink()
            with self.assertRaisesRegex(RuntimeError,'manchete ausente ou alterada'):
                capture_asset(asset,directory,None)

    def test_paragraph_only_capture_cannot_claim_desktop_context(self):
        from PIL import Image
        with TemporaryDirectory() as dirname:
            directory=Path(dirname)
            path=directory/'proof.png'
            Image.new('RGB',(1436,268),'white').save(path)
            asset={'id':'proof','type':'source_excerpt','source_page_url':'https://example.org/news/verified-document',
                   'expected_text':'A literal phrase on the verified document','capture_file':'research/captures/proof.png',
                   'capture_scope':'desktop_context','capture_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            proof={'mode':'authentic_page_capture','image_sha256':asset['capture_sha256'],'source_page_url':asset['source_page_url'],
                   'expected_text':asset['expected_text'],'captured_at':'2026-10-11T05:10:00+00:00','capture_scope':'desktop_context'}
            receipt=path.with_suffix('.provenance.json')
            receipt.write_text(json.dumps(proof),encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError,'só um bloco'):
                capture_asset(asset,directory,None)
            # Full authentic PDF pages use their own provenance, not HTML viewport rules.
            proof['mode']='authentic_pdf_page'
            Image.new('RGB',(1192,1684),'white').save(path)
            asset['capture_sha256']=proof['image_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            receipt.write_text(json.dumps(proof),encoding='utf-8')
            self.assertTrue(capture_asset(asset,directory,None))

    def test_pinned_capture_binds_pixels_url_and_literal(self):
        with TemporaryDirectory() as dirname:
            directory=Path(dirname)
            path=directory/'proof.png'
            path.write_bytes(b'authentic proof pixels')
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            asset={'id':'proof','type':'source_excerpt','source_page_url':'https://example.org/news/verified-document',
                   'expected_text':'A literal phrase on the verified document',
                   'capture_file':'research/captures/proof.png','capture_sha256':digest}
            proof={'mode':'authentic_page_capture','image_sha256':digest,'source_page_url':asset['source_page_url'],
                   'expected_text':asset['expected_text'],'captured_at':'2026-10-11T03:00:00+00:00'}
            receipt=path.with_suffix('.provenance.json')
            receipt.write_text(json.dumps(proof),encoding='utf-8')
            self.assertTrue(capture_asset(asset,directory,None))
            proof['source_page_url']='https://example.org/news/another-document'
            receipt.write_text(json.dumps(proof),encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError,'Proveniência'):
                capture_asset(asset,directory,None)
            path.write_bytes(b'changed proof pixels')
            with self.assertRaisesRegex(RuntimeError,'ausente/alterada'):
                capture_asset(asset,directory,None)


if __name__=='__main__':
    unittest.main()
