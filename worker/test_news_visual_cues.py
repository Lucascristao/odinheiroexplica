"""Pinned authentic pixels must survive capture; stale marks must fail closed."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from auto_capture_sources import capture_asset


class PinnedCaptureTests(unittest.TestCase):
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
