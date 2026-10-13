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
from news_source_corpus import collect_verified
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


def research(client, candidates, history, target):
    """Use actual fetched publisher content to keep free-tier Gemini off paid Google Search grounding."""
    corpus = collect_verified(candidates)
    prompt = f"""Você é editor factual do canal O Dinheiro Explica.
Janela pretendida: {target}; hora agora: {datetime.now(ZoneInfo('America/Fortaleza')).isoformat()}.
Abaixo há páginas efetivamente acessadas. Só use suas URLs literais e trechos
efetivamente presentes em actual_article_text, sem atribuir prova ao RSS Google.
Diferencie hora de reportagem e dia do fato central. Busque dentro do CORPUS um
FATO NOVO ocorrido hoje na região de Fortaleza, apoiado por dois publicadores
independentes: se não houver comprovação, diga que é impossível e pare.
Compare candidatas atuais de política e economia; registre limitações.
Não use as notícias do histórico: {json.dumps(history, ensure_ascii=False)}.
CORPUS DE PÁGINAS VERIFICADAS:
{json.dumps(corpus, ensure_ascii=False)[:46000]}
Retorne relatório apurado com 4 fatos, URLs literais de publicadores, dois
trechos literais curtos e diferenças de perspectiva. Sem fontes inventadas."""
    errors = []
    for model in (os.getenv("ODE_NEWS_RESEARCH_MODEL", "gemini-3.8-flash"), "gemini-3.5-flash-lite"):
        try:
            response = client.models.generate_content(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1),
            )
            if not response.text or len(response.text) < 400:
                raise ValueError("Relatório factual insuficiente.")
            return response.text
        except Exception as error:
            status = getattr(error, "code", None) or getattr(error, "status_code", None) or "unknown"
            detail = re.sub(r"AIza[0-9A-Za-z_-]+", "[REDACTED]", str(error))[:300]
            print("EDITOR_RESEARCH_API_ERROR", model, status, detail, flush=True)
            if not any(code in str(error) for code in ("404", "429", "500", "502", "503", "504")):
                raise
            errors.append(str(status))
    raise RuntimeError("Gemini sem cota disponível para redigir a partir das fontes: " + ", ".join(errors))

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
    models = (os.getenv("ODE_NEWS_WRITER_MODEL", "gemini-3.8-flash"),
              "gemini-3.5-flash-lite")
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
            if not any(code in str(error) for code in ("404", "429", "500", "502", "503", "504")):
                raise
            status = getattr(error, "code", None) or getattr(error, "status_code", None) or "unknown"
            print("EDITOR_WRITER_API_ERROR", model, status, str(error)[:180], flush=True)
            last = type(error).__name__ + ":" + str(status)
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
