"""Offline draft schema checks using an existing historical episode as a fixture."""
import argparse
import copy
from datetime import date
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "worker"))
COMPLETE = Mock()
ARGS = argparse.ArgumentParser(add_help=False)
ARGS.add_argument("--module", default=str(Path(__file__).with_name("news_autonomous_editor.py")))
OPTIONS, TEST_ARGS = ARGS.parse_known_args()


def dependency(name, **values):
    module = types.ModuleType(name)
    module.__dict__.update(values)
    return module


requests = dependency("requests", RequestException=type("RequestException", (Exception,), {}))
# Other offline modules may leave dependency stubs in sys.modules. Load the
# actual canonical validators explicitly so this suite tests the real gates.
PACKAGE_SPEC = importlib.util.spec_from_file_location(
    "schema_canonical_package", ROOT / "worker/build_youtube_package.py"
)
PACKAGE = importlib.util.module_from_spec(PACKAGE_SPEC)
PACKAGE_SPEC.loader.exec_module(PACKAGE)
CANONICAL_SPEC = importlib.util.spec_from_file_location(
    "schema_canonical_project", ROOT / "worker/news_single_project.py"
)
CANONICAL = importlib.util.module_from_spec(CANONICAL_SPEC)
with patch.dict(sys.modules, {"build_youtube_package": PACKAGE}):
    CANONICAL_SPEC.loader.exec_module(CANONICAL)
SPEC = importlib.util.spec_from_file_location(
    "draft_schema_review", OPTIONS.module
)
EDITOR = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {
    "requests": requests,
    "news_scout": dependency("news_scout", collect=Mock()),
    "news_source_corpus": dependency("news_source_corpus", collect_verified=Mock(), extract_article=Mock()),
    "news_groq_client": dependency("news_groq_client", complete=COMPLETE),
    "news_single_project": CANONICAL,
    "build_youtube_package": PACKAGE,
}):
    SPEC.loader.exec_module(EDITOR)

FIXTURE = json.loads(
    (ROOT / "news/episodes/2026-10-12-meio-dia.json").read_text(encoding="utf-8")
)


