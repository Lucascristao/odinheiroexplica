from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/drive.file"]
ProgressCallback = Callable[[float], None]


def credentials_from_env() -> Credentials | None:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN", "").strip()

    if not (client_id and client_secret and refresh_token):
        return None

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )


class DriveUploader:
    def __init__(self, folder_id: str):
        if not folder_id:
            raise ValueError("GOOGLE_DRIVE_FOLDER_ID não informado.")

        self.folder_id = folder_id
        self.service = self._create_service()

    def _create_service(self):
        creds = credentials_from_env()
        if creds is None:
            raise RuntimeError(
                "Credenciais do Google Drive ausentes. Defina GOOGLE_CLIENT_ID, "
                "GOOGLE_CLIENT_SECRET e GOOGLE_REFRESH_TOKEN."
            )
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    def create_folder(self, name: str, parent_id: str | None = None) -> str:
        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id or self.folder_id],
        }

        last_error = None
        for attempt in range(1, 4):
            try:
                result = (
                    self.service.files()
                    .create(body=metadata, fields="id,name")
                    .execute(num_retries=3)
                )
                return str(result["id"])
            except Exception as exc:
                last_error = exc
                print(
                    f"[Drive] Falha ao criar pasta '{name}' "
                    f"({attempt}/3): {exc}",
                    flush=True,
                )
                if attempt < 3:
                    time.sleep(1.5 * attempt)
                    self.service = self._create_service()

        raise RuntimeError(
            f"Falha ao criar pasta '{name}' no Drive: {last_error}"
        ) from last_error

    def upload(
        self,
        file_path: str | Path,
        name: str | None = None,
        *,
        folder_id: str | None = None,
        progress_cb: ProgressCallback | None = None,
    ) -> str:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(file_path)

        final_name = name or file_path.name
        last_error = None

        for attempt in range(1, 6):
            try:
                metadata = {
                    "name": final_name,
                    "parents": [folder_id or self.folder_id],
                }
                media = MediaFileUpload(
                    str(file_path),
                    resumable=True,
                    chunksize=8 * 1024 * 1024,
                )
                request = self.service.files().create(
                    body=metadata,
                    media_body=media,
                    fields="id,name,webViewLink",
                )

                response = None
                last_report = -1.0
                while response is None:
                    status, response = request.next_chunk(num_retries=5)
                    if status is not None and progress_cb is not None:
                        progress = max(0.0, min(1.0, float(status.progress())))
                        if progress >= 1.0 or progress - last_report >= 0.05:
                            progress_cb(progress)
                            last_report = progress

                if progress_cb is not None:
                    progress_cb(1.0)

                return str(response["id"])
            except Exception as exc:
                last_error = exc
                print(
                    f"[Drive] Falha no upload de '{final_name}' "
                    f"({attempt}/5): {type(exc).__name__} - {exc}",
                    flush=True,
                )
                if attempt < 5:
                    time.sleep(2.0 * attempt)
                    self.service = self._create_service()

        raise RuntimeError(
            f"Falha ao enviar '{final_name}' ao Drive: {last_error}"
        ) from last_error


def uploader_from_env() -> DriveUploader | None:
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()
    creds = credentials_from_env()

    if not folder_id or creds is None:
        return None

    return DriveUploader(folder_id)
