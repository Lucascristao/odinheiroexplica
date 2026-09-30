import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


NON_OFFICIAL_CLASSES = {
    "independent_journalism",
    "technical",
    "industry",
    "academic",
    "fact_check",
    "company",
    "other",
}

CONTEXT_CLASSES = {
    "independent_journalism",
    "technical",
    "industry",
    "academic",
    "fact_check",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    project = json.loads(Path(args.input).read_text(encoding="utf-8"))
    editorial = project.get("editorial") or {}
    balance = editorial.get("source_balance") or {}
    sources = project.get("sources") or []
    claims = project.get("claims") or []

    issues: list[str] = []
    warnings: list[str] = []
    right_review = balance.get("right_editorial_review") or {}
    consulted = right_review.get("consulted") or []
    if not isinstance(consulted, list) or not consulted:
        issues.append(
            "Registre ao menos um veículo de linha editorial à direita consultado "
            "em editorial.source_balance.right_editorial_review.consulted."
        )
        consulted = []
    for index, item in enumerate(consulted):
        if not isinstance(item, dict):
            issues.append(f"Consulta editorial {index + 1}: registro inválido.")
            continue
        publisher = str(item.get("publisher") or "").strip()
        url = str(item.get("url") or "").strip()
        summary = str(item.get("summary") or "").strip()
        parsed = urlparse(url)
        if not publisher or parsed.scheme != "https" or not parsed.netloc or not summary:
            issues.append(
                f"Consulta editorial {index + 1}: informe publisher, URL HTTPS "
                "da matéria consultada e resumo do que foi verificado."
            )

    source_by_id = {
        str(source.get("id")): source
        for source in sources
        if str(source.get("id") or "").strip()
    }

    counts: dict[str, int] = {}
    publishers: set[str] = set()
    for source in sources:
        publisher_class = str(source.get("publisher_class") or "other")
        counts[publisher_class] = counts.get(publisher_class, 0) + 1
        publisher = str(source.get("publisher") or "").strip().lower()
        if publisher:
            publishers.add(publisher)

    if balance.get("requires_diversity"):
        official_count = counts.get("official", 0)
        non_official = [
            source
            for source in sources
            if str(source.get("publisher_class") or "other") in NON_OFFICIAL_CLASSES
        ]
        context_sources = [
            source
            for source in sources
            if str(source.get("publisher_class") or "other") in CONTEXT_CLASSES
        ]
        non_official_publishers = {
            str(source.get("publisher") or "").strip().lower()
            for source in non_official
            if str(source.get("publisher") or "").strip()
        }

        if len(sources) < 4:
            issues.append(
                "Pauta com diversidade obrigatória precisa de pelo menos 4 fontes."
            )
        if len(non_official) < 2:
            issues.append(
                "Pauta com diversidade obrigatória precisa de pelo menos 2 fontes não oficiais."
            )
        if len(non_official_publishers) < 2:
            issues.append(
                "As fontes não oficiais precisam vir de pelo menos 2 publicadores diferentes."
            )
        if not context_sources:
            issues.append(
                "Inclua jornalismo independente, análise técnica, setor, academia ou checagem."
            )
        if balance.get("public_policy_or_regulation") and official_count < 1:
            issues.append(
                "Pauta regulatória precisa de pelo menos uma fonte oficial para o texto da regra."
            )
        if balance.get("public_policy_or_regulation") and not balance.get(
            "official_claims_attributed"
        ):
            issues.append(
                "Afirmações de governo/regulador precisam ser marcadas como atribuídas."
            )
        if not str(balance.get("counterpoint_summary") or "").strip():
            issues.append(
                "Pauta com diversidade obrigatória precisa registrar contraponto ou limitação."
            )

    for claim in claims:
        framing = str(claim.get("framing") or "verified_fact")
        claim_id = str(claim.get("id") or "?")
        source_ids = [str(value) for value in claim.get("source_ids") or []]
        claim_sources = [
            source_by_id[source_id]
            for source_id in source_ids
            if source_id in source_by_id
        ]

        if framing == "official_position" and not claim.get(
            "attribution_required", False
        ):
            issues.append(
                f"{claim_id}: posição oficial precisa de attribution_required=true."
            )

        if framing in {"analysis", "reported_claim"}:
            if claim_sources and all(
                str(source.get("publisher_class") or "other") == "official"
                for source in claim_sources
            ):
                issues.append(
                    f"{claim_id}: análise/alegação reportada não pode depender apenas de fonte oficial."
                )

        if framing == "verified_fact" and claim_sources and all(
            str(source.get("publisher_class") or "other") == "official"
            for source in claim_sources
        ):
            warnings.append(
                f"{claim_id}: fato sustentado apenas por fonte oficial; confirme se é dado normativo/operacional."
            )

    payload = {
        "requires_diversity": bool(balance.get("requires_diversity")),
        "public_policy_or_regulation": bool(
            balance.get("public_policy_or_regulation")
        ),
        "source_count": len(sources),
        "publisher_count": len(publishers),
        "publisher_class_counts": counts,
        "right_editorial_consulted_count": len(consulted),
        "issues": issues,
        "warnings": warnings,
        "passed": not issues,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    for warning in warnings:
        print(f"AVISO: {warning}")

    if issues:
        for issue in issues:
            print(f"ERRO: {issue}")
        if args.strict:
            raise RuntimeError(
                f"Auditoria editorial encontrou {len(issues)} problema(s)."
            )

    print(
        "Auditoria editorial: "
        f"{len(sources)} fontes, {len(publishers)} publicadores, "
        f"{len(issues)} erro(s), {len(warnings)} aviso(s)."
    )


if __name__ == "__main__":
    main()
