import argparse
import json
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

    chapters = []
    for scene in render_input.get("scenes", []):
        seconds = int(scene["start_frame"] / render_input["fps"])
        chapters.append(
            {
                "time": timestamp(seconds),
                "title": scene.get("title") or f"Parte {scene['scene_index'] + 1}",
            }
        )

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
        source_page_url = str(asset.get("source_page_url") or "").strip()
        license_name = str(asset.get("license") or "").strip()
        if attribution:
            line = f"- {attribution}"
            if license_name:
                line += f" — {license_name}"
            if source_page_url:
                line += f" — {source_page_url}"
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

    full_description = (
        f"{description}\n\nCAPÍTULOS\n{chapter_text}"
        f"\n\nBases do vídeo:\n{source_text}"
    )
    if visual_credit_text:
        full_description += f"\n\nCréditos visuais:\n{visual_credit_text}"

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
