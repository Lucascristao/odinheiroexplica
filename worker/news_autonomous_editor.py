"""Autonomous newsroom: current research, truthful source checks, and episode JSON."""
import argparse
from datetime import datetime
from html import unescape
import json
import os
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import requests
from news_scout import collect
from news_source_corpus import collect_verified
from news_groq_client import complete
from news_single_project import validate, transform
from build_youtube_package import validate_publication_fields

SLOTS = {"manha": "08:00", "meio-dia": "12:00", "noite": "20:00"}


def plain(text):
    return " ".join(unicodedata.normalize(
        "NFKC", unescape(re.sub(r"<[^>]*>", " ", text))
    ).casefold().split())


def check_documentary_sources(episode):
    checked = {}
    for doc in episode["documentary_evidence"]:
        source = next(x for x in episode["sources"] if x["id"] == doc["source_id"])
        url = doc["source_page_url"]
        if url != source["url"]:
            raise ValueError("Documentary excerpt points to a different URL from its source.")
        if url not in checked:
            host = urlparse(url).hostname or ""
            if host.endswith("google.com") or host.endswith("news.google.com"):
                raise ValueError("Google News is a candidate aggregator, not the primary publisher.")
            response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            if "text/html" not in response.headers.get("Content-Type", ""):
                raise ValueError("News source did not return HTML.")
            checked[url] = plain(response.text[:2000000])
        if plain(doc["expected_text"]) not in checked[url]:
            raise ValueError("Quoted documentary text absent from the actual source: " + url)
    if len(checked) < 2:
        raise ValueError("At least two independent live source pages are required.")


def existing_history(root):
    history = []
    for file in sorted((root / "news/episodes").glob("*.json"), reverse=True)[:25]:
        try:
            e = json.loads(file.read_text(encoding="utf-8"))
            history.append({"episode_id": e.get("episode_id"), "title": e.get("title")})
        except (OSError, ValueError):
            continue
    return history


def prevent_repeated_story(episode, root):
    import string
    new_urls = {str(s.get("url", "")).strip().split("?")[0].lower()
                for s in episode.get("sources", [])}
    title_words = set(re.findall(r"[a-z0-9]{4,}", plain(episode.get("title", ""))))
    for old_path in (root / "news" / "episodes").glob("*.json"):
        old = json.loads(old_path.read_text(encoding="utf-8"))
        if old.get("episode_id") == episode.get("episode_id"):
            raise ValueError("Episódio dessa janela já existe.")
        old_urls = {str(s.get("url", "")).strip().split("?")[0].lower()
                    for s in old.get("sources", [])}
        if new_urls.intersection(old_urls):
            raise ValueError("Notícia usa matéria já coberta no canal: " + old_path.name)
        words = set(re.findall(r"[a-z0-9]{4,}", plain(old.get("title", ""))))
        if len(words & title_words) >= 5 and len(words & title_words) >= .70 * max(1, min(len(words),len(title_words))):
            raise ValueError("Provável tema repetido do título: " + old_path.name)


def research(candidates, history, target):
    """Select an actually verified new event from publisher pages, without model web tools."""
    corpus = collect_verified(candidates)
    # Keep below the Groq free-plan TPM limit. Literal excerpts + real URLs are
    # the only evidence the editor may use; full pages remain checked downstream.
    compact = [
        {**{k: entry[k] for k in ("category", "headline", "publisher_host", "url", "feed_published_utc")},
         "actual_article_text": entry["actual_article_text"][:1550]}
        for entry in corpus[:10]
    ]
    prompt = f"""Você é editor de apuração do canal O Dinheiro Explica.
Hoje em Fortaleza: {datetime.now(ZoneInfo('America/Fortaleza')).isoformat()}. Janela: {target}.
Compare pautas atuais, incluindo política e economia, usando SOMENTE os textos reais abaixo.
Descubra um FATO NOVO ocorrido hoje, com confirmação explícita em dois sites independentes.
Dia da publicação da reportagem NÃO equivale ao dia do fato; se não houver prova atual, declare.
Priorize páginas com texto literal para captura. NÃO invente links, datas ou trechos.
Verifique se duas páginas diferentes tratam realmente do mesmo acontecimento.
Identifique nome e URLs exatas, data original do fato, e ao menos quatro fatos com evidência.
Histórico (não repetir acontecimentos): {json.dumps(history[-12:], ensure_ascii=False)[:2000]}.
CORPUS de páginas HTTP realmente consultadas:
{json.dumps(compact, ensure_ascii=False)[:20000]}
Se nenhuma pauta tiver duas provas independentes do acontecimento de hoje, devolva
exatamente EDITORIAL_INSUFFICIENT_EVIDENCE, sem fabricar material.
Caso exista, escreva relatório factual de 500 a 750 palavras, incluindo URLs e pelo
menos dois trechos LITERAIS realmente presentes no corpus, preferindo trechos de 15 a 70 caracteres."""
    report = complete(prompt)
    if "EDITORIAL_INSUFFICIENT_EVIDENCE" in report or len(report) < 400:
        raise RuntimeError("Corpus não demonstra um acontecimento de hoje por dois publicadores.")
    return report


