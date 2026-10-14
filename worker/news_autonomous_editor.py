"""Autonomous newsroom: current research, truthful source checks, and episode JSON."""
import argparse
from datetime import datetime, timezone
from html import unescape
import json
import os
from pathlib import Path
import re
import traceback
import unicodedata
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import requests
from news_scout import collect
from news_source_corpus import collect_verified, extract_article
from news_groq_client import complete
from news_single_project import validate, transform
from build_youtube_package import validate_publication_fields

SLOTS = {"manha": "08:00", "meio-dia": "12:00", "noite": "20:00"}


DRAFT_SCHEMA_GUIDE = "FORMA EXATA OBRIGATÓRIA — use nomes de chaves literalmente:\nA raiz é UM OBJETO JSON, nunca uma lista, nunca um envelope episodes/episode.\nObjetos (mapas): news_selection, scorecard, discovery_strategy, pronunciations.\nListas de OBJETOS: title_options, sources, verified_facts, documentary_evidence, segments.\nListas de strings: tags, hashtags, secondary_keywords. context_photos=[].\n\nnews_selection é UM OBJETO ANINHADO com estas chaves:\ntopic_area, source_mode, independent_confirmation, new_fact, why_today,\nopening_anchor, candidate_review; acrescentar attribution_note no modo single_source_attributed.\nEscreva news_selection.why_today como STRING de pelo menos 30 caracteres:\nexplique o acontecimento novo ocorrido na data da edição a partir do relatório.\nNão colocar why_today na raiz. Não usar why_now, justification, rationale, reason\nou currentness no lugar de news_selection.why_today.\nnew_fact COPIA literalmente UM verified_facts[].claim. opening_anchor COPIA\num trecho literal único da primeira narration. independent_confirmation é BOOLEAN,\nnão string; true SOMENTE no modo corroborated com confirmação real, false na exclusiva.\ncandidate_review é LISTA de objetos com subject, topic_area, event_date, urls e decision;\nurls é lista de URLs reais; não inventar candidatas nem datas.\n\nscorecard é UM OBJETO com method (string), reason (string) e criteria (OBJETO/mapa).\nNão usar lista para scorecard ou criteria. criteria registra julgamentos editoriais,\nnão métricas de audiência.\n\ntitle_options é LISTA de objetos, cada qual com text (string) e\neditorial_quality (INTEIRO de 1 a 5). Primeiro escreva e avalie as três opções.\nDepois COPIE EXATAMENTE o text de uma opção com editorial_quality máxima para title,\nmantendo todas as palavras e pontuação. Nunca crie um quarto título fora da lista.\nA escolha deve continuar factual; pontuação editorial não é previsão de CTR.\n\nCada source, verified_fact, documentary_evidence e segment é OBJETO,\nnunca lista de pares ou objeto indexado pelo ID. Os IDs são campos dentro dos objetos.\nCampos não citados acima continuam obrigatórios conforme as regras abaixo.\nNão fabricar valores para preencher a forma: se a evidência não sustenta um campo,\ndeclare insuficiência em vez de inventar fato, fonte ou data."


def validate_draft_shape(episode):
    """Reject malformed model JSON without defaults, aliases or invented fields."""
    if not isinstance(episode, dict):
        raise ValueError("draft: a raiz JSON deve ser um objeto, nunca lista ou envelope")
    for key in ("news_selection", "scorecard", "discovery_strategy", "pronunciations"):
        if not isinstance(episode.get(key), dict):
            raise ValueError(f"draft.{key} precisa ser objeto JSON, não lista")
    for key in ("title_options", "sources", "verified_facts", "documentary_evidence", "segments"):
        value = episode.get(key)
        if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
            raise ValueError(f"draft.{key} precisa ser lista de objetos JSON")
    selection = episode["news_selection"]
    why_today = selection.get("why_today")
    if not isinstance(why_today, str) or len(why_today.strip()) < 30:
        raise ValueError("draft.news_selection.why_today é string obrigatória de 30+ caracteres; não usar why_now ou campo na raiz")
    title = episode.get("title")
    options = episode["title_options"]
    if not isinstance(title, str) or not options:
        raise ValueError("draft.title deve copiar uma opção de title_options")
    if any(not isinstance(option.get("text"), str)
           or type(option.get("editorial_quality")) is not int
           or not 1 <= option["editorial_quality"] <= 5 for option in options):
        raise ValueError("draft.title_options exige text string e editorial_quality inteiro de 1 a 5")
    maximum = max(option["editorial_quality"] for option in options)
    if not any(option["text"].strip() == title.strip()
               and option["editorial_quality"] == maximum for option in options):
        raise ValueError("draft.title deve copiar exatamente o text de uma opção com editorial_quality máxima")
    return episode




