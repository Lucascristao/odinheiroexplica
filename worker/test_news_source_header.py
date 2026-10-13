"""Offline structural publisher-markup fixtures; these are not captured news pages."""
import argparse
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


ARGS = argparse.ArgumentParser(add_help=False)
ARGS.add_argument("--module", default=str(Path(__file__).with_name("news_source_corpus.py")))
OPTIONS, TEST_ARGS = ARGS.parse_known_args()


class RequestException(Exception):
    pass


REQUESTS = types.ModuleType("requests")
REQUESTS.RequestException = RequestException
REQUESTS.get = Mock()
DECODER = types.ModuleType("gnews_decoder")
DECODER.decode_many = Mock(return_value={})
SPEC = importlib.util.spec_from_file_location("source_header_review", OPTIONS.module)
CORPUS = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"requests": REQUESTS, "gnews_decoder": DECODER}):
    SPEC.loader.exec_module(CORPUS)

BODY = (
    "A comissão publicou uma decisão nesta manhã. "
    "O documento descreve o procedimento aprovado e preserva o prazo de recurso. "
    "A aplicação depende das condições expressamente indicadas. "
    "Os interessados poderão consultar o texto integral no processo."
)
ARTICLE = (
    "<html><head><title>SITE_HEAD_MARKER</title>"
    "<script>SCRIPT_MARKER</script></head><body>"
    "<header role='banner'>SITE_HEADER_MARKER<nav>SITE_NAV_MARKER</nav></header>"
    "<article><header><h1>Título visível da decisão</h1>"
    "<time datetime='2026-10-13T08:32:00-03:00'>13 de outubro de 2026, às 08h32</time>"
    "<span>Autoria visível</span><nav>ARTICLE_NAV_MARKER</nav>"
    "</header><p>" + BODY + "</p></article>"
    "<footer>SITE_FOOTER_MARKER</footer></body></html>"
)


class Response:
    def __init__(self, html):
        self.text = html
        self.url = "https://publisher.example/politica/decisao"
        self.headers = {"Content-Type": "text/html"}

    def raise_for_status(self):
        pass


class HeaderExtraction(unittest.TestCase):
    def setUp(self):
        REQUESTS.get.reset_mock(return_value=True, side_effect=True)

    def test_article_header_preserves_visible_title_and_date(self):
        text = CORPUS.extract_article(ARTICLE)
        self.assertIn("Título visível da decisão", text)
        self.assertIn("13 de outubro de 2026, às 08h32", text)
        self.assertIn("Autoria visível", text)
        self.assertIn(BODY, text)

    def test_site_header_nav_head_scripts_and_footer_remain_excluded(self):
        text = CORPUS.extract_article(ARTICLE)
        for marker in (
            "SITE_HEAD_MARKER", "SCRIPT_MARKER", "SITE_HEADER_MARKER",
            "SITE_NAV_MARKER", "ARTICLE_NAV_MARKER", "SITE_FOOTER_MARKER",
        ):
            self.assertNotIn(marker, text)

    def test_hidden_article_header_still_stays_hidden(self):
        for declaration in ("hidden", "aria-hidden='true'", "style='display:none'"):
            with self.subTest(declaration=declaration):
                html = (
                    "<article><header " + declaration + ">"
                    "<h1>HIDDEN_HEADLINE_MARKER</h1>"
                    "<time>HIDDEN_DATE_MARKER</time></header><p>" + BODY + "</p></article>"
                )
                text = CORPUS.extract_article(html)
                self.assertNotIn("HIDDEN_HEADLINE_MARKER", text)
                self.assertNotIn("HIDDEN_DATE_MARKER", text)
                self.assertIn(BODY, text)

    def test_banner_inside_article_is_still_a_site_header(self):
        html = (
            "<article><header role='banner'><h1>BANNER_MARKER</h1></header>"
            "<p>" + BODY + "</p></article>"
        )
        self.assertNotIn("BANNER_MARKER", CORPUS.extract_article(html))

    def test_main_without_article_does_not_reclassify_site_header(self):
        html = (
            "<main><header><h1>MAIN_SITE_HEADER_MARKER</h1></header>"
            "<p>" + BODY + "</p></main>"
        )
        text = CORPUS.extract_article(html)
        self.assertNotIn("MAIN_SITE_HEADER_MARKER", text)
        self.assertIn(BODY, text)

    def test_body_only_mode_preserves_the_previous_admission_measure(self):
        text = CORPUS.extract_article(ARTICLE, include_article_header=False)
        self.assertNotIn("Título visível", text)
        self.assertNotIn("13 de outubro", text)
        self.assertIn(BODY, text)
        self.assertGreaterEqual(len(text), 200)

    def test_large_header_does_not_make_an_empty_article_collectable(self):
        html = (
            "<article><header><h1>" + "Grande título editorial " * 20
            + "</h1><time>13 de outubro de 2026</time></header>"
            "<p>Corpo ainda indisponível.</p></article>"
        )
        self.assertGreater(len(CORPUS.extract_article(html)), 200)
        REQUESTS.get.return_value = Response(html)
        candidate = {
            "link": "https://publisher.example/politica/decisao",
            "title": "Grande título editorial", "category": "politics",
            "published_utc": "2026-10-13T11:32:00Z",
        }
        with patch.dict(sys.modules, {"gnews_decoder": DECODER}):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(RuntimeError):
                    CORPUS.collect_verified([candidate])


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]] + TEST_ARGS)
