"""Offline regressions for the public YouTube package."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_youtube_package import compose_description, unique_nonempty


class YoutubePackageTests(unittest.TestCase):
    def test_description_sections_are_ordered_once(self):
        result = compose_description(
            "Pix por aproximação mudou.\n\n- Um\n- Dois\n- Três",
            "0:00 Abertura\n0:20 Limites\n0:40 Segurança",
            "- Fonte A\n- Fonte B",
            "- Banco Central — uso editorial",
            "Você usaria essa função?",
            ["#Pix", "#ODinheiroExplica", "#EducacaoFinanceira"],
        )
        self.assertLess(result.index("Pix por aproximação"), result.index("CAPÍTULOS"))
        self.assertLess(result.index("CAPÍTULOS"), result.index("FONTES"))
        self.assertLess(result.index("FONTES"), result.index("Você usaria"))
        self.assertTrue(result.rstrip().endswith("#Pix #ODinheiroExplica #EducacaoFinanceira"))
        self.assertEqual(result.count("FONTES"), 1)

    def test_duplicate_sources_and_credits_are_removed(self):
        self.assertEqual(unique_nonempty(["Fonte A", "fonte a", "Fonte B", ""]), ["Fonte A", "Fonte B"])

    def test_editorial_body_cannot_embed_generated_sections(self):
        with self.assertRaises(RuntimeError):
            compose_description(
                "Gancho.\n\nFontes:\n- Fonte A",
                "",
                "- Fonte A",
                "",
                "Pergunta?",
                ["#A", "#B", "#C"],
            )


if __name__ == "__main__":
    unittest.main()
