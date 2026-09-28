import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from drive import uploader_from_env


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    uploader = uploader_from_env()
    if uploader is None:
        raise RuntimeError("Google Drive não configurado.")

    input_dir = Path(args.input_dir)
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    root_id = uploader.create_folder(f"teste-vozes_odinheiroexplica_{stamp}")
    male_id = uploader.create_folder("Masculinas", parent_id=root_id)
    female_id = uploader.create_folder("Femininas", parent_id=root_id)

    uploaded = []
    for item in manifest["voices"]:
        if item.get("status") != "ok":
            continue
        file_path = input_dir / item["file"]
        target = male_id if item["gender"] == "masculina" else female_id
        file_id = uploader.upload(file_path, file_path.name, folder_id=target)
        uploaded.append({
            "id": item["id"],
            "label": item["label"],
            "gender": item["gender"],
            "file_id": file_id,
            "url": f"https://drive.google.com/file/d/{file_id}/view",
        })

    readme = input_dir / "LEIA-ME.txt"
    readme_id = uploader.upload(readme, readme.name, folder_id=root_id)

    payload = {
        "folder_id": root_id,
        "folder_url": f"https://drive.google.com/drive/folders/{root_id}",
        "readme_url": f"https://drive.google.com/file/d/{readme_id}/view",
        "voices": uploaded,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
