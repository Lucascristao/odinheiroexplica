"""Generate and visually audit a news thumbnail, without pretending a human reviewed it.

Images are created with the project's existing Gemini API credential. A separate
vision pass observes the actual final pixels; ambiguous inspections fail closed.
"""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
from google import genai
from google.genai import types

from thumbnail_contract import (
    REQUIRED_CHECKS, REQUIRED_OBSERVATIONS, contract_sha256, file_sha256,
    normalized_project_sha256, read_contract, validate_thumbnail_audit,
)

W, H = 1280, 720


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def draw_title(image, text, side):
    """Typeset the exact headline locally: do not trust image-model spelling."""
    canvas = ImageOps.fit(image.convert("RGB"), (W, H), method=Image.Resampling.LANCZOS)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    side = side if side in ("left", "right") else "left"
    x0 = 42 if side == "left" else 645
    # Cinematic edge shading rather than a repeated box/card across thumbnails.
    for x in range(W):
        progress = x / (W - 1)
        strength = (1 - progress) if side == "left" else progress
        alpha = int(165 * max(0, strength) ** 2.1)
        if alpha:
            draw.line((x, 0, x, H), fill=(5, 7, 9, alpha))
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    words = text.strip().split()
    font_size = 91
    for _ in range(65):
        font = ImageFont.truetype(font_path, font_size)
        lines = []
        for word in words:
            if lines and draw.textbbox((0, 0), lines[-1] + " " + word, font=font, stroke_width=0)[2] <= 540:
                lines[-1] += " " + word
            else:
                lines.append(word)
        if len(lines) <= 4 and (len(lines) * int(font_size * 1.23)) <= 455:
            break
        font_size -= 1
    heights = [draw.textbbox((0, 0), item, font=font, stroke_width=0)[3] for item in lines]
    line_step = int(font_size * 1.24)
    y = (H - line_step * len(lines)) // 2 + 12
    for i, line in enumerate(lines):
        color = "#FFBD19" if i == 0 else "#F6F7F8"
        draw.text((x0, y + i * line_step), line, fill=color, font=font,
                  stroke_width=3, stroke_fill="#060607")
    return Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGB")


def generate_image(client, contract, episode):
    side = episode.get("thumbnail_text_side", "left")
    image_side = "right" if side == "left" else "left"
    prompt = f"""Editorial YouTube cover background, 16:9, photo-realistic cinematic storytelling,
subject: {contract['primary_subject']}.
Tension: {contract['visual_tension']}.
Composition hint: {episode.get('thumbnail_composition') or contract['composition']}.
ONE dominant subject on the {image_side}, no secondary crowd of objects,
leave the opposite half visually calm for title added later.
Dark charcoal #090B0D, vivid gold #FFBD19 only as a subtle accent, high contrast,
credible news photography/illustration (do not fabricate documents or people).
ABSOLUTELY NO WORDS, LETTERS, NUMBERS, LOGOS, WATERMARKS, OR TEXT.
Avoid: {'; '.join(contract['forbidden_elements'])}.
Create a distinct composition grounded in this particular news story, not a generic finance template."""
    response = client.models.generate_content(
        model=os.getenv("ODE_NEWS_IMAGE_MODEL", "gemini-3.1-flash-image-preview"),
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="16:9"),
        ),
    )
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            return draw_title(part.as_image(), contract["exact_headline"], side)
    raise RuntimeError("O modelo não devolveu pixels de imagem.")


def documentary_fallback(episode, root, contract):
    """A unique editorial cover from real documentary screenshots, never fake AI evidence.

    Used only if Gemini native image generation is unavailable; actual sources
    have already been captured and verified by the visual-assets pipeline.
    """
    existing = []
    for doc in episode.get("documentary_evidence", []):
        file = root / doc.get("capture_file", "")
        if file.is_file():
            existing.append(file)
    if not existing:
        raise RuntimeError("Sem capturas reais para montar a capa editorial.")
    side = episode.get("thumbnail_text_side", "left")
    on_right = side == "left"
    base = Image.new("RGB", (W, H), "#090B0D")
    with Image.open(existing[0]) as opened:
        full = ImageOps.fit(opened.convert("RGB"), (W, H), method=Image.Resampling.LANCZOS)
    full = ImageEnhance.Color(full).enhance(0.38).filter(ImageFilter.GaussianBlur(18))
    base.paste(Image.blend(full, Image.new("RGB", (W,H), "#090B0D"), 0.68))
    card_w, card_h = 625, 545
    with Image.open(existing[0]) as opened:
        source = ImageOps.fit(opened.convert("RGB"), (card_w, card_h),
                              method=Image.Resampling.LANCZOS, centering=(.5,.18))
    # Preserve actual source pixels without invented layout/headlines.
    frame = Image.new("RGB", (card_w+16,card_h+16), "#F6F7F8")
    frame.paste(source,(8,8))
    angle = -5 if on_right else 5
    tilted=frame.rotate(angle,expand=True,resample=Image.Resampling.BICUBIC)
    shadow=Image.new("RGBA",tilted.size,(0,0,0,0))
    shadow.paste((0,0,0,200),(10,12,tilted.width-8,tilted.height-6))
    shadow=shadow.filter(ImageFilter.GaussianBlur(22))
    x = 645 if on_right else -45
    y = 52
    base.paste(shadow,(x+12,y+17),shadow)
    base.paste(tilted,(x,y))
    accent=ImageDraw.Draw(base)
    edge_x = 640 if on_right else 632
    accent.line([(edge_x, 105),(edge_x, 600)],fill="#FFBD19",width=7)
    return draw_title(base, contract["exact_headline"], side)