def bind_draft_metadata(episode):
    """Derive literal metadata from authored speech, never create or change facts."""
    segments = episode.get("segments") or []
    first = segments[0] if segments and isinstance(segments[0], dict) else {}
    opening = first.get("narration", "")
    selection = episode.get("news_selection") or {}
    discovery = episode.get("discovery_strategy") or {}
    if not isinstance(opening, str) or not isinstance(selection, dict) or not isinstance(discovery, dict):
        return episode
    anchor = selection.get("opening_anchor")
    matching = [fact for fact in episode.get("verified_facts", [])
                if isinstance(fact, dict) and fact.get("claim") == selection.get("new_fact")]
    valid_anchor = isinstance(anchor, str) and 20 <= len(anchor) <= 160 and opening.count(anchor) == 1
    if not valid_anchor and len(matching) == 1 and first.get("type") == "fact":
        claim_terms = set(re.findall(r"\w{3,}", matching[0]["claim"].casefold())) - {
            "uma", "para", "com", "que", "dos", "das", "por", "hoje", "nesta", "esse", "essa"}
        for sentence in re.split(r"(?<=[.!?])\s+", opening)[:3]:
            if sentence.rstrip().endswith("?") or re.search(r"(?i)\b(?:sou|aqui|chamo)\b.{0,20}\b(?:Roberto|Luana)\b", sentence):
                continue
            literal = sentence.strip()
            if len(literal) > 160:
                literal = literal[:160].rsplit(" ", 1)[0]
            overlap = claim_terms & set(re.findall(r"\w{3,}", literal.casefold()))
            if 20 <= len(literal) <= 160 and opening.count(literal) == 1 and len(overlap) >= 2:
                anchor = selection["opening_anchor"] = literal
                valid_anchor = True
                print("EDITORIAL_METADATA_BINDING news_selection.opening_anchor uses existing factual opening", flush=True)
                break
    payoff = discovery.get("first_payoff")
    if valid_anchor and isinstance(payoff, str) and len(payoff.strip()) >= 18 and payoff not in opening:
        discovery["first_payoff"] = anchor
        print("EDITORIAL_METADATA_BINDING discovery_strategy.first_payoff uses literal opening_anchor", flush=True)
    description = episode.get("publication_description")
    if (selection.get("source_mode") == "single_source_attributed"
            and selection.get("independent_confirmation") is False and len(matching) == 1
            and isinstance(description, str)):
        linked = [source for source in episode.get("sources", [])
                  if isinstance(source, dict) and source.get("id") in matching[0].get("source_ids", [])]
        if len(linked) == 1:
            publisher = linked[0].get("publisher")
            if isinstance(publisher, str) and len(publisher.strip()) >= 3 and publisher.casefold() not in (opening + " " + description).casefold():
                episode["publication_description"] = description.rstrip() + "\n\nApuração atribuída a " + publisher.strip() + ". Relato de uma fonte, sem confirmação independente."
    # Garantir identificação explícita de opinião do Roberto exigida pelo validador Zod
    for seg in episode.get("segments") or []:
        if isinstance(seg, dict) and seg.get("type") == "opinion":
            narr = str(seg.get("narration") or "").strip()
            if narr and not re.search(r"(?i)\b(minha leitura|minha opinião|na minha análise|meu ponto)\b", narr):
                seg["narration"] = "Na minha análise, " + narr[:1].lower() + narr[1:]
                print("EDITORIAL_METADATA_BINDING opinion segment prefixed with 'Na minha análise,'", flush=True)

    return episode


def plain(text):
    clean = (text or "").replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    clean = clean.replace("\u00a0", " ").replace("\u202f", " ").replace("\u200b", "")
    return " ".join(unicodedata.normalize(
        "NFKC", unescape(re.sub(r"<[^>]*>", " ", clean))
    ).casefold().split())


def publisher_host(url):
    parsed = urlparse(url)
    host = (parsed.hostname or "").casefold().removeprefix("www.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Documentary source URL cannot contain credentials.")
    if parsed.scheme != "https" or not host:
        raise ValueError("Documentary source must be a real HTTPS publisher page.")
    if host == "google.com" or host.endswith(".google.com"):
        raise ValueError("Google News is a candidate aggregator, not the publisher.")
    return host


