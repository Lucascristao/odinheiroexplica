import argparse
import json
import re
from pathlib import Path

from tts_config import GLOBAL_PRONUNCIATIONS


# Termos estrangeiros/financeiros que costumam variar bastante entre vozes pt-BR.
# Eles não recebem pronúncia inventada aqui: o roteiro precisa declarar um alias,
# ou a correção precisa entrar no léxico global depois de validada pelo ouvido.
WATCH_TERMS = {
    "bet", "bets", "fintech", "fintechs", "spread", "spreads",
    "holding", "holdings", "cashback", "startup", "startups",
    "marketplace", "homebroker", "trader", "trading", "blockchain",
    "bitcoin", "ethereum", "short", "long", "stake", "staking",
    "token", "tokens", "yield", "default", "rating", "guidance",
}

SAFE_ACRONYMS = {
    "MP", "CPF", "CNPJ", "PIB", "IPCA", "CDI", "IOF", "BC",
    "BCB", "BACEN", "CVM", "FGTS", "INSS", "MEI", "STF", "STJ",
    "TR", "IGP", "IGPM", "IPTU", "IPVA", "IR", "IRPF", "IRPJ",
}

TOKEN_RE = re.compile(r"\b[0-9A-Za-zÀ-ÖØ-öø-ÿ][0-9A-Za-zÀ-ÖØ-öø-ÿ._+-]*\b")


def collect_narration(payload: dict) -> str:
    scenes = payload.get("scenes") or payload.get("script", {}).get("scenes", [])
    return "\n".join(str(scene.get("narration", "")) for scene in scenes)


def normalized_map(value: dict | None) -> dict[str, str]:
    return {
        str(key).lower(): str(alias)
        for key, alias in (value or {}).items()
        if str(key).strip() and str(alias).strip()
    }


def risky_reason(token: str) -> str | None:
    lower = token.lower()

    if lower in WATCH_TERMS:
        return "termo estrangeiro/financeiro com pronúncia variável"

    if any(ch in token for ch in "wWyYkK"):
        return "grafia incomum em português brasileiro"

    if token.isupper() and 2 <= len(token) <= 7 and token not in SAFE_ACRONYMS:
        return "sigla que pode ser lida como palavra ou letra por letra"

    # CamelCase e marcas misturando maiúsculas/minúsculas costumam enganar TTS.
    if re.search(r"[a-zá-ÿ][A-Z]", token):
        return "nome/marca com caixa mista"

    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    text = collect_narration(payload)

    project_speech = payload.get("speech") or {}
    project_pronunciations = normalized_map(project_speech.get("pronunciations"))
    ignored = {
        str(term).lower()
        for term in (project_speech.get("ignore_pronunciation_terms") or [])
    }

    effective = dict(GLOBAL_PRONUNCIATIONS)
    effective.update(project_pronunciations)

    seen: dict[str, str] = {}
    for match in TOKEN_RE.finditer(text):
        token = match.group(0)
        key = token.lower()
        if key not in seen:
            seen[key] = token

    resolved = []
    unresolved = []

    for key, original in sorted(seen.items()):
        reason = risky_reason(original)
        if not reason:
            continue

        if key in effective:
            resolved.append({
                "term": original,
                "spoken_as": effective[key],
                "reason": reason,
                "source": "project" if key in project_pronunciations else "global",
            })
        elif key not in ignored:
            unresolved.append({
                "term": original,
                "reason": reason,
            })

    report = {
        "status": "ok" if not unresolved else "review",
        "resolved": resolved,
        "unresolved": unresolved,
        "global_lexicon_size": len(GLOBAL_PRONUNCIATIONS),
        "project_lexicon_size": len(project_pronunciations),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if resolved:
        print("[Pronúncia] Correções aplicadas antes do TTS:")
        for item in resolved:
            print(f"  - {item['term']} -> {item['spoken_as']} ({item['source']})")

    if unresolved:
        print("[Pronúncia] Termos que precisam de revisão antes do TTS:")
        for item in unresolved:
            print(f"  - {item['term']}: {item['reason']}")

        if args.strict:
            raise RuntimeError(
                "Auditoria de pronúncia encontrou termos de risco sem alias. "
                "Adicione speech.pronunciations no projeto ou, se a leitura padrão "
                "já tiver sido validada, use speech.ignore_pronunciation_terms."
            )
    else:
        print("[Pronúncia] Auditoria concluída sem termos pendentes.")


if __name__ == "__main__":
    main()
