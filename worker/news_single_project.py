"""Single-story newsroom adapter: fact-checked topical news -> canonical Remotion + Gemini Live.

No fabricated articles/images/trends. Scene transitions carry sourced B-roll captures
and a transparent right-of-center opinion segment by Roberto.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from news_project import anchors, require


def validate(episode: dict, today: date | None = None) -> dict:
    today = today or date.today()
    require(episode.get("format") == "ode-news-single", "formato deve conter uma matéria por vídeo")
    ep_id = str(episode.get("episode_id") or "")
    require(bool(re.fullmatch(r"noticia-\d{4}-\d{2}-\d{2}-[a-z0-9-]+", ep_id)), "ID do episódio inválido")
    news_day = date.fromisoformat(episode["news_date"])
    require(ep_id.startswith("noticia-" + news_day.isoformat() + "-"), "ID e data divergem")
    require(news_day <= today + timedelta(days=1), "episódio de notícia futura")
    require(episode.get("editorial_status") == "approved_for_private_pilot", "roteiro ainda não aprovado")
    require(bool(episode.get("reviewed_at")), "sem data da revisão editorial")
    require(20 <= len(str(episode.get("title", ""))) <= 100, "título inválido")
    require(8 <= len(str(episode.get("thumbnail_headline", ""))) <= 34, "headline da capa inválida")
    require(len(episode.get("title_options", [])) >= 3, "comparar pelo menos três alternativas de título")
    require(episode.get("scorecard", {}).get("method") and episode["scorecard"].get("reason"), "avaliação de potencial ausente")
    require(episode.get("engagement_question", "").endswith("?"), "pergunta final inválida")
    sources = episode.get("sources") or []
    require(len(sources) >= 2, "apuração precisa de ao menos 2 fontes")
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
    require(len(hosts) >= 2, "fontes precisam incluir publicadores diferentes")
    claims = episode.get("verified_facts") or []
    require(len(claims) >= 4, "menos de quatro fatos apurados")
    for claim in claims:
        require(claim.get("source_ids") and set(claim["source_ids"]) <= source_ids, "fato sem fonte identificável")
        require(claim.get("status") in ("statement", "background", "forecast_not_collected", "projection", "confirmed"), "tipo factual desconhecido")
    documentary = episode.get("documentary_evidence") or []
    require(len(documentary) >= 2, "exigir pelo menos duas referências visuais documentais")
    doc_ids = set()
    for doc in documentary:
        require(doc.get("kind") == "source_excerpt", "imagem deve ser captura de evidência identificada")
        require(doc.get("source_id") in source_ids, "evidência sem fonte")
        require(len(doc.get("expected_text", "")) >= 8, "falta texto verificável na matéria")
        require(doc.get("source_page_url", "").startswith("https://"), "origem visual não comprovada")
        require(len(doc.get("attribution", "")) >= 15 and doc.get("rights_review"), "falta procedência/direitos visuais")
        require(doc.get("capture_file", "").startswith("research/captures/"), "caminho de captura inválido")
        require(doc["id"] not in doc_ids, "asset duplicado")
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
        require(len(str(segment.get("narration", "")).split()) >= 47, "bloco narrativo curto demais")
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
    require(len(used_docs) >= 2, "as duas evidências documentais precisam aparecer no vídeo")
    # Mais de uma matéria visual sobre O MESMO assunto, com fontes diferentes.
    doc_source = {item["id"]: item["source_id"] for item in documentary}
    source_host = {item["id"]: urlparse(item["url"]).hostname.lower().removeprefix("www.") for item in sources}
    require(len({source_host[doc_source[doc_id]] for doc_id in used_docs}) >= 2,
            "mostrar pelo menos duas matérias de publicadores independentes")
    require(len(used_photos | used_docs) >= len(segments) - 2,
            "noticiário não pode ser quase todo texto e ícones; inclua prints comentados")
    return episode


def build_stage(segment: dict) -> dict:
    # Comentário do apresentador precisa ser visualmente diferente de uma
    # matéria/documento: palco aberto, ideia dominante, sem ícone genérico.
    if segment["type"] == "opinion":
        return {
            "show_title": False, "motion_profile": "narrative", "camera_mode": "manual",
            "initial_camera": {"x": 50, "y": 50, "zoom": 1},
            "captions": {"enabled": True, "max_words": 6, "words_per_line": 3,
                         "max_lines": 2, "font_size": 64, "min_free_area_ratio": .30},
            "elements": [
                {"id": "section", "kind": "label", "label": "ANÁLISE DO ROBERTO",
                 "x": 6, "y": 6, "width": 88, "height": 13,
                 "label_size": 44, "surface": "none"},
                {"id": "headline", "kind": "label", "label": segment["headline"],
                 "x": 6, "y": 24, "width": 88, "height": 44,
                 "label_size": 76, "surface": "none"},
                {"id": "metric", "kind": "label", "label": segment["metric"],
                 "x": 6, "y": 78, "width": 85, "height": 14,
                 "label_size": 48, "surface": "none"},
            ], "connections": [],
        }
    label = ("OPINIÃO DO ROBERTO" if segment["type"] == "opinion" else segment["label"])
    has_media = bool(segment.get("document_id") or segment.get("photo_id"))
    media_right = has_media and segment.get("media_side", "left") == "right"
    media_x = 36 if media_right else 4
    text_x = 4 if media_right else 67
    # Referência editorial de noticiário: mídia documental protagonista (~60%)
    # e lateral de narração com frases curtas sincronizadas no lugar do rosto do
    # comentarista. NÃO usar legenda sobre prova/manchete.
    card = {
        "id": "headline", "kind": "label", "label": segment["headline"],
        "x": text_x if has_media else 6, "y": 24, "width": 30 if has_media else 53,
        "height": 39, "label_size": 54 if has_media else 66,
        "surface": "none",
    }
    doc = {
        "id": "document", "kind": "source_excerpt", "label": "TRECHO DA MATÉRIA",
        "asset_id": segment["document_id"], "x": media_x, "y": 18, "width": 60,
        "height": 66, "surface": "none", "image_fit": "contain",
        "visual_role": "support",
    } if segment.get("document_id") else {
        "id": "photo-context", "kind": "photo",
        "label": "IMAGEM DE ARQUIVO", "asset_id": segment["photo_id"],
        "x": media_x, "y": 18, "width": 60, "height": 66,
        "surface": "none", "image_fit": "cover", "image_motion": "none",
        "photo_style": "clean", "visual_role": "support",
    } if segment.get("photo_id") else {
        "id": "subject", "kind": "object", "label": segment["headline"],
        "object_type": segment["object_type"], "x": 61, "y": 24, "width": 36,
        "height": 56, "show_label": False, "surface": "none", "svg_motion": "assemble",
        "sustain": {"kind": "breathe", "amplitude": 13, "period_seconds": 6},
    }
    return {
        "show_title": False, "motion_profile": "narrative", "camera_mode": "manual",
        "initial_camera": {"x": 50, "y": 50, "zoom": 1},
        # A headline lateral atualizada pelos beats cumpre o papel de legenda
        # editorial sem cobrir prints. Closed captions continuam disponíveis no
        # player do YouTube; sobreposição automática só em cenas sem mídia.
        "captions": {"enabled": not has_media, "max_words": 6, "words_per_line": 3,
                     "max_lines": 2, "font_size": 64, "min_free_area_ratio": .30},
        "elements": [
            {"id": "section", "kind": "label", "label": label[:78],
             "x": 6, "y": 5, "width": 85, "height": 13, "label_size": 40, "surface": "none"},
            card, doc,
            {"id": "metric", "kind": "label", "label": segment["metric"][:78],
             "x": text_x if has_media else 6, "y": 73, "width": 30 if has_media else 51,
             "height": 15, "label_size": 43 if has_media else 51, "surface": "none"},
        ],
        "connections": [],
    }


def build_scene(index: int, segment: dict) -> dict:
    narration = segment["narration"]
    available_cues = anchors(narration)
    cards = segment["visual_cards"]
    # Notícias não usam a cadência de animações dos vídeos explicativos:
    # 3 a 4 atualizações legíveis por bloco, enquanto a matéria fica na tela.
    cue_count = min(4, len(cards), len(available_cues))
    cue_indices = [round(i * (len(available_cues) - 1) / (cue_count - 1)) for i in range(cue_count)]
    beats = []
    for i, cue_index in enumerate(cue_indices):
        beats.append({
            "anchor": available_cues[cue_index], "target_id": "headline",
            "action": "update", "headline": cards[i],
            "treatment": "kinetic_type", "behavior": "transform",
            "motion_seconds": .5,
        })
    return {
        "id": f"scene-{index:02d}", "index": index, "title": segment["title"],
        "narration": narration, "claim_ids": [],
        "tts": {"delivery": "explain", "pause_ms": 120, "cues": []},
        "visual": {
            "type": "authored_stage", "transition": "cut",
            "stage": build_stage(segment), "beats": beats,
        },
    }


def transform(episode: dict) -> dict:
    episode = validate(episode)
    docs = [{
        "id": doc["id"], "type": "source_excerpt", "source_page_url": doc["source_page_url"],
        "expected_text": doc["expected_text"], "capture_file": doc["capture_file"],
        "attribution": doc["attribution"], "needs_cutout": False,
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
        "needs_cutout": False, "country_context": "BR",
    } for photo in episode["context_photos"]]
    contract = {
        "version": "1.0",
        "exact_headline": episode["thumbnail_headline"],
        "primary_subject": episode["thumbnail_primary"],
        "secondary_subject": None,
        "composition": "Notícia única, contraste muito alto, protagonista real, leitura imediata no celular, amarelo e carvão.",
        "visual_tension": episode["thumbnail_tension"],
        "forbidden_elements": [
            "valor de tributo já definido sem fonte", "cópias de capas de terceiros",
            "foto apresentada como evidência de um evento diferente", "logotipo partidário inventado",
            "texto extra", "marca d'água",
        ],
        "palette": {"base": "#090B0D", "accent": "#FFBD19", "text": "#F6F7F8"},
        "format": {"width": 1280, "height": 720}, "no_extra_text": True,
    }
    return {
        "version": "1.0", "project_id": episode["episode_id"], "title": episode["title"],
        "presenter": {"name": "Roberto", "gender": "male"},
        "speech": {"pronunciations": episode.get("pronunciations", {}), "ignore_pronunciation_terms": []},
        "story": {"subject": "Notícia única: Imposto Seletivo depois das eleições",
                  "angle": "Momento político do anúncio, projeção fiscal e transparência",
                  "promise": "Separar o que foi anunciado, o que não foi aprovado e a opinião",
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
            "youtube_suitability": {"risk_level": "low", "title_thumbnail_safe": True},
        },
        "packaging": {
            "titles": [{"id": "approved", "text": episode["title"]}],
            "title_alternatives": episode["title_options"],
            "thumbnails": [{"id": "approved", "headline": episode["thumbnail_headline"],
                            "contract": contract}],
        },
        "publication": {
            "description": (
                "O ministro da Fazenda anunciou o envio da proposta de alíquotas do Imposto Seletivo "
                "para depois do segundo turno das eleições. Entenda a diferença entre anúncio e cobrança, "
                "quais produtos podem entrar nas regras, o que significam as estimativas de arrecadação "
                "e a leitura crítica do Roberto sobre o calendário político. Os valores mencionados são "
                "projeções ou planos, não cobranças implementadas."
            ),
            "seo": {"primary_keyword": episode["primary_keyword"]},
            "tags": episode["tags"],
            "engagement_question": episode["engagement_question"],
            "hashtags": episode["hashtags"],
        },
        "scenes": [build_scene(i, seg) for i, seg in enumerate(episode["segments"])],
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
