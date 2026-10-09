"""Sourced, visibly labeled editorial reconstruction of an inaccessible news excerpt."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import re

from PIL import Image, ImageDraw, ImageFont

INK = "#171A1E"
GOLD = "#FFBD19"
PAPER = "#F6F5F0"


def _font(bold: bool, size: int):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for base in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation2"):
        path = Path(base) / name
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    raise RuntimeError("Fonte editorial indisponível")


def _wrap(draw, text, font, width):
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = (current + " " + word).strip()
            if draw.textbbox((0, 0), candidate, font=font)[2] <= width:
                current = candidate
            else:
                if not current:
                    raise RuntimeError("Palavra excede a largura do layout")
                lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def _fit(draw, text, width, max_height, bold, initial_size, minimum_size, leading):
    for size in range(initial_size, minimum_size - 1, -2):
        font = _font(bold, size)
        lines = _wrap(draw, text, font, width)
        step = int(size * leading)
        if len(lines) * step <= max_height:
            return font, lines, step
    raise RuntimeError("Resumo longo demais; revisão editorial obrigatória")


def render_reconstruction(asset: dict, captures_dir: Path, reason: str) -> Path:
    rec = asset.get("editorial_reconstruction")
    if not isinstance(rec, dict):
        raise RuntimeError("Reconstrução sem autorização editorial prévia")
    for field in ("headline", "context", "publisher", "published_at"):
        if not isinstance(rec.get(field), str) or not rec[field].strip():
            raise RuntimeError(f"Reconstrução sem {field}")
    if len(rec["headline"]) > 180 or len(rec["context"]) > 420:
        raise RuntimeError("Reconstrução não pode reproduzir reportagem inteira")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", rec["published_at"]):
        raise RuntimeError("Data da matéria inválida")
    if not str(asset.get("source_page_url", "")).startswith("https://"):
        raise RuntimeError("Reconstrução sem origem verificável")
    dest = (captures_dir / Path(asset["capture_file"]).name).resolve()
    if not dest.is_relative_to(captures_dir.resolve()):
        raise RuntimeError("Destino fora da pasta autorizada")
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Um quadro editorial do próprio canal, não um fac-símile do portal.
    # A proveniência e o motivo de fallback continuam no JSON adjacente.
    im = Image.new("RGB", (1920, 1080), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1920, 12), fill=GOLD)
    d.rectangle((115, 134, 252, 142), fill=GOLD)
    d.text((115, 79), "O DINHEIRO EXPLICA", font=_font(True, 25), fill="#736B62")

    font, lines, line_height = _fit(d, rec["headline"], 1660, 455, True, 108, 64, 1.19)
    y = 192
    for line in lines:
        d.text((115, y), line, font=font, fill=INK)
        y += line_height

    d.rectangle((115, 706, 1805, 709), fill="#D2CEC5")
    font, lines, line_height = _fit(d, rec["context"], 1620, 220, False, 47, 31, 1.32)
    y = 751
    for line in lines:
        d.text((115, y), line, font=font, fill="#34383C")
        y += line_height

    # Crédito discreto sobre o mesmo fundo, sem cabeçalho ou tarja de aviso.
    # Um título editorial nunca deve ser estilizado como recorte original do jornal.
    credit = f"Fonte: {rec['publisher']}  •  {rec['published_at']}"
    credit_font, credit_lines, _ = _fit(d, credit, 1660, 43, False, 27, 19, 1.1)
    d.text((115, 1017), credit_lines[0], font=credit_font, fill="#68635C")
    im.save(dest, "PNG", optimize=True)
    provenance = {
        "kind": "editorial_reconstruction",
        "not_original_screenshot": True,
        "source_page_url": asset["source_page_url"],
        "source_id": asset.get("source_id"),
        "source_publisher": rec["publisher"],
        "published_at": rec["published_at"],
        "editorial_headline": rec["headline"],
        "capture_error": reason[:900],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    dest.with_suffix(".provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[news_reconstruction] Material reconstruído e identificado: {dest.name}")
    return dest
