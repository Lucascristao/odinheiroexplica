"""Literal Live output checks with explicit spoken equivalents, no provider calls."""
from difflib import SequenceMatcher
from decimal import Decimal
import re

from align_narration import tokens

VERSION = "live-literal-token-fidelity-v1"
MONTHS = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")


def canonical_tokens(text, pronunciations=None):
    """Keep all lexical tokens; normalize only punctuation and numeric spelling."""
    text = str(text)
    if re.search(r"\d", text):
        try:
            from num2words import num2words
            if not callable(num2words):
                raise ImportError("missing numeric normalizer")
        except ImportError as exc:
            raise ValueError("num2words indisponível; não validar nem gerar fala numérica sem o normalizador.") from exc
    # Transcribers can render a spoken calendar date numerically.
    def date(match):
        day, month, year = map(int, match.groups())
        if 1 <= day <= 31 and 1 <= month <= 12:
            return f"{day} de {MONTHS[month-1]} de {year}"
        return match.group()
    text = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", date, text)
    def currency(match):
        number = match.group(1)
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", number):
            number = number.replace(".", "")
        return num2words(Decimal(number.replace(",", ".")), lang="pt_BR", to="currency")
    text = re.sub(r"R\$\s*(\d+(?:[.,]\d+)*)", currency, text, flags=re.I)
    text = re.sub(r"\b(\d+(?:[.,]\d+)*)\s+reais\b", currency, text, flags=re.I)
    def ordinal(match):
        spoken = num2words(int(match.group(1)), lang="pt_BR", to="ordinal")
        return " ".join(w[:-1]+"a" if w.endswith("o") else w for w in spoken.split()) if match.group(2) == "ª" else spoken
    text = re.sub(r"\b(\d+)([ºª])", ordinal, text)
    text = re.sub(r"(\d+(?:[.,]\d+)*)\s*%", r"\1 por cento", text)
    text = re.sub(r"(?<![\w])[-−](?=\d)", "menos ", text)
    return tokens(text, pronunciations)


def evaluate_transcription(reference, transcript, pronunciations=None, minimum=.985):
    expected = canonical_tokens(reference, pronunciations)
    actual = canonical_tokens(transcript, pronunciations)
    similarity = round(SequenceMatcher(None, " ".join(expected), " ".join(actual), autojunk=False).ratio(), 6) if expected and actual else 0.0
    differences = []
    for tag, a, b, c, d in SequenceMatcher(None, expected, actual, autojunk=False).get_opcodes():
        if tag != "equal":
            differences.append({"operation": tag, "reference_tokens": expected[a:b], "output_tokens": actual[c:d], "reference_start_token": a, "output_start_token": c})
    exact = bool(expected) and expected == actual
    return {"version": VERSION, "passed": exact and similarity >= minimum,
            "similarity": similarity, "canonical_token_match": exact,
            "reference_token_count": len(expected), "output_token_count": len(actual),
            "differences": differences, "rule": "all lexical tokens required; only explicit pronunciations, numeric spelling, accents and punctuation normalized"}
