"""Não poluir a imagem editorial com avisos; preservar a proveniência real."""
import json
import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from news_reconstruction import GOLD, PAPER, render_reconstruction, prepare_source_fallbacks
from news_quality_contract import editorial_fingerprint


class EditorialReconstructionVisualTests(unittest.TestCase):
    def episode(self):
        ep = {'news_date': '2026-11-10', 'title': 'Pix: a mudança que exige atenção ao prazo',
            'sources': [{'id': 'S1', 'publisher': 'Veículo Exemplo', 'published_at': '2026-11-10'}],
            'verified_facts': [{'claim': 'A aplicação da medida depende das condições expressas no documento.', 'source_ids': ['S1']}],
            'documentary_evidence': [{'id': 'doc-1', 'source_id': 'S1'}]}
        ep['editorial_quality'] = {'reviewed_content_sha256': editorial_fingerprint(ep),
                                  'review': {'approved': True, 'issues': []}}
        return ep

    def test_browser_fallback_copies_exact_reviewed_title_fact_and_source(self):
        ep = self.episode()
        prepare_source_fallbacks(ep)
        rec = ep['documentary_evidence'][0]['editorial_reconstruction']
        self.assertEqual(rec['headline'], ep['title'])
        self.assertEqual(rec['context'], ep['verified_facts'][0]['claim'])
        self.assertEqual(rec['publisher'], ep['sources'][0]['publisher'])
        self.assertEqual(ep['editorial_quality']['reviewed_content_sha256'], editorial_fingerprint(ep))

    def test_missing_rejected_or_stale_review_never_enables_automatic_fallback(self):
        for case in ('missing', 'rejected', 'stale', 'pinned', 'historical'):
            ep = copy.deepcopy(self.episode())
            if case == 'missing': ep.pop('editorial_quality')
            if case == 'rejected': ep['editorial_quality']['review']['approved'] = False
            if case == 'stale': ep['title'] += ' com outra promessa'
            if case == 'pinned': ep['documentary_evidence'][0]['capture_sha256'] = 'a' * 64
            if case == 'historical': ep['news_date'] = '2026-10-09'
            with self.subTest(case=case):
                prepare_source_fallbacks(ep)
                self.assertNotIn('editorial_reconstruction', ep['documentary_evidence'][0])

    def test_cover_never_presents_reconstruction_as_an_original_document(self):
        from news_auto_local_cover import make_background
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            capture = root / 'research/captures/report.png'
            capture.parent.mkdir(parents=True)
            Image.effect_noise((800, 500), 30).convert('RGB').save(capture)
            capture.with_suffix('.provenance.json').write_text(json.dumps({
                'kind': 'editorial_reconstruction', 'not_original_screenshot': True}), encoding='utf-8')
            episode = {'episode_id': 'fixture-test', 'documentary_evidence': [{'capture_file': 'research/captures/report.png'}]}
            with self.assertRaisesRegex(ValueError, 'nenhum documento real'):
                make_background(root, {}, episode)
            capture.with_suffix('.provenance.json').write_text(json.dumps({'mode': 'authentic_page_capture'}), encoding='utf-8')
            self.assertTrue(make_background(root, {}, episode).is_file())

    def test_clean_editorial_visual_and_machine_readable_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            asset = {
                "source_id": "S1",
                "source_page_url": "https://example.org/economia/noticia-sobre-pix",
                "capture_file": "research/captures/report.png",
                "editorial_reconstruction": {
                    "headline": "Pix ultrapassa um bilhão de chaves cadastradas",
                    "context": "Uma pessoa pode cadastrar mais de uma chave Pix. "
                               "O número de chaves não representa pessoas únicas.",
                    "publisher": "Veículo Exemplo",
                    "published_at": "2026-10-09",
                },
            }
            recorded_texts = []
            original_text = ImageDraw.ImageDraw.text

            def record_text(draw, xy, text, *args, **kwargs):
                recorded_texts.append(text)
                return original_text(draw, xy, text, *args, **kwargs)

            with patch.object(ImageDraw.ImageDraw, "text", record_text):
                image_path = render_reconstruction(asset, root, "captura indisponível")
            self.assertTrue(image_path.is_file())
            with Image.open(image_path) as image:
                self.assertEqual(image.size, (1920, 1080))
                # Não há mais faixas escuras de aviso no alto nem no rodapé.
                self.assertEqual(image.getpixel((10, 66)), tuple(bytes.fromhex(PAPER.lstrip("#"))))
                self.assertEqual(image.getpixel((1800, 1045)), tuple(bytes.fromhex(PAPER.lstrip("#"))))
                self.assertEqual(image.getpixel((800, 6)), tuple(bytes.fromhex(GOLD.lstrip("#"))))
            words = " ".join(recorded_texts)
            for forbidden in ("RECONSTRUÇÃO EDITORIAL", "NÃO É PRINT DO PORTAL",
                              "Resumo editorial, não reprodução da página",
                              "NOTÍCIA EM CONTEXTO"):
                self.assertNotIn(forbidden, words)
            self.assertIn("O DINHEIRO EXPLICA", recorded_texts)
            self.assertTrue(any('Resumo editorial' in text for text in recorded_texts))
            self.assertTrue(any("Fonte: Veículo Exemplo" in text for text in recorded_texts))
            provenance = json.loads(image_path.with_suffix(".provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(provenance["kind"], "editorial_reconstruction")
            self.assertIs(provenance["not_original_screenshot"], True)
            self.assertEqual(provenance["source_page_url"], asset["source_page_url"])
            self.assertEqual(provenance["capture_error"], "captura indisponível")


if __name__ == "__main__":
    unittest.main()
