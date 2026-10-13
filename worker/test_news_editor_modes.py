"""Offline checks for source-mode selection and authentic visible HTML evidence."""
from importlib.util import spec_from_file_location, module_from_spec
import json
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

DRAFT = Path(__file__).parent
ROOT = DRAFT.parent if DRAFT.name == "worker" else DRAFT.parents[1]
sys.path.insert(0, str(ROOT / "worker"))
sys.path.insert(0, str(DRAFT))
# No transport or key lookup is needed for these checks.
requests_stub = ModuleType("requests")
class RequestException(Exception):
    pass
class HTTPError(RequestException):
    pass
requests_stub.RequestException = RequestException
requests_stub.HTTPError = HTTPError
requests_stub.get = Mock(side_effect=AssertionError("Unexpected network call"))
sys.modules["requests"] = requests_stub
transport = ModuleType("news_groq_client")
transport.complete = Mock(side_effect=AssertionError("Unexpected model call"))
sys.modules["news_groq_client"] = transport
spec = spec_from_file_location("editor_draft", DRAFT / "news_autonomous_editor.py")
editor = module_from_spec(spec)
spec.loader.exec_module(editor)

Q1 = "A medida foi anunciada hoje com condições publicadas."
Q2 = "O efeito depende do cumprimento dos requisitos declarados."
FILL = " Contexto suficiente da reportagem, com autoria, evento e limites explícitos." * 4

def page(extra="", q1=Q1, q2=Q2):
    return '<html><head><title>Título verificado</title></head><body><nav>Menu do site</nav><article><h1>Notícia atual com contexto e autoria</h1><p>' + q1 + FILL + '</p><p>' + q2 + FILL + '</p>' + extra + '</article></body></html>'

def episode(mode="single_source_attributed", second_url=None):
    sources = [{"id": "S1", "url": "https://example.com/noticia-atual", "publisher": "Publicador Um"}]
    docs = [{"source_id": "S1", "source_page_url": sources[0]["url"], "expected_text": Q1},
            {"source_id": "S1", "source_page_url": sources[0]["url"], "expected_text": Q2}]
    if second_url:
        sources.append({"id": "S2", "url": second_url, "publisher": "Publicador Dois"})
        docs[1].update(source_id="S2", source_page_url=second_url)
    return {"sources": sources, "documentary_evidence": docs,
            "news_selection": {"source_mode": mode, "new_fact": "Relato atribuído da medida anunciada hoje."},
            "verified_facts": [{"claim": "Relato atribuído da medida anunciada hoje.", "status": "statement", "source_ids": ["S1"]}]}