class DraftSchema(unittest.TestCase):
    def setUp(self):
        COMPLETE.reset_mock(return_value=True, side_effect=True)
        self.episode = copy.deepcopy(FIXTURE)

    def draft(self, value):
        COMPLETE.return_value = json.dumps(value, ensure_ascii=False)
        return EDITOR.draft("Relatório histórico de teste; não é nova apuração.", "2026-10-12",
                            "meio-dia", [], "")

    def test_prompt_states_exact_nested_keys_objects_and_title_copy(self):
        self.assertEqual(self.draft(self.episode), self.episode)
        prompt = COMPLETE.call_args.args[0]
        for literal in (
            "A raiz é UM OBJETO JSON",
            "news_selection.why_today",
            "Não colocar why_today na raiz",
            "Não usar why_now",
            "scorecard é UM OBJETO",
            "criteria (OBJETO/mapa)",
            "COPIE EXATAMENTE",
            "editorial_quality máxima",
            "Listas de OBJETOS",
        ):
            self.assertIn(literal, prompt)
        self.assertIs(COMPLETE.call_args.kwargs["json_mode"], True)

    def test_root_array_has_a_clear_error_before_any_string_indexing(self):
        with self.assertRaisesRegex(ValueError, "objeto JSON"):
            self.draft([self.episode])

    def test_prompt_leaves_technical_metadata_to_code_and_narrative_length_flexible(self):
        self.draft(self.episode)
        prompt = COMPLETE.call_args.args[0]
        for text in ("O código preenche", "Crédito curto real é válido",
                     "rights_review é opcional", "não invente licença",
                     "de 4 a 9 cenas", "extensão necessária", "cópia EXATA, CONTÍNUA e LITERAL"):
            self.assertIn(text, prompt)
        self.assertNotIn("EXATAMENTE QUATRO", prompt)
        self.assertNotIn("85-125", prompt)

    def test_user_unicode_and_explicit_opinion_fixes_are_preserved(self):
        self.episode["thumbnail_primary"] = "objeto\u00a0com\u200b contexto"
        opinion = next(segment for segment in self.episode["segments"] if segment["type"] == "opinion")
        opinion["narration"] = "Uma interpretação claramente apresentada como avaliação."
        result = self.draft(self.episode)
        self.assertEqual(result["thumbnail_primary"], "objeto com contexto")
        self.assertTrue(next(segment for segment in result["segments"] if segment["type"] == "opinion")
                        ["narration"].startswith("Na minha análise, "))

    def test_scorecard_list_is_rejected(self):
        self.episode["scorecard"] = [self.episode["scorecard"]]
        with self.assertRaisesRegex(ValueError, r"draft.scorecard"):
            self.draft(self.episode)

    def test_news_selection_list_is_rejected(self):
        self.episode["news_selection"] = [self.episode["news_selection"]]
        with self.assertRaisesRegex(ValueError, r"draft.news_selection"):
            self.draft(self.episode)

    def test_source_array_of_pairs_is_rejected(self):
        self.episode["sources"][0] = list(self.episode["sources"][0].items())
        with self.assertRaisesRegex(ValueError, r"draft.sources"):
            self.draft(self.episode)

    def test_why_now_is_not_silently_renamed(self):
        selection = self.episode["news_selection"]
        selection["why_now"] = selection.pop("why_today")
        original = copy.deepcopy(self.episode)
        with self.assertRaisesRegex(ValueError, r"news_selection.why_today"):
            EDITOR.validate_draft_shape(self.episode)
        self.assertEqual(self.episode, original)

    def test_root_why_today_does_not_replace_nested_why_today(self):
        self.episode["why_today"] = self.episode["news_selection"].pop("why_today")
        with self.assertRaisesRegex(ValueError, r"news_selection.why_today"):
            self.draft(self.episode)

    def test_short_why_today_is_rejected_without_a_generated_justification(self):
        self.episode["news_selection"]["why_today"] = "É de hoje."
        with self.assertRaisesRegex(ValueError, r"news_selection.why_today"):
            self.draft(self.episode)

    def test_title_outside_options_is_rejected(self):
        self.episode["title"] += " agora"
        with self.assertRaisesRegex(ValueError, "copiar exatamente"):
            self.draft(self.episode)

    def test_title_cannot_select_a_lower_scored_option(self):
        options = self.episode["title_options"]
        self.episode["title"] = options[1]["text"]
        options[1]["editorial_quality"] = 1
        options[0]["editorial_quality"] = 5
        with self.assertRaisesRegex(ValueError, "editorial_quality máxima"):
            self.draft(self.episode)

    def test_boolean_is_not_an_integer_rating(self):
        self.episode["title_options"][0]["editorial_quality"] = True
        with self.assertRaisesRegex(ValueError, "inteiro de 1 a 5"):
            self.draft(self.episode)

    def test_criteria_format_is_a_prompt_preference_not_a_new_gate(self):
        self.episode["scorecard"]["criteria"] = []
        self.assertIs(EDITOR.validate_draft_shape(self.episode), self.episode)
        self.assertIs(EDITOR.validate(self.episode, today=date(2026, 10, 13)), self.episode)

    def test_valid_shape_does_not_change_the_historical_episode(self):
        original = copy.deepcopy(self.episode)
        self.assertIs(EDITOR.validate_draft_shape(self.episode), self.episode)
        self.assertEqual(self.episode, original)
        self.assertIs(EDITOR.validate(self.episode, today=date(2026, 10, 13)), self.episode)


