"""Single-story newsroom adapter: fact-checked topical news -> canonical Remotion + Gemini Live.

No fabricated articles/images/trends. Scene transitions carry sourced B-roll captures
and a transparent right-of-center opinion segment by Roberto.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta, datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from news_project import anchors, require
from build_youtube_package import validate_publication_fields
from visual_anchor import normalize_text


SELECTION_POLICY_START = datetime(2026, 10, 11, 21, tzinfo=timezone.utc)
NEWS_TOPIC_AREAS = {"politics", "economy", "personal_finance", "business", "international"}


def validate_news_selection(episode: dict, news_day: date) -> None:
    """Check the editor's dated evidence, without claiming semantic fact checking.

    Freeze the policy against the original review so archived resumes keep their
    contracts, voice caches and thumbnail hashes. Dates remain the editor's
    responsibility: a newly published article is not necessarily a new event.
    """
    reviewed = datetime.fromisoformat(episode["reviewed_at"].replace("Z", "+00:00"))
    if reviewed.tzinfo is None:
        reviewed = reviewed.replace(tzinfo=timezone.utc)
    required = (episode["editorial_status"] == "autonomous_fact_checked"
                and reviewed >= SELECTION_POLICY_START)
    selection = episode.get("news_selection")
    if not required and selection is None:
        return
    require(isinstance(selection, dict), "seleção atual sem news_selection")
    require(selection.get("topic_area") in NEWS_TOPIC_AREAS, "editoria da notícia inválida")
    require(episode.get("event_date") == news_day.isoformat(),
            "o acontecimento novo precisa ser do dia da edição; reportagem recente não renova fato antigo")
    require(isinstance(selection.get("why_today"), str)
            and len(selection["why_today"].strip()) >= 30, "seleção sem justificativa de atualidade")
    fact_text = selection.get("new_fact")
    require(isinstance(fact_text, str) and len(fact_text.strip()) >= 30,
            "seleção sem fato novo literal")
    matching = [fact for fact in episode["verified_facts"] if fact.get("claim") == fact_text]
    require(len(matching) == 1, "fato novo precisa corresponder a um único verified_fact")
    fact = matching[0]
    require(fact.get("event_date") == news_day.isoformat() and fact.get("status") != "background",
            "fato novo sem data do acontecimento ou classificado apenas como contexto")
    linked = [source for source in episode["sources"] if source["id"] in fact["source_ids"]]
    source_mode = selection.get("source_mode", "corroborated")
    require(source_mode in ("corroborated", "single_source_attributed"),
            "modo de comprovação jornalística inválido")
    if source_mode == "corroborated":
        require(len({urlparse(source["url"]).hostname.casefold().removeprefix("www.")
                     for source in linked}) >= 2, "fato novo precisa de dois publicadores")
        require(selection.get("independent_confirmation", True) is True,
                "confirmação independente não pode ser negada no modo corroborated")
    else:
        require(len(linked) >= 1, "notícia exclusiva sem fonte real vinculada")
        require(selection.get("independent_confirmation") is False,
                "fonte única exige sinalizar ausência de confirmação independente")
        require(fact.get("status") == "statement",
                "fonte única precisa ser apresentada como relato atribuído, não fato confirmado")
        require(len(str(selection.get("attribution_note") or "").strip()) >= 30,
                "fonte única exige explicação de atribuição e limites")
        publisher = str(linked[0].get("publisher") or "").strip()
        opening = (episode.get("segments") or [{}])[0].get("narration", "")
        description = str(episode.get("publication_description") or "")
        require(len(publisher) >= 3 and publisher.casefold() in (opening + " " + description).casefold(),
                "fonte única exige nomear publicador na abertura ou descrição")
    require(any(source["published_at"] == news_day.isoformat() for source in linked),
            "fato novo sem fonte publicada no dia da edição")
    anchor = selection.get("opening_anchor")
    opening = (episode.get("segments") or [{}])[0].get("narration", "")
    require(isinstance(anchor, str) and 20 <= len(anchor) <= 160
            and opening.count(anchor) == 1,
            "a abertura precisa apresentar o fato novo com trecho literal único de 20 a 160 caracteres")


def normalize_documentary_metadata(episode: dict) -> dict:
    """Fill technical source-excerpt metadata from existing proof, never facts or rights.

    Return the original object when complete so historical renders retain exactly
    their serialized content. A supplied quote, URL, credit or kind is not rewritten.
    """
    sources = {source.get("id"): source for source in episode.get("sources", [])
               if isinstance(source, dict) and isinstance(source.get("id"), str)}
    documents = episode.get("documentary_evidence")
    if not isinstance(documents, list):
        return episode
    result = []
    changed = False
    for doc in documents:
        if not isinstance(doc, dict):
            result.append(doc)
            continue
        source = sources.get(doc.get("source_id"), {})
        url = source.get("url")
        quote = doc.get("expected_text")
        updated = dict(doc)
        # Metadata cannot make an absent source or an absent quotation usable.
        if (isinstance(url, str) and url.startswith("https://")
                and isinstance(quote, str) and len(quote) >= 8
                and doc.get("kind", "source_excerpt") == "source_excerpt"):
            if "kind" not in updated:
                updated["kind"] = "source_excerpt"
            if not updated.get("source_page_url"):
                updated["source_page_url"] = url
            identifier = updated.get("id")
            capture = updated.get("capture_file")
            if ((not capture or not str(capture).startswith("research/captures/"))
                    and isinstance(identifier, str)
                    and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,119}", identifier)):
                updated["capture_file"] = f"research/captures/{identifier}.png"
            if not str(updated.get("attribution") or "").strip():
                publisher = source.get("publisher")
                if isinstance(publisher, str) and publisher.strip():
                    title = source.get("title")
                    updated["attribution"] = publisher.strip() + (
                        "; " + title.strip() if isinstance(title, str) and title.strip() else "")
        changed = changed or updated != doc
        result.append(updated)
    return {**episode, "documentary_evidence": result} if changed else episode


def validate(episode: dict, today: date | None = None) -> dict:
    episode = normalize_documentary_metadata(episode)
    today = today or date.today()
    require(episode.get("format") == "ode-news-single", "formato deve conter uma matéria por vídeo")
    ep_id = str(episode.get("episode_id") or "")
    require(bool(re.fullmatch(r"noticia-\d{4}-\d{2}-\d{2}-[a-z0-9-]+", ep_id)), "ID do episódio inválido")
    news_day = date.fromisoformat(episode["news_date"])
    require(ep_id.startswith("noticia-" + news_day.isoformat() + "-"), "ID e data divergem")
    require(news_day <= today + timedelta(days=1), "episódio de notícia futura")
    require(episode.get("editorial_status") in ("approved_for_private_pilot", "autonomous_fact_checked"), "roteiro ainda não verificado")
    require(bool(episode.get("reviewed_at")), "sem data da revisão editorial")
    require(20 <= len(str(episode.get("title", ""))) <= 100, "título inválido")
    require(8 <= len(str(episode.get("thumbnail_headline", ""))) <= 34, "headline da capa inválida")
    title_options = episode.get("title_options") or []
    require(len(title_options) >= 3, "comparar pelo menos três alternativas de título")
    titles = [str(option.get("text", "")).strip() for option in title_options if isinstance(option, dict)]
    require(len(titles) == len(title_options) and all(20 <= len(text) <= 100 for text in titles),
            "alternativas de título incompletas")
    require(len({re.sub(r"\s+", " ", text).casefold() for text in titles}) >= 3,
            "as três alternativas de título precisam ser diferentes")
    require(episode["title"].strip() in titles,
            "título final não corresponde às alternativas avaliadas")
    ratings = [option.get("editorial_quality") for option in title_options]
    require(all(type(rating) is int and 1 <= rating <= 5 for rating in ratings),
            "alternativas sem pontuação editorial de 1 a 5")
    require(max(rating for text, rating in zip(titles, ratings) if text == episode["title"].strip()) == max(ratings),
            "título final não é a melhor alternativa segundo a avaliação registrada")
    require(episode.get("scorecard", {}).get("method") and episode["scorecard"].get("reason"),
            "avaliação de potencial ausente")
    discovery = episode.get("discovery_strategy") or {}
    for field in ("viewer_intent", "search_query", "recommendation_angle", "first_payoff",
                  "promise_proof", "audience_hypothesis", "thumbnail_complement",
                  "verification_limits"):
        require(isinstance(discovery.get(field), str) and len(discovery[field].strip()) >= 18,
                f"estratégia YouTube sem {field}")
    require(discovery["first_payoff"] in (episode.get("segments") or [{}])[0].get("narration", ""),
            "a primeira entrega precisa ser trecho literal da abertura")
    require(episode["thumbnail_headline"].casefold() not in episode["title"].casefold(),
            "capa não pode repetir o título")
    keyword = str(episode.get("primary_keyword") or "").strip()
    title = str(episode.get("title") or "").strip()
    description = str(episode.get("publication_description") or "").strip()
    if not keyword:
        candidates = [t for t in episode.get("tags", []) if isinstance(t, str) and len(t) >= 3]
        keyword = candidates[0] if candidates else "economia"
        episode["primary_keyword"] = keyword
    if keyword.casefold() not in (title + " " + description).casefold():
        description = (description + f"\n\nContexto: {keyword}").strip()
        episode["publication_description"] = description
    require(episode["primary_keyword"].casefold() in
            (episode["title"] + " " + episode.get("publication_description", "")).casefold(),
            "palavra-chave relevante precisa existir em título ou descrição")
    require(episode.get("engagement_question", "").endswith("?"), "pergunta final inválida")
    # The downstream YouTube packager's rules must fail here, before costly TTS.
    validate_publication_fields({
        "description": episode.get("publication_description"),
        "seo": {"primary_keyword": episode.get("primary_keyword")},
        "engagement_question": episode.get("engagement_question"),
        "hashtags": episode.get("hashtags"),
    }, episode["title"])
    sources = episode.get("sources") or []
    source_mode = (episode.get("news_selection") or {}).get("source_mode", "corroborated")
    min_sources = 1 if source_mode == "single_source_attributed" else 2
    require(len(sources) >= min_sources, "apuração sem o mínimo de fontes reais do modo editorial")
    hosts = set()
    source_ids = set()
    for source in sources:
        url = urlparse(source.get("url", ""))
        require(url.scheme == "https" and url.hostname and len(url.path) >= 8, "fonte sem URL específica")
        hosts.add(url.hostname.casefold().removeprefix("www."))
        require(source.get("id") not in source_ids, "fonte duplicada")
        source_ids.add(source["id"])
        published = date.fromisoformat(source["published_at"])
        require(published <= news_day and published >= news_day - timedelta(days=45), "fonte fora do período documentado")
    if source_mode != "single_source_attributed":
        require(len(hosts) >= 2, "fontes precisam incluir publicadores diferentes")
    claims = episode.get("verified_facts") or []
    require(len(claims) >= 4, "menos de quatro fatos apurados")
    for claim in claims:
        require(claim.get("source_ids") and set(claim["source_ids"]) <= source_ids, "fato sem fonte identificável")
        require(claim.get("status") in ("statement", "background", "forecast_not_collected", "projection", "confirmed"), "tipo factual desconhecido")
    validate_news_selection(episode, news_day)
    documentary = episode.get("documentary_evidence") or []
    require(len(documentary) >= 2, "exigir pelo menos duas referências visuais documentais")
    doc_ids = set()
    for doc in documentary:
        require(doc.get("kind") == "source_excerpt", "imagem deve ser captura de evidência identificada")
        require(doc.get("source_id") in source_ids, "evidência sem fonte")
        require(len(doc.get("expected_text", "")) >= 8, "falta texto verificável na matéria")
        source = next(s for s in sources if s["id"] == doc["source_id"])
        require(doc.get("source_page_url", "").startswith("https://")
                and doc["source_page_url"] == source["url"],
                f"documento {doc.get('id')}: source_page_url deve corresponder à URL da fonte vinculada")
        require(isinstance(doc.get("attribution"), str) and bool(doc["attribution"].strip()),
                f"documento {doc.get('id')}: informar attribution ou publisher real na fonte vinculada")
        # A short authentic credit is enough. Boilerplate rights_review does not
        # prove a license; source excerpts remain subject to real text/capture
        # verification. Photo licensing/contextual-use checks below are unchanged.
        require(doc.get("capture_file", "").startswith("research/captures/"), "caminho de captura inválido")
        rec = doc.get("editorial_reconstruction")
        if rec is not None:
            require(isinstance(rec, dict), "reconstrução editorial inválida")
            source = next(s for s in sources if s["id"] == doc["source_id"])
            require(rec.get("publisher") == source["publisher"], "fonte da reconstrução divergente")
            require(rec.get("published_at") == source["published_at"], "data da reconstrução divergente")
            require(20 <= len(str(rec.get("headline", ""))) <= 180, "manchete editorial inválida")
            require(30 <= len(str(rec.get("context", ""))) <= 420, "resumo editorial inválido")
            require(any(doc["source_id"] in fact["source_ids"] for fact in claims),
                    "reconstrução sem fato verificado ligado à fonte")
        require(doc["id"] not in doc_ids, "asset duplicado")
        if doc.get("capture_sha256") is not None:
            require(bool(re.fullmatch(r"[a-f0-9]{64}", str(doc["capture_sha256"]))), "hash da captura revisada inválido")
        doc_ids.add(doc["id"])
    photos = episode.get("context_photos") or []
    require(isinstance(photos, list), "imagens contextuais precisam ser uma lista")
    photo_ids = set()
    for photo in photos:
        require(photo.get("type") == "photo", "imagem contextual precisa ser photo")
        require(photo.get("id") and photo["id"] not in photo_ids, "imagem duplicada")
        photo_ids.add(photo["id"])
        basis = photo.get("rights_basis", "licensed" if photo.get("license") else "")
        require(basis in ("licensed", "contextual_quotation"),
                "uso de foto exige licença ou justificativa específica de citação")
        if basis == "licensed":
            require(bool(photo.get("license")) and photo.get("license") not in ("Google Images", "unknown", "all rights reserved"),
                    "licença de imagem não revisada")
        if basis == "contextual_quotation":
            require(photo.get("commentary_target") is True
                    and len(str(photo.get("quotation_justification", "")).strip()) >= 45,
                    "foto sem licença só pode ser mostrada se for alvo de crítica/citação necessária")
        require(photo.get("image_url", "").startswith("https://") and photo.get("source_page_url", "").startswith("https://"),
                "imagem precisa de origem comprovada e URL HTTPS")
        require(len(photo.get("attribution", "")) > 15 and len(photo.get("rights_review", "")) > 25,
                "falta crédito ou avaliação de direitos de imagem")
        require(photo.get("archival") is True and len(photo.get("subject", "")) > 20,
                "foto deve ser identificada como arquivo/contexto, nunca notícia atual")
        require(photo.get("needs_cutout") is False, "fotos de contexto não podem perder o fundo")
    segments = episode.get("segments") or []
    require(4 <= len(segments) <= 9, "uma notícia exige 4 a 9 blocos narrativos")
    require(sum(s.get("type") == "opinion" for s in segments) >= 1, "falta opinião claramente identificada")
    require(sum(s.get("type") == "fact" for s in segments) >= 2, "poucos blocos factuais")
    used_docs = set()
    used_photos = set()
    for segment in segments:
        require(len(str(segment.get("narration", "")).split()) >= 32, "bloco narrativo curto demais")
        cards = segment.get("visual_cards") or []
        require(3 <= len(cards) <= 8 and all(6 <= len(c) <= 65 for c in cards), "faltam destaques sincronizados")
        require(segment.get("object_type") in ("data", "store", "cash", "bank", "package", "truck", "factory"), "objeto gráfico inválido")
        if segment.get("document_id") or segment.get("photo_id"):
            require(segment.get("media_side", "left") in ("left", "right"),
                    "posicionamento da matéria deve ser left ou right")
        require(not (segment.get("document_id") and segment.get("photo_id")),
                "imagem e documento não podem disputar o mesmo quadro de prova")
        if segment.get("photo_id"):
            require(segment["photo_id"] in photo_ids, "fotografia não encontrada no manifesto")
            used_photos.add(segment["photo_id"])
        if segment.get("document_id"):
            require(segment["document_id"] in doc_ids, "recorte documental não encontrado")
            used_docs.add(segment["document_id"])
        cues = segment.get("visual_cues")
        if cues is not None:
            require(isinstance(cues, list) and 1 <= len(cues) <= 12, "cues autorais inválidas")
            positions = []
            normalized_narration = normalize_text(segment["narration"])
            for cue in cues:
                anchor = cue.get("anchor", "")
                require(isinstance(anchor, str) and 5 <= len(anchor) <= 160
                        and segment["narration"].count(anchor) == 1, "cue deve ser trecho literal único da fala")
                normalized_anchor = normalize_text(anchor)
                require(normalized_narration.count(normalized_anchor) == 1,
                        "cue deve continuar única após normalização de caixa, acentos e espaços usada na sincronia")
                positions.append(normalized_narration.index(normalized_anchor))
                if cue.get("view") or cue.get("mark_ids"):
                    doc = next((d for d in documentary if d["id"] == segment.get("document_id")), {})
                    require(bool(doc.get("capture_sha256")), "zoom/grifo autoral exige captura autêntica revisada e fixada por hash")
            require(positions == sorted(set(positions)), "cues precisam acompanhar a ordem da narração")
    require(len(used_docs) >= 2, "as duas evidências documentais precisam aparecer no vídeo")
    # Exibir prova autêntica mesmo quando a pauta é exclusiva de uma fonte.
    doc_source = {item["id"]: item["source_id"] for item in documentary}
    source_host = {item["id"]: urlparse(item["url"]).hostname.lower().removeprefix("www.") for item in sources}
    if source_mode == "single_source_attributed":
        excerpts = [d["expected_text"].strip().casefold() for d in documentary
                    if d["id"] in used_docs]
        require(len(set(excerpts)) >= 2,
                "fonte única exige dois trechos documentais diferentes, sem simular duas matérias")
    else:
        require(len({source_host[doc_source[doc_id]] for doc_id in used_docs}) >= 2,
                "mostrar pelo menos duas matérias de publicadores independentes")
    require(len(used_photos | used_docs) >= len(segments) - 2,
            "noticiário não pode ser quase todo texto e ícones; inclua prints comentados")
    return episode


def build_stage(segment: dict) -> dict:
    """Real evidence fills the frame; Roberto's opinion stays on the same visual.

    Narration and commentary are audio-first, not isolated title slides.
    Every newsroom segment must resolve to a verified visual asset.
    """
    document_id = segment.get("document_id")
    photo_id = segment.get("photo_id")
    require(bool(document_id) != bool(photo_id),
            "cena jornalística deve exibir uma matéria ou uma imagem identificada")
    if document_id:
        evidence = {
            "id": "evidence", "kind": "source_excerpt",
            "label": "RECORTE DOCUMENTAL", "asset_id": document_id,
            "x": 0, "y": 0, "width": 100, "height": 100,
            "surface": "none", "image_fit": "contain",
            "visual_role": "protagonist",
            "annotations": segment.get("annotations", []),
            **({"document_context_seconds": segment["document_context_seconds"]}
               if "document_context_seconds" in segment else {}),
        }
    else:
        evidence = {
            "id": "evidence", "kind": "photo",
            "label": segment.get("photo_subject", "FOTOGRAFIA DOCUMENTAL"),
            "asset_id": photo_id,
            "x": 0, "y": 0, "width": 100, "height": 100,
            "surface": "none", "image_fit": "cover",
            "image_motion": "none", "photo_style": "clean",
            "visual_role": "protagonist",
        }
    return {
        "show_title": False, "full_bleed_news": True,
        "motion_profile": "narrative", "camera_mode": "manual",
        "initial_camera": {"x": 50, "y": 50, "zoom": 1},
        "captions": {"enabled": False},
        "elements": [evidence], "connections": [],
    }


def build_scene(index: int, segment: dict) -> dict:
    narration = segment["narration"]
    available_cues = anchors(narration)
    cards = segment["visual_cards"]
    authored_cues = segment.get("visual_cues")
    if authored_cues:
        return {
            "id": f"scene-{index:02d}", "index": index, "title": segment["title"],
            "editorial_role": segment["type"], "narration": narration, "claim_ids": [],
            "tts": {"delivery": "explain", "pause_ms": 120, "cues": []},
            "visual": {"type": "authored_stage", "transition": "cut", "stage": build_stage(segment),
                "beats": [{"anchor": cue["anchor"], "target_id": "evidence", "action": "focus",
                           "headline": cue.get("headline", cards[cue_index % len(cards)]),
                           "treatment": "spotlight", "behavior": "hold", "motion_seconds": .7,
                           **({"view": cue["view"]} if cue.get("view") else {}),
                           **({"mark_ids": cue["mark_ids"]} if "mark_ids" in cue else {})}
                          for cue_index, cue in enumerate(authored_cues)]},
        }
    # No unanchored text cards on top of material. Authored focus regions and
    # marks are optional: if none are reviewed, keep the evidence stable.
    cue_count = min(4, len(cards), len(available_cues))
    cue_indices = [round(i * (len(available_cues) - 1) / (cue_count - 1)) for i in range(cue_count)]
    beats = []
    for i, cue_index in enumerate(cue_indices):
        beat = {
            "anchor": available_cues[cue_index], "target_id": "evidence",
            "action": "focus", "headline": cards[i],
            "treatment": "spotlight", "behavior": "hold",
            "motion_seconds": .6,
        }
        # Never invent crop/mark coordinates. If the editor verified them on
        # the actual capture, the Remotion evidence engine can animate them.
        focus_views = segment.get("focus_views") or []
        mark_sequences = segment.get("mark_sequences") or []
        if i < len(focus_views):
            require(segment.get("document_id"), "zoom de trecho exige documento")
            beat["view"] = focus_views[i]
        if i < len(mark_sequences):
            require(segment.get("document_id"), "grifo exige documento")
            beat["mark_ids"] = mark_sequences[i]
        beats.append(beat)
    normalized_narration = normalize_text(narration)
    for beat in beats:
        require(normalized_narration.count(normalize_text(beat["anchor"])) == 1,
                "cue automática ambígua após normalização usada na sincronia")
    return {
        "id": f"scene-{index:02d}", "index": index, "title": segment["title"],
        "editorial_role": segment["type"],
        "narration": narration, "claim_ids": [],
        "tts": {"delivery": "explain", "pause_ms": 120, "cues": []},
        "visual": {
            "type": "authored_stage", "transition": "cut",
            "stage": build_stage(segment), "beats": beats,
        },
    }



def transform(episode: dict) -> dict:
    episode = validate(episode)
    # Freeze the cutover against the episode's factual review, never wall clock.
    # Historical resumes retain identical projects and voice/thumbnail hashes.
    reviewed = datetime.fromisoformat(episode["reviewed_at"].replace("Z", "+00:00"))
    if reviewed.tzinfo is None:
        reviewed = reviewed.replace(tzinfo=timezone.utc)
    contextual = reviewed >= datetime(2026, 10, 11, 5, tzinfo=timezone.utc)
    docs = [{
        "id": doc["id"], "type": "source_excerpt", "source_page_url": doc["source_page_url"],
        "expected_text": doc["expected_text"], "capture_file": doc["capture_file"],
        "attribution": doc["attribution"], "needs_cutout": False,
        "source_id": doc["source_id"],
        **({"editorial_reconstruction": doc["editorial_reconstruction"]}
           if doc.get("editorial_reconstruction") else {}),
        **({"capture_sha256": doc["capture_sha256"]} if doc.get("capture_sha256") else {}),
        **({"capture_scope": "desktop_context"} if contextual else {}),
        "narrative_role": "documentary_proof", "country_context": "BR",
    } for doc in episode["documentary_evidence"]]
    photo_assets = [{
        "id": photo["id"], "type": "photo",
        "image_url": photo["image_url"],
        "source_page_url": photo["source_page_url"],
        "subject": photo["subject"], "narrative_role": photo["role"],
        "license": photo.get("license"),
        "attribution": photo["attribution"],
        "rights_basis": photo.get("rights_basis", "licensed" if photo.get("license") else "contextual_quotation"),
        "image_fallback_urls": photo.get("image_fallback_urls", []),
        "needs_cutout": False, "country_context": "BR",
    } for photo in episode["context_photos"]]
    contract = {
        "version": "1.0",
        "exact_headline": episode["thumbnail_headline"],
        "primary_subject": episode["thumbnail_primary"],
        "secondary_subject": None,
        "composition": episode.get("thumbnail_composition") or "Composição noticiosa singular com protagonista verificável, amarelo e carvão.",
        "visual_tension": episode["thumbnail_tension"],
        "forbidden_elements": episode.get("thumbnail_forbidden_elements") or [
            "dados ou documentos inventados", "cópias de capas de terceiros",
            "foto apresentada como evidência de um evento diferente", "logotipo inventado",
            "texto extra", "marca d'água",
        ],
        "palette": {"base": "#090B0D", "accent": "#FFBD19", "text": "#F6F7F8"},
        "format": {"width": 1280, "height": 720}, "no_extra_text": True,
    }
    from presenter_identity import news_presenter_contract
    portrait = news_presenter_contract(episode["news_date"], reviewed_at=episode.get("reviewed_at"),
                                       expression=episode.get("thumbnail_presenter_expression"),
                                       variant_key=episode["episode_id"])
    if portrait:
        contract["presenter_identity"] = portrait
        contract["secondary_subject"] = "Roberto, apresentador virtual do canal; reutilizar o retrato oficial sem recriar o rosto"
        contract["composition"] += "; retrato oficial do Roberto em apoio à notícia, com rosto inteiro e texto separados"
    return {
        "version": "1.0", "project_id": episode["episode_id"], "title": episode["title"],
        "presenter": {"name": "Roberto", "gender": "male"},
        "speech": {"pronunciations": episode.get("pronunciations", {}), "ignore_pronunciation_terms": []},
        "story": {"subject": episode.get("story_subject") or episode["title"],
                  "angle": episode.get("story_angle") or episode["discovery_strategy"]["recommendation_angle"],
                  "promise": episode["discovery_strategy"]["promise_proof"],
                  "category": "finance"},
        "sources": episode["sources"],
        "claims": [],
        "visual_assets": docs + photo_assets,
        "visual_direction": {"concept": "Noticiário factual com recortes documentais e análise editorial",
                             "world": "market", "secondary_color": "#FFBD19"},
        "editorial": {
            "format": "ode-news-single", "date": episode["news_date"],
            "editorial_status": episode["editorial_status"],
            "scorecard": episode["scorecard"],
            "discovery_strategy": episode["discovery_strategy"],
            **({"news_selection": episode["news_selection"]} if "news_selection" in episode else {}),
            "youtube_suitability": {"risk_level": "low", "title_thumbnail_safe": True},
        },
        "packaging": {
            "titles": [{"id": "approved", "text": episode["title"]}],
            "title_alternatives": episode["title_options"],
            "strategy": {
                "viewer_intent": episode["discovery_strategy"]["viewer_intent"],
                "recommendation_angle": episode["discovery_strategy"]["recommendation_angle"],
                "promise_proof": episode["discovery_strategy"]["promise_proof"],
                "thumbnail_complement": episode["discovery_strategy"]["thumbnail_complement"],
                "audience_hypothesis": episode["discovery_strategy"]["audience_hypothesis"],
                "verification_limits": episode["discovery_strategy"]["verification_limits"],
            },
            "thumbnails": [{"id": "approved", "headline": episode["thumbnail_headline"],
                            **({"concept": episode["thumbnail_primary"] + " " + episode["thumbnail_tension"]}
                               if contextual else {}),
                            "contract": contract}],
        },
        "publication": {
            "description": episode["publication_description"],
            "seo": {"primary_keyword": episode["primary_keyword"],
                    "secondary_keywords": episode.get("secondary_keywords", []),
                    "viewer_search_query": episode["discovery_strategy"]["search_query"]},
            "tags": episode["tags"],
            "engagement_question": episode["engagement_question"],
            "hashtags": episode["hashtags"],
        },
        "scenes": [
            build_scene(i, {
                **seg,
                **({"document_context_seconds": 1.6} if contextual else {}),
                **({
                    "document_id" if episode["segments"][i-1].get("document_id") else "photo_id":
                    episode["segments"][i-1].get("document_id")
                    or episode["segments"][i-1]["photo_id"]
                } if seg["type"] == "opinion" and i > 0
                    and not seg.get("document_id") and not seg.get("photo_id")
                    and (episode["segments"][i-1].get("document_id")
                         or episode["segments"][i-1].get("photo_id")) else {}),
            })
            for i, seg in enumerate(episode["segments"])
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    episode = json.loads(Path(args.input).read_text(encoding="utf-8"))
    project = transform(episode)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"NEWS_SINGLE_OK: {project['project_id']} {len(project['scenes'])} scenes; "
          f"{len(project['visual_assets'])} documentary excerpts, Roberto/Charon")


if __name__ == "__main__":
    main()