class EditorSourceModeTests(unittest.TestCase):
    def run_check(self, ep, html=None, final_url=None, content_type="text/html", http_error=None):
        def response(url, **kwargs):
            result = Mock()
            result.url = final_url or url
            result.text = html or page()
            result.headers = {"Content-Type": content_type}
            result.raise_for_status.side_effect = http_error
            return result
        with patch.object(editor.requests, "get", side_effect=response) as get:
            editor.check_documentary_sources(ep)
        return get

    def test_one_article_two_distinct_excerpts_is_valid(self):
        self.assertEqual(self.run_check(episode()).call_count, 1)

    def test_duplicate_quotes_do_not_simulate_two_excerpts(self):
        ep = episode()
        ep["documentary_evidence"][1]["expected_text"] = "  " + Q1.upper() + "  "
        with self.assertRaisesRegex(ValueError, "two distinct"):
            self.run_check(ep)

    def test_two_independent_publisher_domains_are_valid(self):
        self.assertEqual(self.run_check(episode("corroborated", "https://example.org/noticia-atual")).call_count, 2)

    def test_two_pages_of_same_publisher_are_not_corroboration(self):
        with self.assertRaisesRegex(ValueError, "two publisher domains"):
            self.run_check(episode("corroborated", "https://example.com/outra-materia"))

    def test_context_source_cannot_replace_primary_article_two_quotes(self):
        with self.assertRaisesRegex(ValueError, "two distinct"):
            self.run_check(episode(second_url="https://example.org/contexto"))

    def test_single_source_claim_cannot_be_confirmed(self):
        ep = episode()
        ep["verified_facts"].append({"claim": "Relato secundário", "status": "confirmed", "source_ids": ["S1"]})
        with self.assertRaisesRegex(ValueError, "cannot promote"):
            self.run_check(ep)

    def test_single_source_central_claim_must_be_statement(self):
        ep = episode()
        ep["verified_facts"][0]["status"] = "projection"
        with self.assertRaisesRegex(ValueError, "attributed statement"):
            self.run_check(ep)

    def test_head_script_navigation_and_hidden_text_are_not_evidence(self):
        missing = "A frase oculta não constitui evidência."
        for extra in ("<script>" + missing + "</script>", "<nav>" + missing + "</nav>",
                      '<p hidden>' + missing + '</p>', '<p aria-hidden="true">' + missing + '</p>',
                      '<p style="display:none">' + missing + '</p>', '<header>' + missing + '</header>'):
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError, "visible article"):
                ep = episode()
                ep["documentary_evidence"][1]["expected_text"] = missing
                self.run_check(ep, html=page(extra))
        with self.assertRaisesRegex(ValueError, "visible article"):
            ep = episode()
            ep["documentary_evidence"][1]["expected_text"] = missing
            self.run_check(ep, html=page().replace("<title>", "<title>" + missing))

    def test_google_final_redirect_is_not_a_publisher(self):
        with self.assertRaisesRegex(ValueError, "aggregator"):
            self.run_check(episode(), final_url="https://news.google.com/articles/abc")

    def test_insecure_final_redirect_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            self.run_check(episode(), final_url="http://example.com/noticia-atual")

    def test_non_html_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "HTML"):
            self.run_check(episode(), content_type="application/json")

    def test_http_failure_is_not_turned_into_evidence(self):
        with self.assertRaises(editor.requests.HTTPError):
            self.run_check(episode(), http_error=editor.requests.HTTPError("Mock HTTP 403"))

    def test_unknown_mode_fails_before_network(self):
        with patch.object(editor.requests, "get") as get, self.assertRaisesRegex(ValueError, "Unknown"):
            editor.check_documentary_sources(episode("unknown"))
        get.assert_not_called()

    def test_credentials_in_source_url_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "credentials"):
            editor.publisher_host("https://fixture:fixture@example.com/noticia-atual")

    def test_research_allows_attributed_exclusive_report(self):
        corpus = [{"category": "politics", "headline": "Evento atual", "publisher_host": "example.com",
                   "url": "https://example.com/noticia-atual", "feed_published_utc": "2026-10-13T10:00:00Z",
                   "actual_article_text": Q1 + Q2 + FILL}]
        report = "SOURCE_MODE: single_source_attributed\n" + ("Relato atribuído com limitações. " * 20)
        with patch.object(editor, "collect_verified", return_value=corpus), patch.object(editor, "complete", return_value=report) as complete:
            self.assertEqual(editor.research([], [], "2026-10-13T12:00:00-03:00"), report)
        prompt = complete.call_args.args[0]
        self.assertIn("PREFIRA", prompt)
        self.assertIn("independent_confirmation=false", prompt)
        self.assertIn("Não descarte automaticamente", prompt)
        self.assertNotIn("Se nenhuma pauta tiver duas provas independentes", prompt)

    def test_insufficient_evidence_still_stops_research(self):
        with patch.object(editor, "collect_verified", return_value=[]), patch.object(editor, "complete", return_value="EDITORIAL_INSUFFICIENT_EVIDENCE"):
            with self.assertRaisesRegex(RuntimeError, "relato verificável"):
                editor.research([], [], "2026-10-13T12:00:00-03:00")

    def test_draft_requests_truthful_single_source_contract(self):
        with patch.object(editor, "complete", return_value=json.dumps({"fixture": True})) as complete:
            self.assertEqual(editor.draft("Relatório de fixture", "2026-10-13", "meio-dia", [], ""), {"fixture": True})
        prompt = complete.call_args.args[0]
        for expected in ('source_mode=', 'independent_confirmation=false', 'attribution_note',
                         'Não use status confirmed', 'MESMA página HTML', 'ocorrido nesse dia'):
            self.assertIn(expected, prompt)

if __name__ == "__main__":
    unittest.main()
