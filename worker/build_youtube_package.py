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
    if not title.strip() or len(title) > 100:
        raise RuntimeError("Título precisa ter entre 1 e 100 caracteres.")

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
    source_text = "\n".join(
        f"- {source.get('title', 'Fonte')}"
        for source in sources
    )

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

    visual_credit_text = "\n".join(visual_credit_lines)

    publication = project.get("publication", {})
    description = publication.get("description", "").strip()
    seo = publication.get("seo", {})
    tags = publication.get("tags", [])

    if not description:
        raise RuntimeError("Descrição editorial ausente.")
    if not seo.get("primary_keyword"):
        raise RuntimeError("SEO sem palavra-chave principal.")

    if not engagement_question or not engagement_question.endswith("?"):
        raise RuntimeError("Pergunta de engajamento ausente ou inválida.")
    if len(hashtags) != 3 or any(not re.fullmatch(r"#[^\\s#]+", item) for item in hashtags):
        raise RuntimeError("A publicação precisa de exatamente 3 hashtags válidas.")

    full_description = compose_description(
        description,
        chapter_text,
        source_text,
        visual_credit_text,
        engagement_question,
        hashtags,
    )
    # Public descriptions are link-free; research URLs remain in the project.
    if re.search(r"https?://|www\.|\[[^\]]+\]\([^)]+\)", full_description, re.IGNORECASE):
        raise RuntimeError("Descrição não pode conter links. Mantenha URLs somente nos registros internos e escolha imagens com crédito textual compatível.")
    if len(full_description) > 5000:
        raise RuntimeError("Descrição final excede 5.000 caracteres. Encurte a redação sem remover fontes ou créditos obrigatórios.")

    payload = {
        "title": title,
        "thumbnail_headline": thumbnail,
        "packaging_strategy": project.get("packaging", {}).get("strategy", {}),
        "youtube_suitability": project.get("editorial", {}).get("youtube_suitability", {}),
        "seo": seo,
        "tags": tags,
        "description": full_description,
        "chapters": chapters,
        "duration_seconds": round(
            render_input["duration_in_frames"] / render_input["fps"], 2
        ),
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
