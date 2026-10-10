"""Regression tests for early news packaging validation."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "worker"))
from build_youtube_package import validate_publication_fields


def editorial(hashtags):
    return {
        "description": (
            "Dólar abaixo de cinco reais e a Bolsa em recorde histórico. "
            "Entenda os efeitos para o bolso e os investimentos."
        ),
        "seo": {"primary_keyword": "dólar"},
        "engagement_question": "O dólar mais baixo mudou algo para você?",
        "hashtags": hashtags,
    }


class NewsPublicationPreflightTests(unittest.TestCase):
    def test_one_to_three_hashtags_are_valid(self):
        for tags in (
            ["#Ibovespa"],
            ["#Ibovespa", "#Dolar"],
            ["#Ibovespa", "#Dolar", "#Bolsa"],
        ):
            with self.subTest(tags=tags):
                self.assertEqual(
                    validate_publication_fields(editorial(tags), "Dólar abaixo de R$ 5: quem ganha?"),
                    tags,
                )

    def test_empty_excessive_or_repeated_tags_fail_before_voice(self):
        for tags in ([], ["#A", "#B", "#C", "#D"], ["#Ibovespa", "#ibovespa"], ["Ibo vespa"]):
            with self.subTest(tags=tags):
                with self.assertRaises(RuntimeError):
                    validate_publication_fields(editorial(tags), "Dólar abaixo de R$ 5: quem ganha?")

    def test_description_does_not_duplicate_generated_sections(self):
        for addition in (" #Ibovespa", "\n\nFontes: B3", "\n\nCapítulos\n0:00 Abertura", " https://example.com"):
            with self.subTest(addition=addition):
                p = editorial(["#Ibovespa"])
                p["description"] += addition
                with self.assertRaises(RuntimeError):
                    validate_publication_fields(p, "Dólar abaixo de R$ 5: quem ganha?")


if __name__ == "__main__":
    unittest.main()
