"""Persist non-blocking production observations for the following news edition.

This is editorial feedback only. It does not certify that a video is correct,
silence a QA failure, change raw voice audio or modify production gates.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path


FOLLOW_UP = {
    "asr-low-coverage": "Na próxima pauta, revisar números, siglas e construções longas da narração; confirmar cobertura ASR sem presumir erro na voz.",
    "estimated-visual-anchors": "Na próxima pauta, escolher âncoras visuais curtas, únicas e próximas à prova documental; conferir posições reais no áudio.",
    "master-level-variation": "Examinar variação de energia entre cenas; preservar política de áudio raw e não normalizar automaticamente.",
    "estimated-register-variation": "Acompanhar prosódia e intenção de cenas similares; não refazer fala com base apenas em estimativa.",
    "delivery-variation": "Variar a estrutura natural das frases e a intenção das cenas, sem forçar velocidade sintética.",
    "long-boundary-pause": "Reduzir pausas editoriais desnecessárias entre blocos na próxima estrutura narrativa.",
    "mp4-positive-true-peak": "Registrar pico entre amostras e inspecionar áudio codificado; manter métricas e gates de falha técnica separados.",
}


def summarize(qa: dict, episode: dict) -> dict:
    warnings = qa.get("warnings") or []
    failures = qa.get("failures") or []
    counts = Counter(str(item.get("code", "unknown")) for item in warnings)
    return {
        "version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "episode_id": episode.get("episode_id"),
        "qa_status": qa.get("status"),
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "warning_counts_by_code": dict(sorted(counts.items())),
        "warnings": warnings,
        "failures": failures,
        "next_cycle_actions": [
            {"code": code, "occurrences": count,
             "suggestion": FOLLOW_UP.get(code, "Investigar este aviso no vídeo anterior antes de criar correção; não presumir causa nem mudar gates.")}
            for code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "learning_status": "pending_next_edition_review" if warnings else "no_warning_follow_up",
        "note": "Avisos preservados para comparação no próximo ciclo; não afirmam qualidade subjetiva nem justificam ignorar falhas.",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--qa", required=True)
    p.add_argument("--episode", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    qa = json.loads(Path(args.qa).read_text(encoding="utf-8"))
    episode = json.loads(Path(args.episode).read_text(encoding="utf-8"))
    report = summarize(qa, episode)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ODE_QA_FEEDBACK:", report["episode_id"], report["qa_status"],
          report["warning_counts_by_code"], report["learning_status"])


if __name__ == "__main__":
    main()
