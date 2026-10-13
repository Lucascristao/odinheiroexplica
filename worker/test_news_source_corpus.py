"""Behavioral newsroom-corpus checks; fixtures are invented test data, not news.

Run: python this_file.py --module PATH_TO_COLLECTOR.py -v
No HTTP or Google decoder call escapes the mocks. Does not invoke an LLM.
"""
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
ARGS.add_argument("--module", default="worker/news_source_corpus.py")
OPTIONS, UNITTEST_ARGS = ARGS.parse_known_args()


class RequestException(Exception):
    pass


REQUESTS = types.ModuleType("requests")
REQUESTS.RequestException = RequestException
REQUESTS.get = Mock(name="requests.get")
DECODER = types.ModuleType("gnews_decoder")
DECODER.decode_many = Mock(name="decode_many")

SPEC = importlib.util.spec_from_file_location(
    "tested_news_source_corpus", Path(OPTIONS.module).resolve()
)
CORPUS = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"requests": REQUESTS, "gnews_decoder": DECODER}):
    SPEC.loader.exec_module(CORPUS)


PARAGRAPH = (
    "A comissão informou que aprovou uma medida administrativa nesta manhã. "
    "O texto define o procedimento e preserva o prazo de recurso. "
    "A decisão será registrada no documento oficial e seus efeitos dependem das regras publicadas."
)
SHORT_HTML = (
    "<html><body><article><h1>Decisão publicada nesta manhã</h1>"
    "<p>" + PARAGRAPH + "</p></article></body></html>"
)
LONG_HTML = SHORT_HTML.replace(PARAGRAPH, PARAGRAPH * 4)


def candidate(url, title="Decisão publicada nesta manhã", category="politics"):
    return {
        "link": url, "title": title, "category": category,
        "published_utc": "2026-10-13T12:00:00Z",
    }


class Response:
    def __init__(self, url, html=LONG_HTML, status=200, content_type="text/html; charset=utf-8"):
        self.url = url
        self.text = html
        self.status_code = status
        self.headers = {"Content-Type": content_type}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RequestException("HTTP " + str(self.status_code))


