"""Upload Gemini Live voice-test files to a dedicated Drive folder."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from drive import uploader_from_env


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    uploader = uploader_from_env()
    if uploader is None:
        raise RuntimeError("Google Drive não configurado.")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    folder_id = uploader.create_folder(f"voice-test_gemini-3.8-live_charon_{stamp}")

    files = {}
    for path in sorted(input_dir.iterdir()):
        if not path.is_file():
            continue
        file_id = uploader.upload(path, path.name, folder_id=folder_id)
        files[path.name] = {
            "file_id": file_id,
            "web_view_url": f"https://drive.google.com/file/d/{file_id}/view",
        }

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
