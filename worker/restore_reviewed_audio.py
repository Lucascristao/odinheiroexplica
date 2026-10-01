"""Restore unchanged Gemini narration from a verified production artifact.

No synthesis or audio processing occurs here. Artifact provenance, original
narration hashes, and decoded durations are checked before rebuilding the
worker's cache sidecars. Changed scenes are left for the normal TTS worker.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import time
from urllib.parse import urlparse
import zipfile

import requests

from synthesize_scenes import (
    FALLBACK_TTS_MODEL,
    FALLBACK_VOICE_TREATMENT,
    NO_VOICE_TREATMENT,
    PRIMARY_TTS_MODEL,
    SECONDARY_TTS_MODEL,
    TTS_MODEL_CASCADE,
    audio_sha256,
    cached_duration,
    duration_seconds,
    save_audio_sidecar,
    voice_treatment_for_model,
)
from tts_config import (
    DEFAULT_PRESENTER,
    DEFAULT_TTS_VOICE,
    PRESENTER_VOICES,
    voice_policy_fingerprint,
)


MAX_ARCHIVE_BYTES = 2 * 1024**3
MAX_AUDIO_BYTES = 128 * 1024**2
MAX_JSON_BYTES = 16 * 1024**2
SHA256 = re.compile(r"[0-9a-f]{64}")
SCENE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}")


def requested_artifact(explicit: int | None, trigger_file: Path) -> int | None:
    markers = []
    if trigger_file.is_file():
        for line in trigger_file.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip().startswith("restore_audio_artifact"):
                continue
            match = re.fullmatch(r"\s*restore_audio_artifact\s*=\s*([1-9][0-9]*)\s*", line)
            if not match:
                raise RuntimeError("Marcador restore_audio_artifact inválido.")
            markers.append(int(match.group(1)))
    if len(set(markers)) > 1 or (explicit and markers and explicit != markers[0]):
        raise RuntimeError("IDs de artifact conflitantes no pedido de restauração.")
    artifact_id = explicit or (markers[0] if markers else None)
    if artifact_id is not None and artifact_id <= 0:
        raise RuntimeError("O artifact deve ter um ID positivo.")
    return artifact_id


class GitHubArtifacts:
    def __init__(self, repository: str, token: str) -> None:
        if not re.fullmatch(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+", repository):
            raise RuntimeError("GITHUB_REPOSITORY inválido ou ausente.")
        if not token:
            raise RuntimeError("GITHUB_TOKEN ausente para ler o artifact autorizado.")
        self.repository = repository
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def request(self, path: str, *, stream: bool = False) -> requests.Response:
        for attempt in range(3):
            try:
                response = requests.get(
                    f"https://api.github.com/repos/{self.repository}/{path}",
                    headers=self.headers, timeout=(15, 90),
                    allow_redirects=False, stream=stream,
                )
            except requests.RequestException:
                if attempt == 2:
                    raise RuntimeError("Falha de rede ao consultar o artifact no GitHub.") from None
                time.sleep(2**attempt)
                continue
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                response.close()
                time.sleep(2**attempt)
                continue
            return response
        raise RuntimeError("Não foi possível consultar o artifact.")

    def metadata(self, path: str) -> dict:
        with self.request(path) as response:
            if response.status_code != 200:
                raise RuntimeError(f"GitHub recusou leitura do artifact/run (HTTP {response.status_code}).")
            try:
                payload = response.json()
            except ValueError:
                raise RuntimeError("Metadados inválidos recebidos do GitHub.") from None
        if not isinstance(payload, dict):
            raise RuntimeError("Metadados do artifact/run não são um objeto.")
        return payload

    def verified_metadata(self, artifact_id: int) -> tuple[dict, dict, str]:
        artifact = self.metadata(f"actions/artifacts/{artifact_id}")
        if artifact.get("id") != artifact_id or artifact.get("expired") is not False:
            raise RuntimeError("Artifact incorreto ou expirado; nenhuma restauração realizada.")
        if artifact.get("name") != "daily-production-review":
            raise RuntimeError("A restauração exige um artifact de produção daily-production-review.")
        size = artifact.get("size_in_bytes")
        if not isinstance(size, int) or not 0 < size <= MAX_ARCHIVE_BYTES:
            raise RuntimeError("Tamanho do artifact inválido ou superior ao limite.")
        digest = str(artifact.get("digest") or "")
        if not digest.startswith("sha256:") or not SHA256.fullmatch(digest[7:]):
            raise RuntimeError("Artifact sem digest SHA256 verificável no GitHub.")
        provenance = artifact.get("workflow_run") or {}
        run_id = provenance.get("id")
        if not isinstance(run_id, int) or run_id <= 0:
            raise RuntimeError("Artifact sem run de origem identificável.")
        run = self.metadata(f"actions/runs/{run_id}")
        if (
            run.get("id") != run_id
            or run.get("head_sha") != provenance.get("head_sha")
            or not re.fullmatch(r"[0-9a-f]{40}", str(run.get("head_sha") or ""))
            or run.get("status") != "completed"
            or run.get("conclusion") != "success"
        ):
            raise RuntimeError("O run de origem não corresponde a uma produção concluída com sucesso.")
        for field in ("repository", "head_repository"):
            repository = run.get(field) or {}
            expected_id = provenance.get("repository_id" if field == "repository" else "head_repository_id")
            if (
                str(repository.get("full_name") or "").lower() != self.repository.lower()
                or repository.get("id") != expected_id
            ):
                raise RuntimeError("Artifact/run de outro repositório ou fork recusado.")
        if str(run.get("path") or "").split("@", 1)[0] != ".github/workflows/render-daily.yml":
            raise RuntimeError("O artifact não pertence ao workflow diário de produção.")
        return artifact, run, digest[7:]

    def download(self, artifact: dict, destination: Path, expected_digest: str) -> None:
        # The API redirect is authenticated; signed storage requests never carry
        # the GitHub token. Never log their URL, which can contain credentials.
        for attempt in range(3):
            response = self.request(f"actions/artifacts/{artifact['id']}/zip", stream=True)
            try:
                for _ in range(4):
                    if response.status_code not in {301, 302, 303, 307, 308}:
                        break
                    location = response.headers.get("Location", "")
                    response.close()
                    parsed = urlparse(location)
                    host = parsed.hostname or ""
                    allowed = host == "api.github.com" or host.endswith((".githubusercontent.com", ".blob.core.windows.net"))
                    if parsed.scheme != "https" or not allowed or parsed.username or parsed.password:
                        raise RuntimeError("Destino de download do GitHub não reconhecido.")
                    response = requests.get(location, timeout=(15, 90), stream=True, allow_redirects=False)
                if response.status_code != 200:
                    raise RuntimeError(f"Download do artifact recusado (HTTP {response.status_code}).")
                received = 0
                digest = hashlib.sha256()
                with destination.open("wb") as output:
                    for chunk in response.iter_content(chunk_size=1024**2):
                        if not chunk:
                            continue
                        received += len(chunk)
                        if received > artifact["size_in_bytes"] or received > MAX_ARCHIVE_BYTES:
                            raise RuntimeError("Download excedeu o tamanho do artifact informado pelo GitHub.")
                        digest.update(chunk)
                        output.write(chunk)
                if received != artifact["size_in_bytes"] or digest.hexdigest() != expected_digest:
                    raise RuntimeError("SHA256 ou tamanho do ZIP diverge do artifact registrado no GitHub.")
                return
            except requests.RequestException:
                if attempt == 2:
                    raise RuntimeError("Falha de rede durante download do artifact.") from None
                time.sleep(2**attempt)
            finally:
                response.close()


def safe_members(archive: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    members = {}
    infos = archive.infolist()
    if len(infos) > 10000:
        raise RuntimeError("ZIP contém arquivos demais.")
    for info in infos:
        name = info.filename
        path = PurePosixPath(name)
        mode = info.external_attr >> 16
        if (
            not name or "\\" in name or "\x00" in name or ":" in name
            or path.is_absolute() or ".." in path.parts
            or stat.S_ISLNK(mode) or info.flag_bits & 1
            or name in members
        ):
            raise RuntimeError("ZIP contém caminho inseguro, duplicado ou arquivo não permitido.")
        if not info.is_dir():
            members[name] = info
    return members


def unique_member(members: dict, filename: str) -> zipfile.ZipInfo:
    matches = [info for name, info in members.items() if PurePosixPath(name).name == filename]
    if len(matches) != 1:
        raise RuntimeError(f"O artifact deve conter exatamente um {filename}.")
    return matches[0]


def read_json(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> dict:
    if info.file_size > MAX_JSON_BYTES:
        raise RuntimeError("JSON do artifact excede o limite de tamanho.")
    try:
        payload = json.loads(archive.read(info).decode("utf-8-sig"))
    except (ValueError, UnicodeError):
        raise RuntimeError("JSON inválido no artifact de produção.") from None
    if not isinstance(payload, dict):
        raise RuntimeError("JSON do artifact não é um objeto.")
    return payload


def scene_jobs(project: dict) -> dict[str, dict]:
    scenes = project.get("scenes") or project.get("script", {}).get("scenes", [])
    jobs = {}
    for position, scene in enumerate(scenes):
        index = scene.get("scene_index", scene.get("index", position))
        scene_id = str(scene.get("id") or f"scene-{int(index):02d}")
        if not SCENE_ID.fullmatch(scene_id) or ".." in scene_id or scene_id in jobs:
            raise RuntimeError("IDs de cenas inválidos ou duplicados.")
        # Match synthesize_scenes.main exactly. The hash covers the original
        # narration after strip(), before any optional pronunciation expansion.
        narration = str(scene["narration"]).strip()
        jobs[scene_id] = {"hash": hashlib.sha256(narration.encode("utf-8")).hexdigest()}
    if not jobs:
        raise RuntimeError("Projeto sem cenas para restaurar.")
    return jobs


def restore(project: dict, archive_path: Path, output_dir: Path, provenance: dict) -> tuple[int, int]:
    targets = scene_jobs(project)
    presenter = project.get("presenter") or {}
    presenter_key = str(presenter.get("gender") or presenter.get("voice_id") or DEFAULT_PRESENTER)
    project_voice = PRESENTER_VOICES.get(presenter_key, DEFAULT_TTS_VOICE)
    with zipfile.ZipFile(archive_path) as archive:
        members = safe_members(archive)
        manifest = read_json(archive, unique_member(members, "daily-tts-manifest.json"))
        original_render = read_json(archive, unique_member(members, "daily-render-input.json"))
        if not project.get("project_id") or original_render.get("project_id") != project["project_id"]:
            print("[Audio Restore] Projeto diferente do artifact; todas as cenas permanecem pendentes.", flush=True)
            return 0, len(targets)
        originals = scene_jobs(original_render)
        if manifest.get("engine") != "google-gemini-tts" or manifest.get("voice") != project_voice:
            raise RuntimeError("Artifact sem narração Google Gemini na mesma voz do projeto.")
        audio_scenes = manifest.get("scenes")
        if not isinstance(audio_scenes, list):
            raise RuntimeError("Manifest de áudio não contém cenas válidas.")
        audio_by_id = {}
        for scene in audio_scenes:
            scene_id = scene.get("id")
            if not isinstance(scene_id, str) or scene_id in audio_by_id:
                raise RuntimeError("Manifest de áudio contém IDs inválidos ou duplicados.")
            audio_by_id[scene_id] = scene
        output_dir.mkdir(parents=True, exist_ok=True)
        restored = 0
        for scene_id, target in targets.items():
            source = audio_by_id.get(scene_id)
            if not source or source.get("narration_sha256") != target["hash"]:
                print(f"[Audio Restore] {scene_id}: texto/id diferente; mantida para o TTS normal.", flush=True)
                continue
            if originals.get(scene_id, {}).get("hash") != target["hash"]:
                raise RuntimeError(f"Narração de origem não corresponde ao manifest em {scene_id}.")
            model = source.get("model")
            treatment = source.get("voice_treatment", NO_VOICE_TREATMENT)
            if source.get("engine") != "google-gemini-tts" or source.get("voice") != project_voice or model not in TTS_MODEL_CASCADE:
                raise RuntimeError(f"Modelo, voz ou tratamento não permitido na origem de {scene_id}.")
            if source.get("voice_policy_fingerprint") != voice_policy_fingerprint(model, project_voice):
                print(
                    f"[Audio Restore] {scene_id}: política de voz de origem ausente/diferente; "
                    "mantida para o TTS normal.",
                    flush=True,
                )
                continue
            if treatment != voice_treatment_for_model(model, project_voice):
                raise RuntimeError(f"Tratamento de áudio diverge da política de origem em {scene_id}.")
            if source.get("file") != f"{scene_id}.mp3":
                raise RuntimeError(f"Nome do MP3 não corresponde à cena {scene_id}.")
            audio_info = unique_member(members, source["file"])
            if not 1000 < audio_info.file_size <= MAX_AUDIO_BYTES:
                raise RuntimeError(f"Tamanho de áudio inválido na cena {scene_id}.")
            output = output_dir / source["file"]
            temporary = output.with_name(output.stem + ".restore.mp3")
            try:
                temporary.write_bytes(archive.read(audio_info))
                actual_duration = duration_seconds(temporary)
                recorded_duration = float(source["duration_seconds"])
                if (
                    not math.isfinite(actual_duration) or actual_duration <= 0
                    or not math.isfinite(recorded_duration)
                    or abs(actual_duration - recorded_duration) > 0.05
                ):
                    raise RuntimeError(f"Duração do MP3 diverge do manifest em {scene_id}.")
                source_hash = source.get("audio_sha256")
                if source_hash and source_hash != audio_sha256(temporary):
                    raise RuntimeError(f"Hash do MP3 diverge do manifest em {scene_id}.")
                # Older production artifacts omit sidecars/audio hashes. The
                # authenticated GitHub ZIP digest binds their original MP3 bytes.
                temporary.replace(output)
                save_audio_sidecar(
                    output, target["hash"], model, project_voice, actual_duration,
                    treatment, source.get("fallback_reason"),
                )
                sidecar = output.with_suffix(".tts.json")
                metadata = json.loads(sidecar.read_text(encoding="utf-8"))
                metadata["restored_from_artifact"] = provenance
                sidecar_tmp = sidecar.with_name(sidecar.name + ".tmp")
                sidecar_tmp.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                sidecar_tmp.replace(sidecar)
                if cached_duration(output, target["hash"], model, project_voice, treatment) is None:
                    raise RuntimeError(f"Cache restaurado não passou pela validação do worker em {scene_id}.")
                restored += 1
            finally:
                temporary.unlink(missing_ok=True)
    return restored, len(targets) - restored


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--artifact-id", type=int)
    parser.add_argument("--trigger-file", default="render-trigger/daily.txt")
    parser.add_argument("--output-dir", default="public/generated-audio/daily")
    args = parser.parse_args()
    artifact_id = requested_artifact(args.artifact_id, Path(args.trigger_file))
    if artifact_id is None:
        print("[Audio Restore] Sem artifact solicitado; seguindo com o cache/TTS normal.", flush=True)
        return
    project = json.loads(Path(args.project).read_text(encoding="utf-8-sig"))
    github = GitHubArtifacts(os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", "").strip())
    artifact, run, digest = github.verified_metadata(artifact_id)
    with tempfile.TemporaryDirectory(prefix="ode-reviewed-audio-") as folder:
        archive_path = Path(folder) / "review.zip"
        github.download(artifact, archive_path, digest)
        restored, pending = restore(project, archive_path, Path(args.output_dir), {
            "artifact_id": artifact_id,
            "repository": github.repository,
            "run_id": run["id"],
            "head_sha": run["head_sha"],
            "archive_sha256": digest,
        })
    print(f"[Audio Restore] {restored} cenas reutilizadas; {pending} cenas pendentes. Nenhuma chamada TTS realizada.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(f"[Audio Restore] Erro: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