class CorpusBehavior(unittest.TestCase):
    def setUp(self):
        REQUESTS.get.reset_mock(return_value=True, side_effect=True)
        DECODER.decode_many.reset_mock(return_value=True, side_effect=True)
        DECODER.decode_many.return_value = {}
        self.decoder_modules = patch.dict(sys.modules, {"gnews_decoder": DECODER})
        self.decoder_modules.start()
        self.addCleanup(self.decoder_modules.stop)

    def responses(self, mapping):
        def fetch(url, **kwargs):
            result = mapping[url]
            if isinstance(result, Exception):
                raise result
            return result
        REQUESTS.get.side_effect = fetch

    def collect(self, items, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return CORPUS.collect_verified(items, **kwargs)

    def assert_rejected(self, items):
        with self.assertRaises(RuntimeError):
            self.collect(items)

    def test_short_exclusive_article_from_one_real_publisher_is_usable(self):
        url = "https://portal-a.example/politica/nota-exclusiva"
        self.assertGreaterEqual(len(CORPUS.extract_article(SHORT_HTML)), 200)
        self.assertLess(len(CORPUS.extract_article(SHORT_HTML)), 550)
        self.responses({url: Response(url, SHORT_HTML)})
        docs = self.collect([candidate(url)])
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["url"], url)
        self.assertEqual(docs[0]["publisher_host"], "portal-a.example")
        self.assertIn(PARAGRAPH, docs[0]["actual_article_text"])

    def test_main_with_real_heading_and_paragraph_remains_acceptable(self):
        url = "https://portal-a.example/politica/nota-curta"
        self.responses({url: Response(url, SHORT_HTML.replace("article", "main"))})
        self.assertEqual(len(self.collect([candidate(url)])), 1)

    def test_article_below_minimum_length_is_not_evidence(self):
        url = "https://portal-a.example/politica/manchete-sem-corpo"
        html = "<article><h1>Um anúncio</h1><p>Confira em breve.</p></article>"
        self.responses({url: Response(url, html)})
        self.assert_rejected([candidate(url)])

    def test_navigation_only_page_is_not_a_real_article(self):
        url = "https://portal-a.example/politica/indice"
        html = "<html><main><h1>Últimas notícias</h1><ul>" + "".join(
            "<li><a href='/item'>" + PARAGRAPH + "</a></li>" for _ in range(8)
        ) + "</ul></main></html>"
        self.responses({url: Response(url, html)})
        self.assert_rejected([candidate(url)])

    def test_http_error_even_with_news_shaped_body_is_rejected(self):
        url = "https://portal-a.example/politica/inacessivel"
        self.responses({url: Response(url, LONG_HTML, status=403)})
        self.assert_rejected([candidate(url)])

    def test_soft_error_with_status_200_is_rejected(self):
        url = "https://portal-a.example/politica/bloqueado"
        html = (
            "<html><main><h1>Access denied</h1><p>"
            + ("You do not have permission to access this resource. " * 15)
            + "</p></main></html>"
        )
        self.responses({url: Response(url, html)})
        self.assert_rejected([candidate(url)])

    def test_non_html_payload_is_not_an_article(self):
        url = "https://portal-a.example/politica/arquivo"
        self.responses({url: Response(url, LONG_HTML, content_type="application/json")})
        self.assert_rejected([candidate(url)])

    def test_hidden_text_cannot_inflate_a_small_visible_note(self):
        url = "https://portal-a.example/politica/nota-incompleta"
        html = (
            "<article><h1>Uma decisão anunciada</h1><p>Confira em breve.</p>"
            "<div aria-hidden='true'>" + PARAGRAPH * 8 + "</div>"
            "<p style='display:none'>" + PARAGRAPH * 8 + "</p></article>"
        )
        self.responses({url: Response(url, html)})
        self.assert_rejected([candidate(url)])

    def test_footer_text_cannot_inflate_a_small_visible_note(self):
        url = "https://portal-a.example/politica/nota-incompleta"
        html = (
            "<main><article><h1>Uma decisão anunciada</h1><p>Confira em breve.</p></article>"
            "<footer>" + PARAGRAPH * 8 + "</footer></main>"
        )
        self.responses({url: Response(url, html)})
        self.assert_rejected([candidate(url)])

    def test_a_real_report_may_quote_an_access_denied_error(self):
        url = "https://portal-a.example/tecnologia/indisponibilidade"
        html = (
            "<article><h1>Portal esclarece uma indisponibilidade temporária</h1><p>"
            + PARAGRAPH
            + " O relatório técnico citou a mensagem Access denied e explicou a correção."
            + "</p></article>"
        )
        self.responses({url: Response(url, html)})
        self.assertEqual(len(self.collect([candidate(url)])), 1)

    def test_credentials_in_publisher_url_are_rejected_before_fetch(self):
        self.assert_rejected([
            candidate("https://fixture-user:fixture-pass@portal-a.example/politica/nota")
        ])
        REQUESTS.get.assert_not_called()

    def test_non_https_candidate_is_never_fetched(self):
        self.assert_rejected([candidate("http://portal-a.example/politica/nota")])
        REQUESTS.get.assert_not_called()

    def test_undecoded_google_wrapper_cannot_be_used_as_source(self):
        google = "https://news.google.com/rss/articles/opaque"
        DECODER.decode_many.return_value = {google: google}
        self.assert_rejected([candidate(google)])
        REQUESTS.get.assert_not_called()

    def test_decode_only_google_links_and_fetch_the_real_publisher(self):
        google = "https://news.google.com/rss/articles/opaque"
        direct = "https://portal-a.example/politica/nota"
        decoded = "https://portal-b.example/politica/nota"
        DECODER.decode_many.return_value = {google: decoded}
        self.responses({direct: Response(direct), decoded: Response(decoded)})
        docs = self.collect([candidate(direct), candidate(google)])
        self.assertEqual({d["url"] for d in docs}, {direct, decoded})
        self.assertEqual(DECODER.decode_many.call_args.args[0], [google])
        self.assertEqual({c.args[0] for c in REQUESTS.get.call_args_list}, {direct, decoded})

    def test_google_decoder_failure_preserves_an_accessible_direct_article(self):
        google = "https://news.google.com/rss/articles/opaque"
        direct = "https://portal-a.example/politica/nota"
        DECODER.decode_many.side_effect = TimeoutError("decoder fixture timeout")
        self.responses({direct: Response(direct)})
        docs = self.collect([candidate(google), candidate(direct)])
        self.assertEqual([d["url"] for d in docs], [direct])
        self.assertEqual([c.args[0] for c in REQUESTS.get.call_args_list], [direct])

    def test_duplicate_rss_links_do_not_consume_the_link_budget(self):
        duplicate = "https://portal-a.example/politica/inacessivel"
        real = "https://portal-b.example/politica/nota"
        self.responses({
            duplicate: RequestException("fixture unavailable"),
            real: Response(real),
        })
        items = [candidate(duplicate)] * 54 + [candidate(real)]
        docs = self.collect(items, max_links=54)
        self.assertEqual([d["url"] for d in docs], [real])
        self.assertEqual([c.args[0] for c in REQUESTS.get.call_args_list].count(duplicate), 1)

    def test_decoded_http_url_is_rejected_before_fetch(self):
        google = "https://news.google.com/rss/articles/opaque"
        DECODER.decode_many.return_value = {google: "http://portal-a.example/politica/nota"}
        self.assert_rejected([candidate(google)])
        REQUESTS.get.assert_not_called()

    def test_redirect_to_google_does_not_become_publisher_evidence(self):
        url = "https://portal-a.example/politica/redirect"
        self.responses({url: Response("https://news.google.com/articles/x", LONG_HTML)})
        self.assert_rejected([candidate(url)])

    def test_redirect_to_http_is_rejected(self):
        url = "https://portal-a.example/politica/redirect"
        self.responses({url: Response("http://portal-a.example/politica/nota", LONG_HTML)})
        self.assert_rejected([candidate(url)])

    def test_duplicate_broken_url_is_attempted_only_once(self):
        failed = "https://portal-a.example/politica/quebrada"
        valid = "https://portal-b.example/politica/nota"
        self.responses({failed: RequestException("temporary fixture error"), valid: Response(valid)})
        docs = self.collect([candidate(failed), candidate(failed), candidate(valid)])
        self.assertEqual(len(docs), 1)
        self.assertEqual([c.args[0] for c in REQUESTS.get.call_args_list].count(failed), 1)

    def test_google_and_direct_duplicate_fetch_only_one_article(self):
        google = "https://news.google.com/rss/articles/opaque"
        real = "https://portal-a.example/politica/nota"
        DECODER.decode_many.return_value = {google: real}
        self.responses({real: Response(real)})
        docs = self.collect([candidate(google), candidate(real)])
        self.assertEqual(len(docs), 1)
        self.assertEqual(REQUESTS.get.call_count, 1)

    def test_redirect_aliases_do_not_duplicate_the_same_final_article(self):
        alias_a = "https://alias-a.example/noticia"
        alias_b = "https://alias-b.example/noticia"
        final = "https://portal-a.example/politica/nota"
        self.responses({alias_a: Response(final), alias_b: Response(final)})
        docs = self.collect([candidate(alias_a), candidate(alias_b)])
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["url"], final)

    def test_publisher_cap_applies_to_final_host_after_redirect(self):
        candidates = []
        responses = {}
        final_host = "portal-a.example"
        for i in range(5):
            alias = f"https://alias-{i}.example/noticia"
            final = f"https://{final_host}/politica/nota-{i}"
            candidates.append(candidate(alias))
            responses[alias] = Response(final)
        self.responses(responses)
        docs = self.collect(candidates)
        self.assertEqual(len(docs), 3)
        self.assertEqual({d["publisher_host"] for d in docs}, {final_host})

    def test_multiple_articles_from_one_host_do_not_invent_a_second_publisher(self):
        urls = [f"https://www.portal-a.example/politica/nota-{i}" for i in range(2)]
        self.responses({url: Response(url) for url in urls})
        docs = self.collect([candidate(url) for url in urls])
        self.assertEqual(len(docs), 2)
        self.assertEqual({d["publisher_host"] for d in docs}, {"portal-a.example"})

    def test_distinct_final_domains_are_preserved_without_claiming_independence(self):
        urls = [
            "https://portal-a.example/politica/nota",
            "https://portal-b.example/politica/nota",
        ]
        self.responses({url: Response(url) for url in urls})
        docs = self.collect([candidate(url) for url in urls])
        self.assertEqual({d["publisher_host"] for d in docs}, {"portal-a.example", "portal-b.example"})
        self.assertTrue(all("actual_article_text" in d for d in docs))
        self.assertFalse(any("independent" in d for d in docs))

    def test_total_document_cap_remains_eighteen(self):
        urls = [f"https://portal-{i}.example/politica/nota" for i in range(25)]
        self.responses({url: Response(url) for url in urls})
        docs = self.collect([candidate(url) for url in urls])
        self.assertEqual(len(docs), 18)
        self.assertEqual(REQUESTS.get.call_count, 18)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]] + UNITTEST_ARGS)
