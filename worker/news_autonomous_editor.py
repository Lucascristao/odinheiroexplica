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
from google import genai
from google.genai import types
from news_scout import collect
from news_single_project import validate

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


def research(client, candidates, history, target):
    prompt = f"""Você é repórter de O Dinheiro Explica, Brasil.
Horário de publicação pretendido: {target}; hora da pesquisa:
{datetime.now(ZoneInfo('America/Fortaleza')).isoformat()}.
Escolha UMA notícia atual, concreta, verificável e diferente do histórico.
É OBRIGATÓRIO pesquisar a internet real pela ferramenta Google Search grounding.
Candidatos RSS não apurados: {json.dumps(candidates[:28], ensure_ascii=False)}.
Histórico: {json.dumps(history, ensure_ascii=False)}.
Investigue uma pauta com consequência para brasileiros e prova documental.
Retorne relatório factual detalhado com datas, ao menos 4 fatos separados
e pelo menos 2 URLs HTTPS COMPLETAS de matérias reais de diferentes editoras,
com trechos LITERAIS comprováveis no texto da página, não links Google News.
Priorize matérias públicas e acessíveis para captura de trechos pelo navegador.
Separe afirmações do governo, fato, projeção, controvérsia e opinião.
Não invente números, fotos, notícias, links ou citações.
Relatório em texto com URLs e trechos originais."""
    response = None
    failures = []
    for model in (os.getenv("ODE_NEWS_RESEARCH_MODEL", "gemini-3.1-pro-preview"),
                  "gemini-2.5-flash-lite"):
        try:
            response = client.models.generate_content(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())], temperature=0.2
                ),
            )
            break
        except Exception as error:
            if "404" not in str(error) and "429" not in str(error):
                raise
            failures.append(model + ":" + type(error).__name__)
    if response is None:
        raise RuntimeError("Pesquisa indisponível nos modelos autorizados: " + ", ".join(failures))
    grounding = getattr(response.candidates[0], "grounding_metadata", None)
    if not grounding or not getattr(grounding, "grounding_chunks", None):
        raise RuntimeError("A pesquisa não trouxe confirmações por grounding.")
    if not response.text or len(response.text) < 400:
        raise RuntimeError("Pesquisa superficial, sem relatório suficiente.")
    return response.text


def draft(client, report, day, slot, history, error):
    target = SLOTS[slot]
    prompt = f"""Retorne SOMENTE um objeto JSON válido, em português do Brasil,
para um episódio jornalístico de notícia ÚNICA do canal O Dinheiro Explica.
A redação foi pesquisada por Google Search grounding:
{report}
Assuntos proibidos por repetição: {json.dumps(history, ensure_ascii=False)}.
Revisão de erro anterior: {error[:1200]}. Data: {day}, janela: {slot}.
Roberto, brasileiro, conversacional e crítico na economia, com opiniões
nitidamente separadas dos fatos. Não imitar fala nem slogan de ANCAPSU/Piter.
Objetivo é CTR legítimo e compreensão, nunca clickbait enganoso.

Esquema TOP-LEVEL obrigatório:
version, format, episode_id, news_date, event_date, editorial_status,
reviewed_at, title, title_options, thumbnail_headline,
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
igual/menor à data atual e ligado ao acontecimento verificado.

title: 20-100 caracteres, factual e magnético, assunto no começo.
title_options: lista de três objetos com text e editorial_quality (1-5).
thumbnail_headline: 8-34 caracteres e 2-5 palavras, distinta do título.
thumbnail_primary: protagonista visual específico da notícia.
thumbnail_tension: tensão editorial comprovável, sem mentira.
thumbnail_composition: enquadramento e posição do protagonista próprios.
thumbnail_text_side: "left" ou "right", lado oposto ao protagonista.
scorecard: method, reason, criteria com julgamentos editoriais e não
CTR ou dados inventados.

sources: 2 ou 3 objetos, URLs REAIS HTTPS verificáveis do relatório,
cada item id (S1, S2...), publisher, url, published_at YYYY-MM-DD,
role; no mínimo dois publicadores/dominios diferentes, até 45 dias.
verified_facts: quatro ou mais itens {claim,source_ids,status}
com status SOMENTE "statement","background","forecast_not_collected",
"projection","confirmed"; source_ids devem existir.
documentary_evidence: exatamente dois ou três itens com id doc-1,doc-2
etc, kind="source_excerpt", source_id, source_page_url IGUAL à URL
original da fonte, expected_text sendo TRECHO VERBATIM copiado da matéria
real de >=8 caracteres, attribution, rights_review com explicação da
citação curta e capture_file "research/captures/doc-1.png" etc.
Não adicionar reconstrução editorial fictícia ou fotos da imprensa.
context_photos=[].

segments: EXATAMENTE QUATRO cenas, types nesta ordem fact,fact,opinion,outro.
Cada objeto deve ter id,title,type,label,headline,metric,object_type
(data/store/cash/bank/package/truck/factory), visual_cards com 3-5
strings de 6-65 caracteres, narration de 85-125 PALAVRAS, document_id
doc-1/doc-2 alternando, media_side left/right.
Todas as cenas exibem documento real, incluindo o comentário opinativo.
Pelo menos 2 cenas factuais com prova. Uma opinião editorial fundamentada
sem fatos inventados. Final responde à pergunta inicial.
Não incluir photo_id ao usar document_id.
engagement_question termina em ponto de interrogação.
hashtags: três hashtags específicas, sem espaço.
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
Não invente datas ou alegações sem respaldo documental."""
    models = (os.getenv("ODE_NEWS_WRITER_MODEL", "gemini-3.1-pro-preview"),
              "gemini-2.5-flash-lite")
    last = None
    for model in models:
        try:
            response = client.models.generate_content(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json", temperature=0.25
                ),
            )
            return json.loads(response.text)
        except Exception as error:
            if "404" not in str(error) and "429" not in str(error):
                raise
            last = type(error).__name__
    raise RuntimeError("Nenhum modelo conseguiu gerar JSON: " + str(last))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slot", choices=SLOTS, required=True)
    p.add_argument("--root", default=".")
    args = p.parse_args()
    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit("GEMINI_API_KEY inexistente; sem apuração automática.")
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
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    history = existing_history(root)
    report = research(client, candidates["candidates"], history,
                      f"{date}T{SLOTS[args.slot]}:00-03:00")
    error = ""
    for attempt in range(3):
        try:
            episode = draft(client, report, date, args.slot, history, error)
            episode["version"] = "1.0"
            episode["format"] = "ode-news-single"
            episode["episode_id"] = f"noticia-{date}-{args.slot}"
            episode["news_date"] = date
            episode["publication_target_local"] = f"{date}T{SLOTS[args.slot]}:00-03:00"
            episode["editorial_status"] = "autonomous_fact_checked"
            episode["reviewed_at"] = datetime.now(ZoneInfo("America/Fortaleza")).isoformat()
            episode["editorial_review_method"] = "AI Google Search grounded research and literal source checks"
            validate(episode, today=local.date())
            check_documentary_sources(episode)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(episode, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"NEWS_EPISODE_VALIDATED:{output}, attempt={attempt+1}")
            return
        except (ValueError, KeyError, TypeError, IndexError, requests.RequestException) as exc:
            error = f"Falha real {type(exc).__name__}: {str(exc)[:400]}"
            print("EDITORIAL_RETRY:", error)
    raise SystemExit("Nenhum roteiro passou na verificação factual e estrutural.")


if __name__ == "__main__":
    main()