def draft(report, day, slot, history, error):
    target = SLOTS[slot]
    prompt = f"""Retorne SOMENTE um objeto JSON válido, em português do Brasil,
para um episódio jornalístico de notícia ÚNICA do canal O Dinheiro Explica.
Relatório preliminar baseado EXCLUSIVAMENTE em páginas HTML recuperadas e verificáveis:
{report}
Assuntos proibidos por repetição: {json.dumps(history, ensure_ascii=False)}.
Revisão de erro anterior: {error[:1200]}. Data: {day}, janela: {slot}.
Roberto, brasileiro, conversacional e crítico na economia, com opiniões
nitidamente separadas dos fatos. Não imitar fala nem slogan de ANCAPSU/Piter.
Objetivo é CTR legítimo e compreensão, nunca clickbait enganoso.

Esquema TOP-LEVEL obrigatório:
version, format, episode_id, news_date, event_date, editorial_status,
reviewed_at, news_selection, title, title_options, thumbnail_headline,
thumbnail_primary, thumbnail_tension, thumbnail_composition,
thumbnail_text_side, scorecard, sources, verified_facts,
documentary_evidence, context_photos, segments, engagement_question,
hashtags, tags, primary_keyword, secondary_keywords, pronunciations,
discovery_strategy, publication_description, publication_target_local.
version = "1.0"; format = "ode-news-single"; episode_id =
"noticia-{day}-{slot}", news_date = "{day}".
publication_target_local="{day}T{target}:00-03:00".
editorial_status="autonomous_fact_checked" e reviewed_at="" (serão
definidos pelo verificador depois). event_date YYYY-MM-DD deve ser
IGUAL à data {day}, com acontecimento ocorrido nesse dia; reportagem nova não renova fato antigo.

title: 20-100 caracteres, factual e magnético, assunto no começo.
title_options: lista de três objetos com text e editorial_quality (1-5).
thumbnail_headline: 8-34 caracteres e 2-5 palavras, distinta do título.
thumbnail_primary: protagonista visual específico da notícia.
thumbnail_tension: tensão editorial comprovável, sem mentira.
thumbnail_composition: enquadramento e posição do protagonista próprios.
thumbnail_text_side: "left" ou "right", lado oposto ao protagonista.
news_selection: objeto contendo topic_area (politics,economy,personal_finance,business,international); new_fact deve ser EXATAMENTE um claim de verified_facts com event_date={day}, status diferente de background e source_ids de pelo menos DOIS publicadores distintos, um publicado em {day}; why_today com motivo concreto de 30+ caracteres; opening_anchor com trecho literal de 20 a 160 caracteres presente uma vez na narração inicial; candidate_review com candidatas reais comparadas, incluindo política, datas reais do fato, URLs e justificativas. Não inventar candidatas.
scorecard: method, reason, criteria com julgamentos editoriais e não
CTR ou dados inventados.

sources: 2 ou 3 objetos, URLs REAIS HTTPS verificáveis do relatório e capturáveis sem HTTP 403,
cada item id (S1, S2...), publisher, url, published_at YYYY-MM-DD,
role; no mínimo dois publicadores/dominios diferentes, até 45 dias.
verified_facts: quatro ou mais itens {claim,source_ids,status,event_date}
com status SOMENTE "statement","background","forecast_not_collected",
"projection","confirmed"; source_ids devem existir.
documentary_evidence: exatamente dois ou três itens com id doc-1,doc-2
etc, kind="source_excerpt", source_id, source_page_url IGUAL à URL
original da fonte, expected_text sendo TRECHO VERBATIM copiado da matéria
real de >=8 caracteres, attribution, rights_review com explicação da
citação curta e capture_file "research/captures/doc-1.png" etc.
Não adicionar reconstrução editorial fictícia ou fotos da imprensa.
context_photos=[].

segments: EXATAMENTE QUATRO cenas, types nesta ordem fact,fact,opinion,outro. A primeira cena abre com o fato novo real e inclui news_selection.opening_anchor literalmente.
Cada objeto deve ter id,title,type,label,headline,metric,object_type
(data/store/cash/bank/package/truck/factory), visual_cards com 3-5
strings de 6-65 caracteres, narration de 85-125 PALAVRAS, document_id
doc-1/doc-2 alternando, media_side left/right.
Todas as cenas exibem documento real, incluindo o comentário opinativo.
Pelo menos 2 cenas factuais com prova. Uma opinião editorial fundamentada
sem fatos inventados. Final responde à pergunta inicial.
Não incluir photo_id ao usar document_id.
engagement_question termina em ponto de interrogação.
hashtags: de 1 a 3 hashtags específicas e distintas, começando com # e sem espaço.
tags: até 10 strings específicas. pronunciations: objeto vazio ou
pronúncias comprováveis, sem forçar fala.
publication_description: corpo editorial natural com palavra-chave no
início e sem URLs. primary_keyword: expressão literal presente no
title ou publication_description; secondary_keywords lista.

discovery_strategy: objeto com oito strings de ao menos 18 caracteres:
viewer_intent, search_query, recommendation_angle, first_payoff,
promise_proof, audience_hypothesis, thumbnail_complement,
verification_limits. first_payoff PRECISA SER UM TRECHO EXATO
e literalmente presente na narração da primeira cena.
Não reutilize fatos nem tema do vídeo-piloto de imposto seletivo.
Não invente datas nem alegações sem respaldo. Não incluir links, hashtags, FONTES ou CAPÍTULOS na publication_description; páginas devem permitir captura Playwright. Não confundir data da matéria com a data do acontecimento."""
    raw = complete(prompt, json_mode=True)
    return json.loads(raw)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slot", choices=SLOTS, required=True)
    p.add_argument("--root", default=".")
    args = p.parse_args()
    if not os.getenv("GROQ_API_KEY"):
        raise SystemExit("GROQ_API_KEY inexistente; configurar secret no GitHub.")
    local = datetime.now(ZoneInfo("America/Fortaleza"))
    date = local.date().isoformat()
    root = Path(args.root).resolve()
    output = root / "news" / "episodes" / f"{date}-{args.slot}.json"
    if output.exists():
        print("NEWS_SLOT_ALREADY_EXISTS:", output)
        return
    candidates = collect()
    if not candidates.get("candidates"):
        raise SystemExit("Nenhuma pauta RSS atual, não inventar notícias.")
    history = existing_history(root)
    report = research(candidates["candidates"], history,
                      f"{date}T{SLOTS[args.slot]}:00-03:00")
    error = ""
    for attempt in range(3):
        try:
            episode = draft(report, date, args.slot, history, error)
            episode["version"] = "1.0"
            episode["format"] = "ode-news-single"
            episode["episode_id"] = f"noticia-{date}-{args.slot}"
            episode["news_date"] = date
            episode["publication_target_local"] = f"{date}T{SLOTS[args.slot]}:00-03:00"
            episode["editorial_status"] = "autonomous_fact_checked"
            episode["reviewed_at"] = datetime.now(ZoneInfo("America/Fortaleza")).isoformat()
            episode["editorial_review_method"] = "Groq GPT-OSS 120B; independent publisher source corpus and literal source checks"
            validate(episode, today=local.date())
            prevent_repeated_story(episode, root)
            check_documentary_sources(episode)
            project = transform(episode)
            validate_publication_fields(project["publication"], episode["title"])
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(episode, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"NEWS_EPISODE_VALIDATED:{output}, attempt={attempt+1}")
            return
        except (ValueError, KeyError, TypeError, IndexError, RuntimeError, requests.RequestException) as exc:
            error = f"Falha real {type(exc).__name__}: {str(exc)[:400]}"
            print("EDITORIAL_RETRY:", error)
    raise SystemExit("Nenhum roteiro passou na verificação factual e estrutural.")


if __name__ == "__main__":
    main()
