import argparse
import io
import json
import mimetypes
import re
import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, ImageOps, ImageStat, UnidentifiedImageError
from rembg import new_session, remove


MAX_BYTES = 20 * 1024 * 1024
CAPTURE_ROOT = Path(__file__).resolve().parents[1] / "research" / "captures"


def validate_excerpt_image(image: Image.Image, asset_id: str) -> None:
    """Rejeita capturas sem conteúdo visual suficiente para servir como evidência."""
    sample = image.copy()
    sample.thumbnail((512, 512))
    sample = sample.convert("RGB")
    pixels = memoryview(sample.tobytes())
    dark_count = sum(
        pixels[index] < 238 or pixels[index + 1] < 238 or pixels[index + 2] < 238
        for index in range(0, len(pixels), 3)
    )
    dark_ratio = dark_count / (sample.width * sample.height)
    contrast = max(ImageStat.Stat(sample).stddev)
    if dark_ratio < 0.012 or contrast < 8:
        raise RuntimeError(
            f"Asset {asset_id}: recorte quase branco ou vazio; revise a URL, o seletor e a área de crop."
        )


def prepare_excerpt(raw: bytes, output_dir: Path, asset: dict) -> tuple[str, dict]:
    try:
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise RuntimeError(f"Asset {asset['id']}: captura não é uma imagem válida.") from exc
    original_width, original_height = image.size
    original_image = image
    original = f"{safe_name(asset['id'])}.source.png"
    region = asset.get("crop") or {"x": 0, "y": 0, "width": 100, "height": 100}
    x, y, w, h = (float(region[k]) for k in ("x", "y", "width", "height"))
    if not (0 <= x < 100 and 0 <= y < 100 and w > 0 and h > 0 and x+w <= 100 and y+h <= 100):
        raise RuntimeError("Recorte fora da captura original.")
    box = (round(x*image.width/100), round(y*image.height/100), round((x+w)*image.width/100), round((y+h)*image.height/100))
    image = image.crop(box)
    if min(image.size) < 100:
        raise RuntimeError("Recorte muito pequeno. Capture uma região legível em maior resolução.")
    validate_excerpt_image(image, str(asset["id"]))
    filename = f"{safe_name(asset['id'])}.png"
    original_image.save(output_dir / original)
    image.save(output_dir / filename)
    return filename, {"width": image.width, "height": image.height, "original_width": original_width, "original_height": original_height, "original_file": f"generated-assets/{original}", "crop": region, "sha256": hashlib.sha256(raw).hexdigest(), "source_id": asset.get("source_id"), "captured_at": asset.get("captured_at")}


def safe_name(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-")
    return value or "asset"


def download(url: str, fallback_urls: list[str] | None = None) -> tuple[bytes, str]:
    urls = [url, *(fallback_urls or [])]
    for candidate in urls:
        if urlparse(candidate).scheme != "https":
            raise RuntimeError("Asset visual precisa usar URL https.")

    last_error = "sem resposta"
    for candidate in urls:
        for attempt in range(2):
            try:
                response = requests.get(
                    candidate,
                    headers={
                        "User-Agent": "ODinheiroExplica-VisualAssets/1.1 (https://github.com/Lucascristao/odinheiroexplica)"
                    },
                    timeout=60,
                    allow_redirects=True,
                )
            except requests.RequestException as exc:
                last_error = type(exc).__name__
                if attempt == 0:
                    time.sleep(4)
                    continue
                break

            if response.status_code == 200:
                content = response.content
                if len(content) > MAX_BYTES:
                    raise RuntimeError(f"Asset visual excede {MAX_BYTES // 1024 // 1024} MB.")
                return content, response.headers.get("content-type", "").split(";")[0].strip()

            last_error = f"HTTP {response.status_code}"
            if response.status_code in {429, 500, 502, 503, 504} and attempt == 0:
                retry_after = response.headers.get("Retry-After", "")
                delay = min(int(retry_after), 120) if retry_after.isdigit() else 5
                print(f"Asset visual: {last_error}; aguardando {delay}s antes de tentar novamente.")
                time.sleep(delay)
                continue
            break

    raise RuntimeError(f"Download do asset visual falhou após {len(urls)} URL(s): {last_error}.")


def save_graphic(raw: bytes, content_type: str, output_dir: Path, asset_id: str) -> str:
    extension = mimetypes.guess_extension(content_type) or ".bin"
    if extension == ".jpe":
        extension = ".jpg"

    path = output_dir / f"{safe_name(asset_id)}{extension}"
    path.write_bytes(raw)
    return path.name


def save_photo(
    raw: bytes,
    output_dir: Path,
    asset_id: str,
    needs_cutout: bool,
    session,
) -> str:
    image = Image.open(io.BytesIO(raw)).convert("RGBA")

    if needs_cutout:
        image = remove(image, session=session)

    path = output_dir / f"{safe_name(asset_id)}.png"
    image.save(path, format="PNG", optimize=True)
    return path.name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    project = json.loads(Path(args.project).read_text(encoding="utf-8"))
    assets = project.get("visual_assets") or []

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    session = None
    prepared = []

    for asset in assets:
        asset_id = str(asset["id"])
        asset_type = str(asset.get("type") or "photo_cutout")
        if asset.get("capture_file"):
            capture = (Path(__file__).resolve().parents[1] / asset["capture_file"]).resolve()
            if not capture.is_relative_to(CAPTURE_ROOT.resolve()) or capture.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                raise RuntimeError(f"Asset {asset_id}: captura precisa ser uma imagem em research/captures/.")
            if not capture.is_file():
                raise RuntimeError(f"Asset {asset_id}: capture_file não encontrado: {capture}")
            if capture.stat().st_size > MAX_BYTES:
                raise RuntimeError(f"Asset {asset_id}: captura excede 20 MB.")
            raw, content_type = capture.read_bytes(), mimetypes.guess_type(capture.name)[0]
        else:
            if asset_type == "source_excerpt" and not asset.get("image_url"):
                raise RuntimeError(f"Asset {asset_id}: source_excerpt exige capture_file existente ou image_url HTTPS.")
            raw, content_type = download(
                str(asset["image_url"]), asset.get("image_fallback_urls") or []
            )

        dimensions = {}
        if asset_type == "source_excerpt":
            if asset.get("needs_cutout"):
                raise RuntimeError("Recorte documental não pode remover fundo.")
            filename, dimensions = prepare_excerpt(raw, output_dir, asset)
        elif asset_type == "graphic" and content_type == "image/svg+xml":
            filename = save_graphic(raw, content_type, output_dir, asset_id)
        else:
            needs_cutout = bool(asset.get("needs_cutout", asset_type == "photo_cutout"))
            if needs_cutout and session is None:
                session = new_session("u2netp")
            filename = save_photo(
                raw,
                output_dir,
                asset_id,
                needs_cutout,
                session,
            )

        prepared.append(
            {
                "id": asset_id,
                **dimensions,
                "type": asset_type,
                "subject": asset.get("subject"),
                "narrative_role": asset.get("narrative_role"),
                "country_context": asset.get("country_context"),
                "source_page_url": asset.get("source_page_url"),
                "license": asset.get("license"),
                "attribution": asset.get("attribution"),
                "public_file": f"generated-assets/{filename}",
            }
        )

        print(f"Asset visual pronto: {asset_id} -> {filename}")

    manifest = {
        "project_id": project.get("project_id", "project"),
        "assets": prepared,
    }
    output = Path(args.manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Assets visuais preparados: {len(prepared)}")


if __name__ == "__main__":
    main()
