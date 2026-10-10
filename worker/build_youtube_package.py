import argparse
import json
import re
from pathlib import Path


def timestamp(total_seconds: int) -> str:
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def unique_nonempty(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        clean = str(value or "").strip()
        key = clean.casefold()
        if clean and key not in seen:
            seen.add(key)
            result.append(clean)
    return result


def compose_description(
    body: str,
    chapter_text: str,
    source_text: str,
    visual_credit_text: str,
    engagement_question: str,
    hashtags: list[str],
) -> str:
    if re.search(
        r"(?im)^\s*(fontes|bases do vídeo|capítulos|créditos visuais)\s*:?.*$",
        body,
    ):
        raise RuntimeError(
            "publication.description não deve repetir capítulos, fontes ou créditos; "
            "essas seções são montadas pelo pipeline."
        )
    sections = [body.strip()]
    if chapter_text:
        sections.append(f"CAPÍTULOS\n{chapter_text}")
    if source_text:
        sections.append(f"FONTES\n{source_text}")
    if visual_credit_text:
        sections.append(f"Créditos visuais:\n{visual_credit_text}")
    if engagement_question:
        sections.append(engagement_question.strip())
    if hashtags:
        sections.append(" ".join(hashtags))
    return "\n\n".join(section for section in sections if section)


def validate_publication_fields(publication: dict, title: str) -> list[str]:
    """Validate editor inputs before expensive narration or rendering."""
    description = str(publication.get("description") or "").strip()
    seo = publication.get("seo") or {}
    question = str(publication.get("engagement_question") or "").strip()
    raw_hashtags = publication.get("hashtags") or []
    if not isinstance(raw_hashtags, list):
        raise RuntimeError("Hashtags precisam ser uma lista.")
    hashtags = unique_nonempty(raw_hashtags)
    if not title.strip() or len(title) > 100:
        raise RuntimeError("Título precisa ter entre 1 e 100 caracteres.")
    if not description:
        raise RuntimeError("Descrição editorial ausente.")
    if not seo.get("primary_keyword"):
        raise RuntimeError("SEO sem palavra-chave principal.")
    if not question or not question.endswith("?"):
        raise RuntimeError("Pergunta de engajamento ausente ou inválida.")
    if len(hashtags) != len(raw_hashtags):
        raise RuntimeError("Hashtags repetidas ou vazias não são permitidas.")
    if not 1 <= len(hashtags) <= 3 or any(
        not re.fullmatch(r"#[^\s#]+", item) for item in hashtags
    ):
        raise RuntimeError("A publicação precisa de 1 a 3 hashtags válidas.")
    if re.search(r"(?<!\w)#[^\s#]+", description):
        raise RuntimeError("Hashtags devem ficar apenas no campo publication.hashtags.")
    compose_description(description, "", "", "", question, hashtags)
    if re.search(r"https?://|www\.|\[[^\]]+\]\([^)]+\)", description, re.IGNORECASE):
        raise RuntimeError("Descrição não pode conter links; mantenha URLs nas fontes.")
    return hashtags



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--render-input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    project = json.loads(Path(args.project).read_text(encoding="utf-8"))
    render_input = json.loads(Path(args.render_input).read_text(encoding="utf-8"))

    titles = project.get("packaging", {}).get("titles", [])
    thumbs = project.get("packaging", {}).get("thumbnails", [])
    title = titles[0]["text"] if titles else project["story"]["subject"]
    thumbnail = thumbs[0]["headline"] if thumbs else ""
    chapters = []
    duration_seconds = render_input["duration_in_frames"] / render_input["fps"]
    chapter_seconds = []
    for scene in render_input.get("scenes", []):
        seconds = int(scene["start_frame"] / render_input["fps"])
        if chapter_seconds and seconds - chapter_seconds[-1] < 10:
            continue
        chapter_seconds.append(seconds)
        chapters.append(
            {
                "time": timestamp(seconds),
                "title": scene.get("title") or f"Parte {scene['scene_index'] + 1}",
            }
        )

    # YouTube requires 0:00, at least three chapters, and >=10s per chapter.
    if chapters and duration_seconds - chapter_seconds[-1] < 10:
        chapters.pop()
        chapter_seconds.pop()
    if len(chapters) < 3 or chapter_seconds[0] != 0:
        chapters = []

    chapter_text = "\n".join(
        f"{item['time']} {item['title']}" for item in chapters
    )

    sources = project.get("sources", [])
    source_titles = unique_nonempty(
        [
            f"{source['publisher']} — {source.get('title', 'Fonte')}"
            if source.get("publisher")
            else source.get("title", "Fonte")
            for source in sources
        ]
    )
    source_text = "\n".join(f"- {title}" for title in source_titles)

    visual_assets = project.get("visual_assets", [])
    visual_credit_lines = []
    for asset in visual_assets:
        attribution = str(asset.get("attribution") or "").strip()
        license_name = str(asset.get("license") or "").strip()
        if attribution:
            line = f"- {attribution}"
            if license_name:
                line += f" — {license_name}"
            visual_credit_lines.append(line)
    visual_credit_text = "\n".join(unique_nonempty(visual_credit_lines))

    publication = project.get("publication", {})
    description = str(publication.get("description") or "").strip()
    seo = publication.get("seo", {})
    tags = publication.get("tags", [])
    engagement_question = str(publication.get("engagement_question") or "").strip()
    hashtags = unique_nonempty(publication.get("hashtags", []))

    hashtags = validate_publication_fields(publication, title)

    full_description = compose_description(
        description,
        chapter_text,
        source_text,
        visual_credit_text,
        engagement_question,
        hashtags,
    )

    # Public descriptions are link-free; research URLs remain in the project.
    if re.search(
        r"https?://|www\.|\[[^\]]+\]\([^)]+\)",
        full_description,
        re.IGNORECASE,
    ):
        raise RuntimeError(
            "Descrição não pode conter links. Mantenha URLs somente nos registros "
            "internos e escolha imagens com crédito textual compatível."
        )
    if len(full_description) > 5000:
        raise RuntimeError(
            "Descrição final excede 5.000 caracteres. Encurte a redação sem "
            "remover fontes ou créditos obrigatórios."
        )

    payload = {
        "title": title,
        "thumbnail_headline": thumbnail,
        "packaging_strategy": project.get("packaging", {}).get("strategy", {}),
        "youtube_suitability": project.get("editorial", {}).get("youtube_suitability", {}),
        "seo": seo,
        "tags": tags,
        "engagement_question": engagement_question,
        "hashtags": hashtags,
        "description": full_description,
        "chapters": chapters,
        "duration_seconds": round(duration_seconds, 2),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    txt = output.with_suffix(".txt")
    txt.write_text(
        f"TÍTULO\n{title}\n\n"
        f"THUMBNAIL\n{thumbnail}\n\n"
        f"DESCRIÇÃO\n{full_description}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