def check_documentary_sources(episode):
    selection = episode.get("news_selection") or {}
    mode = selection.get("source_mode", "corroborated")
    if mode not in ("corroborated", "single_source_attributed"):
        raise ValueError("Unknown factual source mode.")
    sources = {source["id"]: source for source in episode["sources"]}
    checked = {}
    final_hosts = set()
    excerpts_by_url = {}
    for doc in episode["documentary_evidence"]:
        source = sources[doc["source_id"]]
        url = doc["source_page_url"]
        if url != source["url"]:
            raise ValueError("Documentary excerpt points to a different URL from its source.")
        publisher_host(url)
        expected = plain(doc["expected_text"])
        if len(expected) < 8:
            raise ValueError("Documentary quotation must contain at least eight characters.")
        if url not in checked:
            response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            final_hosts.add(publisher_host(response.url))
            if "text/html" not in response.headers.get("Content-Type", "").casefold():
                raise ValueError("News source did not return HTML.")
            # Shared article extractor excludes scripts, head, navigation,
            # boilerplate and declared hidden content; never match raw HTML.
            checked[url] = plain(extract_article(response.text[:2000000]))
        if expected not in checked[url]:
            raise ValueError("Quoted documentary text absent from the visible article: " + url)
        excerpts_by_url.setdefault(url, set()).add(expected)
    if mode == "corroborated":
        if len(final_hosts) < 2:
            raise ValueError("Corroborated mode needs at least two publisher domains.")
    else:
        matching = [fact for fact in episode["verified_facts"]
                    if fact.get("claim") == selection.get("new_fact")]
        if len(matching) != 1 or matching[0].get("status") != "statement":
            raise ValueError("A single-source new claim must remain an attributed statement.")
        if any(fact.get("status") == "confirmed" for fact in episode["verified_facts"]):
            raise ValueError("Single-source mode cannot promote a reported claim to confirmed.")
        primary_urls = {sources[source_id]["url"] for source_id in matching[0]["source_ids"]}
        if not any(len(excerpts_by_url.get(url, set())) >= 2 for url in primary_urls):
            raise ValueError("Single-source mode needs two distinct real excerpts from one primary article.")


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


