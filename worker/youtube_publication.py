"""YouTube delivery for O Dinheiro Explica.

Video delivery is private-first and skips Drive. Scopes: youtube.upload + youtube.readonly.
Video publication/public visibility is NOT implemented with these scopes.
The thumbnail stage uses the canonical image+review audit before upload.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

EXPECTED_ID = "UCd7laspUAiQk0DEF9NQ-itw"
EXPECTED_TITLE = "O Dinheiro Explica"
EXPECTED_HANDLE = "@odinheiro.explica"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def youtube_credentials():
    from google.oauth2.credentials import Credentials
    required = ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
    missing = [key for key in required if not os.getenv(key, "").strip()]
    if missing:
        raise ValueError("Credenciais ausentes: " + ", ".join(missing))
    return Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=SCOPES,
    )


def youtube_service():
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=youtube_credentials(), cache_discovery=False)


def assert_channel(service):
    """Block all writes if OAuth is not the channel confirmed in YouTube Studio."""
    result = service.channels().list(part="id,snippet,contentDetails", mine=True).execute()
    items = result.get("items", [])
    if len(items) != 1:
        raise ValueError("Token não identifica exatamente um canal.")
    channel = items[0]
    title = channel.get("snippet", {}).get("title", "")
    handle = channel.get("snippet", {}).get("customUrl", "")
    if channel.get("id") != EXPECTED_ID or title != EXPECTED_TITLE or handle.casefold() != EXPECTED_HANDLE:
        raise ValueError("Acesso OAuth pertence a outro canal; envio bloqueado.")
    return channel


def validate_package(video: Path, metadata: dict, project_id: str):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,119}", project_id):
        raise ValueError("project-id inválido.")
    if not video.is_file() or video.suffix.lower() != ".mp4" or video.stat().st_size == 0:
        raise ValueError("MP4 de produção ausente ou inválido.")
    title = metadata.get("title", "")
    description = metadata.get("description", "")
    tags = metadata.get("tags", [])
    if not isinstance(title, str) or not 1 <= len(title) <= 100:
        raise ValueError("Título do vídeo inválido.")
    if not isinstance(description, str) or not 1 <= len(description) <= 5000:
        raise ValueError("Descrição do vídeo inválida.")
    if not isinstance(tags, list) or len(tags) > 12 or any(not isinstance(x, str) for x in tags):
        raise ValueError("Tags inválidas.")
    tag = "ODE_EPISODE_" + project_id
    return {
        "snippet": {
            "title": title,
            "description": description,
            "tags": list(dict.fromkeys(tags + [tag])),
            "categoryId": "27",
            "defaultLanguage": "pt-BR",
        },
        "status": {"privacyStatus": "private"},
    }


def lookup_existing(service, channel: dict, episode_tag: str):
    playlist = channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads", "")
    if not playlist:
        raise ValueError("Playlist de envios indisponível; não é seguro testar duplicidade.")
    token = None
    for _ in range(5):
        page = service.playlistItems().list(
            part="contentDetails", playlistId=playlist, maxResults=50, pageToken=token
        ).execute()
        ids = [x.get("contentDetails", {}).get("videoId") for x in page.get("items", [])]
        ids = [i for i in ids if i]
        if ids:
            videos = service.videos().list(part="snippet,status", id=",".join(ids)).execute()
            for item in videos.get("items", []):
                if episode_tag in item.get("snippet", {}).get("tags", []):
                    if item.get("snippet", {}).get("channelId") != EXPECTED_ID:
                        raise ValueError("Vídeo encontrado fora do canal autorizado.")
                    return item
        token = page.get("nextPageToken")
        if not token:
            break
    return None


def load_receipt(path: Path, project_id: str, digest: str):
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("project_id") != project_id or data.get("video_sha256") != digest:
            raise ValueError("Recibo de outro episódio/MP4. Upload bloqueado.")
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", str(data.get("video_id", ""))):
            raise ValueError("ID do vídeo no recibo é inválido.")
        return data
    return None


def save_receipt(path: Path, project_id: str, digest: str, video_id: str, recovered: bool):
    data = {
        "version": "1.0", "destination": "youtube",
        "project_id": project_id, "video_sha256": digest,
        "video_id": video_id, "url": "https://youtu.be/" + video_id,
        "privacy_requested": "private", "thumbnail_required": True,
        "publication": "not_authorized", "recovered_existing_upload": recovered,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def upload_private(service, channel, video_path: Path, metadata: dict, project_id: str, receipt_path: Path):
    """Resumable, private upload with receipt and best-effort duplicate protection."""
    body = validate_package(video_path, metadata, project_id)
    digest = sha256(video_path)
    prior = load_receipt(receipt_path, project_id, digest)
    if prior is not None:
        return prior
    found = lookup_existing(service, channel, "ODE_EPISODE_" + project_id)
    if found is not None:
        if found.get("status", {}).get("privacyStatus") != "private":
            raise ValueError("Episódio já existe, mas não está privado. Não alterar.")
        return save_receipt(receipt_path, project_id, digest, found["id"], True)
    from googleapiclient.http import MediaFileUpload
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    request = service.videos().insert(part="snippet,status", body=body, media_body=media)
    result = None
    while result is None:
        _, result = request.next_chunk(num_retries=3)
    video_id = result.get("id", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Upload sem ID válido; investigar antes de tentar novamente.")
    # Do not publish. Verify channel on the uploaded resource.
    if result.get("snippet", {}).get("channelId", EXPECTED_ID) != EXPECTED_ID:
        raise ValueError("Vídeo enviado para canal inesperado; verifique imediatamente no Studio.")
    return save_receipt(receipt_path, project_id, digest, video_id, False)


def validate_thumbnail_target(service, video_id: str):
    found = service.videos().list(part="snippet,status", id=video_id).execute().get("items", [])
    if len(found) != 1 or found[0].get("snippet", {}).get("channelId") != EXPECTED_ID:
        raise ValueError("O vídeo não pertence ao canal O Dinheiro Explica.")
    if found[0].get("status", {}).get("privacyStatus") != "private":
        raise ValueError("Não alterar capa de vídeo que não esteja privado neste fluxo.")


def add_thumbnail(service, thumbnail: Path, video_id: str):
    if not thumbnail.is_file() or thumbnail.suffix.lower() not in (".png", ".jpg", ".jpeg"):
        raise ValueError("Capa inexistente ou em formato não suportado.")
    validate_thumbnail_target(service, video_id)
    from googleapiclient.http import MediaFileUpload
    mime = "image/png" if thumbnail.suffix.lower() == ".png" else "image/jpeg"
    media = MediaFileUpload(str(thumbnail), mimetype=mime, resumable=False)
    service.thumbnails().set(videoId=video_id, media_body=media).execute()
    return {"video_id": video_id, "thumbnail_sha256": sha256(thumbnail), "privacy": "private"}


def cli():
    p = argparse.ArgumentParser(description="Entrega direta ao YouTube; sempre privado.")
    p.add_argument("action", choices=("verify", "upload-private", "thumbnail"))
    p.add_argument("--project-id")
    p.add_argument("--video")
    p.add_argument("--metadata")
    p.add_argument("--thumbnail")
    p.add_argument("--receipt")
    p.add_argument("--video-id", help="ID do upload privado observado no YouTube")
    p.add_argument("--project", default="video/data/daily.json")
    p.add_argument("--root", default=".")
    args = p.parse_args()
    if args.action == "upload-private" and (not args.project_id or not args.receipt):
        p.error("Envio privado exige --project-id e --receipt.")
    if args.action == "thumbnail" and (not args.project_id or not (args.video_id or args.receipt)):
        p.error("Capa exige --project-id e --video-id (ou --receipt).")
    service = youtube_service()
    try:
        channel = assert_channel(service)
        if args.action == "verify":
            print("YOUTUBE_AUTH_OK: O Dinheiro Explica (@odinheiro.explica); nenhum vídeo enviado.")
            return
        receipt_path = Path(args.receipt) if args.receipt else None
        if args.action == "upload-private":
            if not args.video or not args.metadata:
                p.error("Envio privado exige --video e --metadata.")
            metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
            result = upload_private(service, channel, Path(args.video), metadata, args.project_id, receipt_path)
            print(json.dumps(result, ensure_ascii=False))
        else:
            from thumbnail_contract import validate_thumbnail_audit
            if not args.thumbnail:
                p.error("Capa exige --thumbnail.")
            root = Path(args.root).resolve()
            project = json.loads(Path(args.project).read_text(encoding="utf-8"))
            if project.get("project_id") != args.project_id:
                raise ValueError("ID do projeto difere do projeto aprovado.")
            audit = validate_thumbnail_audit(root, project, Path(args.thumbnail))
            target_id = args.video_id
            if receipt_path and receipt_path.exists():
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                if receipt.get("project_id") != args.project_id or receipt.get("destination") != "youtube":
                    raise ValueError("Recibo não corresponde ao projeto/canal.")
                if target_id and target_id != receipt["video_id"]:
                    raise ValueError("ID informado difere do recibo comprovado.")
                target_id = receipt["video_id"]
            if not target_id or not re.fullmatch(r"[A-Za-z0-9_-]{11}", target_id):
                raise ValueError("Informe ID válido do vídeo privado.")
            result = add_thumbnail(service, Path(args.thumbnail), target_id)
            result["contract_sha256"] = audit["contract_sha256"]
            print(json.dumps(result, ensure_ascii=False))
    except Exception as error:
        # Google API errors can include URL/request metadata; do not log raw exceptions.
        print(f"YOUTUBE_ERROR: {type(error).__name__}: operação interrompida. Verifique credenciais, canal e recibo.")
        raise SystemExit(1) from None


if __name__ == "__main__":
    cli()