def inspect_pixels(client, image_path, contract):
    image_bytes = Path(image_path).read_bytes()
    query = f"""Inspect the ATTACHED ACTUAL FINAL THUMBNAIL PIXELS, not a proposed design.
You are an independent, conservative, automated visual reviewer.
Return ONLY a JSON object with keys checks and observations.
The checks object must have boolean keys {list(REQUIRED_CHECKS)}.
The observations object must have meaningful Portuguese strings for
{list(REQUIRED_OBSERVATIONS)}. Describe the pixels you actually see.
Only mark TRUE if visibly confirmed. For exact lettering verify every accent,
punctuation, word and order against: {contract['exact_headline']!r}.
Primary subject required: {contract['primary_subject']}.
Secondary subject: {contract['secondary_subject']!r} (null means none required).
Forbidden elements: {contract['forbidden_elements']}.
Visual identity: dark charcoal base, #FFBD19 gold accents, warm white text;
readable when reduced to 320x180. No misleading fake data or extra text.
If uncertain, mark false. No invented claim of human viewing."""
    result = client.models.generate_content(
        model=os.getenv("ODE_NEWS_VISION_MODEL", "gemini-3.8-flash"),
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"), query
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    answer = json.loads(result.text)
    checks = answer.get("checks") or {}
    obs = answer.get("observations") or {}
    if set(checks) != set(REQUIRED_CHECKS) or set(obs) != set(REQUIRED_OBSERVATIONS):
        raise ValueError("Revisor automático não preencheu o contrato inteiro.")
    if any(checks[key] is not True for key in REQUIRED_CHECKS):
        raise ValueError("Inspeção visual reprovou pelo menos um critério.")
    if any(not isinstance(obs[key], str) or len(obs[key].strip()) < 15
           for key in REQUIRED_OBSERVATIONS):
        raise ValueError("Revisor não descreveu evidência observada.")
    return checks, obs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--qa", required=True)
    args = parser.parse_args()
    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit("GEMINI_API_KEY ausente; não criar capa fictícia.")
    qa = load_json(args.qa)
    if qa.get("status") != "pass" or qa.get("failures") or qa.get("warnings"):
        raise SystemExit("QA do vídeo não está integralmente aprovado; não criar capa/publicar.")
    project = load_json(args.project)
    episode = load_json(args.episode)
    if episode.get("episode_id") != project.get("project_id"):
        raise SystemExit("Projeto e episódio diferentes.")
    root = Path(args.root).resolve()
    directory = root / "production" / project["project_id"]
    directory.mkdir(parents=True, exist_ok=True)
    contract = read_contract(project, directory)
    thumbnail = directory / "thumbnail.jpg"
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    for attempt in range(3):
        try:
            try:
                picture = generate_image(client, contract, episode)
                generator = "Gemini-native-image"
            except Exception as model_error:
                reason = str(model_error)
                if not any(code in reason for code in ("429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND")):
                    raise
                print("NATIVE_IMAGE_UNAVAILABLE: usando recorte documental real no lugar de mídia inventada.")
                picture = documentary_fallback(episode, root, contract)
                generator = "Verified-documentary-source-collage"
            picture.save(thumbnail, "JPEG", quality=94)
            checks, observations = inspect_pixels(client, thumbnail, contract)
            audit = {
                "version": "1.0", "project_id": project["project_id"],
                "project_sha256": normalized_project_sha256(args.project),
                "contract_sha256": contract_sha256(contract),
                "image_sha256": file_sha256(thumbnail),
                "headline": contract["exact_headline"], "approval_status": "approved",
                "reviewer": "Gemini automated multimodal pixel inspection",
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "checks": checks, "observations": observations,
                "checked_forbidden_elements": contract["forbidden_elements"],
                "observed_forbidden_elements": [],
            }
            (directory / "thumbnail-audit.json").write_text(
                json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            validate_thumbnail_audit(root, project, thumbnail, project_source_path=args.project)
            print(f"THUMBNAIL_AUTONOMOUS_OK:{thumbnail} attempt={attempt + 1} generator={generator}")
            return
        except (ValueError, RuntimeError, KeyError, IndexError) as err:
            print(f"THUMBNAIL_RETRY_{attempt+1}:{type(err).__name__}")
    raise SystemExit("Capa sem revisão visual automática válida; manter o vídeo privado.")


if __name__ == "__main__":
    main()
