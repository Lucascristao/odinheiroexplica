"""Não poluir a imagem editorial com avisos; preservar a proveniência real."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from news_reconstruction import GOLD, PAPER, render_reconstruction


class EditorialReconstructionVisualTests(unittest.TestCase):
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
            self.assertTrue(any("Fonte: Veículo Exemplo" in text for text in recorded_texts))
            provenance = json.loads(image_path.with_suffix(".provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(provenance["kind"], "editorial_reconstruction")
            self.assertIs(provenance["not_original_screenshot"], True)
            self.assertEqual(provenance["source_page_url"], asset["source_page_url"])
            self.assertEqual(provenance["capture_error"], "captura indisponível")


if __name__ == "__main__":
    unittest.main()
