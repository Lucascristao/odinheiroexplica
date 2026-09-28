import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from drive import uploader_from_env


def safe_name(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._ -]+", "", value).strip()
    return value[:120] or "video"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--thumbnail", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--project-slug", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    uploader = uploader_from_env()
    if uploader is None:
        raise RuntimeError(
            "Google Drive não configurado. Faltam credenciais ou folder ID."
        )

    project_slug = safe_name(args.project_slug)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    folder_name = f"{project_slug}_{stamp}"
    folder_id = uploader.create_folder(folder_name)

    files = {}

    def upload_one(key: str, path: str):
        file_path = Path(path)
        print(f"[Drive] Enviando {file_path.name}...", flush=True)
        file_id = uploader.upload(
            file_path,
            file_path.name,
            folder_id=folder_id,
            progress_cb=lambda p: print(
                f"[Drive] {file_path.name}: {p * 100:.0f}%",
                flush=True,
            ),
        )
        files[key] = {
            "file_id": file_id,
            "name": file_path.name,
            "web_view_url": f"https://drive.google.com/file/d/{file_id}/view",
        }

    upload_one("video", args.video)
    upload_one("thumbnail", args.thumbnail)
    upload_one("metadata", args.metadata)

    payload = {
        "folder_id": folder_id,
        "folder_url": f"https://drive.google.com/drive/folders/{folder_id}",
        "files": files,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