class LiteralMetadataBinding(unittest.TestCase):
    def test_paraphrased_payoff_binds_existing_literal_without_changing_facts(self):
        anchor = "O governo apresentou hoje a proposta."
        value = {"segments": [{"narration": anchor + " A decisão ainda depende do Congresso."}],
                 "news_selection": {"opening_anchor": anchor},
                 "discovery_strategy": {"first_payoff": "A proposta foi apresentada pelo governo hoje."},
                 "verified_facts": [{"claim": "Uma proposta foi apresentada.", "source_ids": ["S1"]}],
                 "sources": [{"id": "S1", "url": "https://example.com/proposta"}]}
        original = copy.deepcopy(value)
        EDITOR.bind_draft_metadata(value)
        self.assertEqual(value["discovery_strategy"]["first_payoff"], anchor)
        for key in ("segments", "news_selection", "verified_facts", "sources"):
            self.assertEqual(value[key], original[key])

    def test_existing_literal_is_preserved(self):
        payoff = "A decisão ainda depende do Congresso."
        value = {"segments": [{"narration": "A proposta chegou hoje. " + payoff}],
                 "news_selection": {"opening_anchor": "A proposta chegou hoje."},
                 "discovery_strategy": {"first_payoff": payoff}}
        EDITOR.bind_draft_metadata(value)
        self.assertEqual(value["discovery_strategy"]["first_payoff"], payoff)

    def test_missing_ambiguous_or_absent_opening_is_not_fabricated(self):
        anchor = "O governo apresentou hoje a proposta."
        for opening in ("Outra narrativa sem esse trecho.", anchor + " " + anchor):
            value = {"segments": [{"narration": opening}],
                     "news_selection": {"opening_anchor": anchor},
                     "discovery_strategy": {"first_payoff": "Paráfrase sem correspondência literal."}}
            before = copy.deepcopy(value)
            EDITOR.bind_draft_metadata(value)
            self.assertEqual(value, before)


class DerivedOpeningAndAttribution(unittest.TestCase):
    def fixture(self):
        claim = "O governo anunciou hoje uma proposta de perdão para MEIs."
        return {"segments": [{"type": "fact", "narration": claim + " A aplicação depende da análise do Congresso."}],
                "news_selection": {"new_fact": claim, "opening_anchor": "Uma paráfrase que não aparece na fala.",
                                   "source_mode": "single_source_attributed", "independent_confirmation": False},
                "verified_facts": [{"claim": claim, "source_ids": ["S1"], "status": "statement"}],
                "sources": [{"id": "S1", "publisher": "Publicador da Fixture", "url": "https://example.com/proposta"}],
                "discovery_strategy": {"first_payoff": "O relato apresenta uma proposta anunciada pelo governo."},
                "publication_description": "A proposta e seus limites são explicados nesta notícia."}

    def test_metadata_uses_real_fact_sentence_and_existing_source_without_changing_proof(self):
        value = self.fixture()
        original = copy.deepcopy(value)
        EDITOR.bind_draft_metadata(value)
        self.assertEqual(value["news_selection"]["opening_anchor"], original["verified_facts"][0]["claim"])
        self.assertEqual(value["discovery_strategy"]["first_payoff"], value["news_selection"]["opening_anchor"])
        self.assertIn("Apuração atribuída a Publicador da Fixture.", value["publication_description"])
        for key in ("segments", "verified_facts", "sources"):
            self.assertEqual(value[key], original[key])

    def test_unknown_or_ambiguous_new_fact_is_not_filled(self):
        for duplicate in (False, True):
            value = self.fixture()
            if duplicate:
                value["verified_facts"].append(copy.deepcopy(value["verified_facts"][0]))
            else:
                value["news_selection"]["new_fact"] = "Outra alegação que não consta dos fatos fornecidos."
            original = copy.deepcopy(value)
            EDITOR.bind_draft_metadata(value)
            self.assertEqual(value, original)

    def test_intro_question_is_not_used_as_a_new_fact(self):
        value = self.fixture()
        value["segments"][0]["narration"] = "Você quer entender essa proposta? Eu sou Roberto. " + value["verified_facts"][0]["claim"]
        EDITOR.bind_draft_metadata(value)
        self.assertEqual(value["news_selection"]["opening_anchor"], value["verified_facts"][0]["claim"])


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]] + TEST_ARGS)
