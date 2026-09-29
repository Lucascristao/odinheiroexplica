import argparse
import io
import json
import mimetypes
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image
from rembg import new_session, remove


MAX_BYTES = 20 * 1024 * 1024


def safe_name(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-")
    return value or "asset"


def download(url: str) -> tuple[bytes, str]:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise RuntimeError("Asset visual precisa usar URL https.")

    response = requests.get(
        url,
        headers={"User-Agent": "odinheiroexplica-visual-assets/1.0"},
        timeout=60,
        allow_redirects=True,
    )
    response.raise_for_status()
    content = response.content
    if len(content) > MAX_BYTES:
        raise RuntimeError(
            f"Asset visual excede {MAX_BYTES // 1024 // 1024} MB."
        )
    return content, response.headers.get("content-type", "").split(";")[0].strip()


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
        image_url = str(asset["image_url"])
        raw, content_type = download(image_url)

        if asset_type == "graphic" and content_type == "image/svg+xml":
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