def diagnostic_text(value, limit=1500):
    """Bounded operational text; never read credentials from the environment."""
    text = str(value)
    text = re.sub(r"(?i)(\b(?:groq_api_key|gemini_api_key|api[_-]?key|access[_-]?token|refresh[_-]?token)\b[\"']?\s*[:=]\s*[\"']?)[^\s&;,\"']+",
                  r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(\bBearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", text)
    text = re.sub(r"\bgsk_[A-Za-z0-9_-]{20,}\b|\bAIza[A-Za-z0-9_-]{30,}\b", "[REDACTED]", text)
    return text[:limit]


def safe_transport_diagnostics(data):
    """Copy only bounded transport state and token counts, never arbitrary payloads."""
    data = data or {}
    result = {}
    for key in ("provider", "model", "finish_reason"):
        if isinstance(data.get(key), str):
            result[key] = diagnostic_text(data[key], 180)
    for key in ("attempt", "http_status"):
        if type(data.get(key)) is int:
            result[key] = data[key]
    usage = data.get("usage") or {}
    if isinstance(usage, dict):
        result["usage"] = {key: usage[key] for key in
                           ("prompt_tokens", "completion_tokens", "total_tokens", "reasoning_tokens")
                           if type(usage.get(key)) is int and usage[key] >= 0}
    return result


def save_research_diagnostics(path, corpus, target, report=None, error_type=None, transport=None):
    if path is None:
        return
    record = {
        "phase": "research_model_output",
        "target_local": target,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "factual_review_completed": False,
        "scope": "Corpus metadata and unverified bounded model output; not factual approval.",
        "corpus": [{
            "url": diagnostic_text(entry.get("url", ""), 1200),
            "headline": diagnostic_text(entry.get("headline", ""), 240),
            "publisher_host": diagnostic_text(entry.get("publisher_host", ""), 180),
            "feed_published_utc": diagnostic_text(entry.get("feed_published_utc", ""), 100),
            "article_characters": len(entry.get("actual_article_text", "")),
        } for entry in corpus],
        "model_report": None,
        "rejection_reasons": [],
        "error_type": error_type,
        "transport": safe_transport_diagnostics(transport),
    }
    if report is not None:
        preview = report
        # A model may copy a supplied body; omit full copies before bounding.
        for entry in corpus:
            body = entry.get("actual_article_text", "")
            if body:
                preview = preview.replace(body, "[FULL_ARTICLE_BODY_OMITTED]")
        record["model_report"] = {
            "characters": len(report),
            "preview": diagnostic_text(preview),
            "preview_truncated": len(preview) > 1500,
        }
        if "EDITORIAL_INSUFFICIENT_EVIDENCE" in report:
            record["rejection_reasons"].append("marker")
        if len(report) < 400:
            record["rejection_reasons"].append("short_report")
        if (transport or {}).get("finish_reason") == "length":
            record["rejection_reasons"].append("response_truncated")
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if report is not None or error_type is not None:
        print("EDITORIAL_RESEARCH_DIAGNOSTIC", json.dumps(record, ensure_ascii=False), flush=True)


def research(candidates, history, target, diagnostic_path=None):
    """Select an actually verified new event from publisher pages, without model web tools."""
    corpus = collect_verified(candidates)
    # Keep below the Groq free-plan TPM limit. Literal excerpts + real URLs are
    # the only evidence the editor may use; full pages remain checked downstream.
    compact = [
        {**{k: entry[k] for k in ("category", "headline", "publisher_host", "url", "feed_published_utc")},
         "actual_article_text": entry["actual_article_text"][:1550]}
        for entry in corpus[:10]
    ]
    day = target[:10] if (isinstance(target, str) and len(target) >= 10 and target[4] == "-" and target[7] == "-") else datetime.now(ZoneInfo("America/Fortaleza")).date().isoformat()
    prompt = f"""Você é editor de apuração do canal O Dinheiro Explica.
Hoje em Fortaleza: {datetime.now(ZoneInfo('America/Fortaleza')).isoformat()}. Janela: {target}. Data do episódio: {day}.
Compare pautas atuais, incluindo política e economia, usando SOMENTE os textos reais abaixo.
Descubra um FATO NOVO ocorrido em {day} (ou hoje). PREFIRA confirmação explícita em dois publicadores realmente independentes (source_mode=corroborated).\nUma matéria exclusiva de um único publicador também pode ser selecionada quando o texto demonstra o acontecimento de {day} (ou hoje): source_mode=single_source_attributed, independent_confirmation=false. Nesse caso, apresente o acontecimento como RELATO ATRIBUÍDO, nunca como confirmação independente.
Dia da publicação da reportagem NÃO equivale ao dia do fato; se não houver prova atual, declare.
Priorize páginas com texto literal para captura. NÃO invente links, datas ou trechos.
Quando houver duas páginas, verifique se tratam realmente do mesmo acontecimento e não apenas repetem a mesma agência. Em fonte única, informe honestamente a ausência de segunda confirmação e os limites da reportagem.
Identifique nome e URLs exatas, data original do fato, e ao menos quatro fatos com evidência.
Histórico (não repetir acontecimentos): {json.dumps(history[-12:], ensure_ascii=False)[:2000]}.
CORPUS de páginas HTTP realmente consultadas:
{json.dumps(compact, ensure_ascii=False)[:20000]}
Se não houver relato de acontecimento de {day} (ou hoje) sustentado por texto real, seja corroborado ou atribuído a fonte única, devolva
exatamente EDITORIAL_INSUFFICIENT_EVIDENCE, sem fabricar material. Não descarte automaticamente uma exclusiva só porque ainda não foi republicada.
Caso exista, comece com SOURCE_MODE: corroborated ou SOURCE_MODE: single_source_attributed. Escreva relatório factual de 500 a 750 palavras, incluindo URLs e pelo
menos dois trechos LITERAIS DIFERENTES realmente presentes no corpus, preferindo trechos de 15 a 70 caracteres. Na exclusiva, os dois trechos devem vir da mesma matéria HTML; não simule duas fontes porque há dois recortes."""
    transport_diag = {}
    save_research_diagnostics(diagnostic_path, corpus, target, transport=transport_diag)
    try:
        report = complete(prompt, diagnostics=transport_diag)
    except Exception as exc:
        save_research_diagnostics(diagnostic_path, corpus, target, error_type=type(exc).__name__, transport=transport_diag)
        raise
    save_research_diagnostics(diagnostic_path, corpus, target, report=report, transport=transport_diag)
    if transport_diag.get("finish_reason") == "length":
        raise RuntimeError("Groq cortou o relatório no limite de resposta; não usar apuração incompleta.")
    if "EDITORIAL_INSUFFICIENT_EVIDENCE" in report or len(report) < 400:
        raise RuntimeError("Corpus não demonstra um relato verificável de acontecimento de hoje.")
    return report


def draft(report, day, slot, history, error, diagnostics=None):
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

{DRAFT_SCHEMA_GUIDE}

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
news_selection: objeto contendo topic_area (politics,economy,personal_finance,business,international); source_mode="corroborated" ou "single_source_attributed", segundo as provas reais do relatório.
new_fact deve ser EXATAMENTE um claim de verified_facts com event_date={day}, status diferente de background, e fonte publicada em {day}.
No modo corroborated: source_ids de pelo menos DOIS publicadores independentes e independent_confirmation=true.
No modo single_source_attributed: fonte real da exclusiva vinculada, status do new_fact="statement", independent_confirmation=false e attribution_note de pelo menos 30 caracteres explicando atribuição e limites. Nomeie o publisher literal da fonte na abertura OU na publication_description. Todos os relatos dessa matéria continuam statement; contexto histórico pode ser background. Não use status confirmed, nem transforme declaração, acusação, risco ou previsão em fato consumado.
why_today: motivo concreto de 30+ caracteres; opening_anchor: trecho literal de 20 a 160 caracteres presente uma vez na narração inicial; candidate_review: candidatas reais comparadas, incluindo política, datas reais do fato, URLs e justificativas. Não inventar candidatas.
scorecard: method, reason, criteria com julgamentos editoriais e não
CTR ou dados inventados.

sources: de 1 a 3 objetos, URLs REAIS HTTPS verificáveis do relatório e capturáveis sem HTTP 403,
cada item id (S1, S2...), publisher, url, published_at YYYY-MM-DD,
role; corroborated exige ao menos dois publicadores/dominios independentes; single_source_attributed permite um publicador, com sua identificação verdadeira. Período de até 45 dias para contexto, mantendo o fato novo no dia da edição.
verified_facts: quatro ou mais itens {{claim,source_ids,status,event_date}}
com status SOMENTE "statement","background","forecast_not_collected",
"projection","confirmed"; source_ids devem existir.
documentary_evidence: pelo menos dois recortes reais; cada objeto precisa de
id estável (doc-1, doc-2...), source_id e expected_text.
expected_text é cópia EXATA, CONTÍNUA e LITERAL de uma frase ou oração real
de >=8 caracteres: não altere palavras/pontuação nem junte fragmentos separados.
O código preenche kind="source_excerpt", source_page_url a partir da URL da fonte,
capture_file a partir do id e attribution a partir do publisher real quando omitidos.
Se escrever esses campos, preserve os valores corretos. Crédito curto real é válido.
rights_review é opcional para esses recortes; não invente licença, permissão de uso
ou aprovação jurídica. Registre somente restrições concretas conhecidas.
Use material suficiente para as cenas: N cenas precisam de pelo menos N-2 recortes distintos.
No modo single_source_attributed, use ao menos DOIS expected_text DIFERENTES da MESMA página HTML da exclusiva; não use cópias do mesmo trecho ou scripts, metadados, links de navegação ou conteúdo escondido como prova. Não simule duas matérias ou duas confirmações.
Não adicionar reconstrução editorial fictícia ou fotos da imprensa.
context_photos=[].

segments: de 4 a 9 cenas conforme a explicação precisar, com pelo menos duas fact,
uma opinion e conclusão. A primeira cena abre com o fato novo real e inclui
news_selection.opening_anchor literalmente. Organize a progressão naturalmente.
Na cena de tipo 'opinion', a fala (narration) DEVE OBRIGATORIAMENTE começar com 'Na minha análise,' ou 'Na minha opinião,'.
Cada objeto deve ter id,title,type,label,headline,metric,object_type
(data/store/cash/bank/package/truck/factory), visual_cards com 3-5
strings de 6-65 caracteres, narration com a extensão necessária para explicar
o ponto (desenvolvimento claro de 45 a 85 palavras; no mínimo 32 palavras por cena), document_id do recorte pertinente
e media_side left/right. Não alternar documentos sem motivo editorial.
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
    raw = complete(prompt, json_mode=True, diagnostics=diagnostics)
    if (diagnostics or {}).get("finish_reason") == "length":
        raise RuntimeError("Groq cortou o roteiro no limite de resposta; não usar JSON incompleto.")
    episode = json.loads(raw)
    if not isinstance(episode, dict):
        raise ValueError("Groq deve retornar um objeto JSON na raiz, nunca uma lista.")
    episode = clean_unicode_spaces(episode)
    return bind_draft_metadata(validate_draft_shape(episode))


def clean_unicode_spaces(obj):
    if isinstance(obj, str):
        s = obj.replace("\u2011", "-")
        return s.replace("\u00a0", " ").replace("\u202f", " ").replace("\u200b", "")
    elif isinstance(obj, list):
        return [clean_unicode_spaces(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: clean_unicode_spaces(v) for k, v in obj.items()}
    return obj


def record_draft_diagnostic(path, attempt, episode, transport, error=None):
    """Record structure and call metrics; rejected output is never editorial approval."""
    target = Path(path)
    record = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
    item = {"attempt": attempt, "validated": error is None,
            "transport": safe_transport_diagnostics(transport),
            "error_type": type(error).__name__ if error else None,
            "error": diagnostic_text(str(error), 500) if error else None,
            "field_types": {key: type(value).__name__ for key, value in episode.items()}
                           if isinstance(episode, dict) else {"root": type(episode).__name__}}
    if error:
        item["location"] = [{"file": Path(frame.filename).name, "line": frame.lineno,
                              "function": frame.name} for frame in traceback.extract_tb(error.__traceback__)[-3:]]
    record.setdefault("draft_attempts", []).append(item)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if isinstance(episode, dict) and error:
        recovery = {"status": "unverified_rejected_draft", "factual_approval": False,
                    "attempt": attempt, "draft": episode}
        recovery_path = target.with_name(f"news-editorial-rejected-draft-{attempt}.json")
        recovery_path.write_text(diagnostic_text(json.dumps(recovery, ensure_ascii=False, indent=2), 40000) + "\n", encoding="utf-8")
    print("EDITORIAL_DRAFT_DIAGNOSTIC", json.dumps(item, ensure_ascii=False), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slot", choices=SLOTS, required=True)
    p.add_argument("--date", default=None, help="Data YYYY-MM-DD da edição; padrão hoje em Fortaleza")
    p.add_argument("--root", default=".")
    args = p.parse_args()
    if not os.getenv("GROQ_API_KEY"):
        raise SystemExit("GROQ_API_KEY inexistente; configurar secret no GitHub.")
    local = datetime.now(ZoneInfo("America/Fortaleza"))
    date = args.date or local.date().isoformat()
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
                      f"{date}T{SLOTS[args.slot]}:00-03:00",
                      diagnostic_path=root / "render-output" / "news-editorial-diagnostics.json")
    error = ""
    for attempt in range(3):
        episode = None
        transport = {}
        try:
            episode = draft(report, date, args.slot, history, error, diagnostics=transport)
            episode["version"] = "1.0"
            episode["format"] = "ode-news-single"
            episode["episode_id"] = f"noticia-{date}-{args.slot}"
            episode["news_date"] = date
            episode["publication_target_local"] = f"{date}T{SLOTS[args.slot]}:00-03:00"
            episode["editorial_status"] = "autonomous_fact_checked"
            episode["reviewed_at"] = datetime.now(ZoneInfo("America/Fortaleza")).isoformat()
            episode["editorial_review_method"] = (
                "Groq GPT-OSS 120B; fetched publisher corpus and literal source checks; source_mode="
                + (episode.get("news_selection") or {}).get("source_mode", "corroborated")
            )
            episode = validate(episode, today=local.date())
            prevent_repeated_story(episode, root)
            check_documentary_sources(episode)
            project = transform(episode)
            validate_publication_fields(project["publication"], episode["title"])
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(episode, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            record_draft_diagnostic(root / "render-output/news-editorial-diagnostics.json",
                                    attempt + 1, episode, transport)
            print(f"NEWS_EPISODE_VALIDATED:{output}, attempt={attempt+1}")
            return
        except (ValueError, KeyError, TypeError, IndexError, RuntimeError, requests.RequestException) as exc:
            record_draft_diagnostic(root / "render-output/news-editorial-diagnostics.json",
                                    attempt + 1, episode, transport, exc)
            error = f"Falha real {type(exc).__name__}: {str(exc)[:400]}"
            print("EDITORIAL_RETRY:", error)
    raise SystemExit("Nenhum roteiro passou na verificação factual e estrutural.")


if __name__ == "__main__":
    main()
