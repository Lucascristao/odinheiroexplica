"""Restore a proven final MP4 and its derivatives without synthesis or rendering.

The downloaded artifact is data, never a replacement for checked-out source.
Provenance, source compatibility, the project, final MP4 and raw speech hashes
must pass before any derivative is copied. Delivery QA runs again afterwards.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
from datetime import datetime, timezone

import requests

from editorial_project import normalize_project


CRITICAL_PATHS = [
    "video/src/", "public/fonts/", "video/hyperframes/", "src/lib/",
    "package.json", "package-lock.json", "scripts/prepare-hyperframes.ts",
    "scripts/render-daily.ts", "worker/editorial_project.py",
    "worker/build_render_input.py", "worker/align_narration.py",
    "worker/editorial_caption_timing.py", "worker/tts_config.py",
    "worker/voice-policy.json", "worker/voice_master.py",
    "worker/synthesize_scenes.py", "worker/gemini_live_fidelity.py",
    "worker/process_voice_continuity.py", "worker/generate_music.py",
    "worker/generate_sound_design.py", "worker/prepare_visual_assets.py",
    "worker/auto_capture_sources.py", "worker/build_youtube_package.py",
    ":(exclude)src/lib/production-chat-request.ts",
]
DERIVED_ROOTS = (
    "video/generated", "public/generated-assets", "public/generated-audio/daily",
    "public/processed-audio/daily", "public/generated-music", "public/generated-clips",
    "research/captures", "render-output/layout-geometry", "render-output/layout-preflight",
    "render-output/layout-final",
)
DERIVED_FILES = {"render-output/daily-video.mp4", "render-output/daily-youtube.json",
                 "render-output/daily-youtube.txt"}
SHA256 = re.compile(r"[0-9a-f]{64}")
MAX_BYTES = 4 * 1024**3


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def canonical(project, reference=None):
    normalized = normalize_project(project)
    original_assets = {asset.get("id"): asset for asset in (reference or {}).get("visual_assets", [])}
    for asset in normalized.get("visual_assets", []):
        if asset.get("type") != "source_excerpt":
            continue
        asset.pop("captured_at", None)
        original = original_assets.get(asset.get("id"))
        if original is not None and not original.get("capture_file") and asset.get("capture_file"):
            safe_id = "".join(c if c.isalnum() or c in "-_" else "-" for c in asset.get("id", "asset"))
            if asset["capture_file"] != f"research/captures/{safe_id}.png":
                raise RuntimeError("Caminho de captura automática diverge do capturador canônico.")
            asset.pop("capture_file")
    return json.dumps(normalized, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def load(path):
    if not path.is_file() or path.stat().st_size > 32 * 1024**2:
        raise RuntimeError(f"JSON necessário ausente ou excessivo: {path.name}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("Consulta/verificação do Git falhou; nenhuma fonte será sobrescrita.")
    return result.stdout.strip()


def github(repository, token, path):
    if not re.fullmatch(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+", repository) or not token:
        raise RuntimeError("Repositório ou autenticação do GitHub ausente/inválido.")
    try:
        response = requests.get(f"https://api.github.com/repos/{repository}/{path}",
                                headers={"Authorization": f"Bearer {token}",
                                         "Accept": "application/vnd.github+json",
                                         "X-GitHub-Api-Version": "2022-11-28"},
                                timeout=(15, 60), allow_redirects=False)
    except requests.RequestException:
        raise RuntimeError("Falha de rede ao consultar proveniência no GitHub.") from None
    with response:
        if response.status_code != 200:
            raise RuntimeError(f"Proveniência recusada pelo GitHub (HTTP {response.status_code}).")
        return response.json()


def verify_source_run(repository, token, run_id):
    if not re.fullmatch(r"[1-9][0-9]{0,19}", str(run_id)):
        raise RuntimeError("source_run_id precisa ser um ID positivo de execução.")
    run = github(repository, token, f"actions/runs/{run_id}")
    if (run.get("id") != int(run_id) or run.get("status") != "completed"
            or run.get("head_branch") != "main"
            or run.get("conclusion") not in {"failure", "success"}
            or str(run.get("path", "")).split("@", 1)[0] != ".github/workflows/render-daily.yml"
            or not re.fullmatch(r"[0-9a-f]{40}", str(run.get("head_sha", "")))):
        raise RuntimeError("Origem não é uma execução finalizada do render diário na main.")
    for field in ("repository", "head_repository"):
        if (run.get(field) or {}).get("full_name", "").casefold() != repository.casefold():
            raise RuntimeError("Render de outro repositório ou fork recusado.")
    if run["repository"].get("id") != run["head_repository"].get("id"):
        raise RuntimeError("Repositório de origem diverge da execução.")
    jobs = github(repository, token, f"actions/runs/{run_id}/attempts/{run['run_attempt']}/jobs?per_page=100")
    proven = any(
        all(any(step.get("name") == name and step.get("conclusion") == "success"
                for step in job.get("steps", []))
            for name in ("Render video with live progress", "Verify delivery before Drive",
                         "Upload production review artifact"))
        for job in jobs.get("jobs", []))
    if not proven:
        raise RuntimeError("Render, QA e upload de artifact precisam ter concluído com sucesso na mesma tentativa.")
    artifacts = github(repository, token, f"actions/runs/{run_id}/artifacts?per_page=100")
    matches = [item for item in artifacts.get("artifacts", [])
               if item.get("name") == "daily-production-review" and item.get("expired") is False]
    if len(matches) != 1:
        raise RuntimeError("Exige um único artifact daily-production-review ativo para evitar tentativa ambígua.")
    artifact = matches[0]
    provenance = artifact.get("workflow_run") or {}
    if (provenance.get("id") != int(run_id) or provenance.get("head_sha") != run["head_sha"]
            or not 0 < artifact.get("size_in_bytes", 0) <= MAX_BYTES
            or not str(artifact.get("digest", "")).startswith("sha256:")
            or not SHA256.fullmatch(str(artifact.get("digest", ""))[7:])):
        raise RuntimeError("Artifact sem origem, tamanho ou digest SHA256 verificáveis.")
    return run, artifact


def safe_tree(directory):
    """Inspect every downloaded entry before trusting/copying even one file."""
    if directory.is_symlink() or not directory.is_dir():
        raise RuntimeError("Diretório do artifact inválido ou simbólico.")
    resolved = directory.resolve()
    files = {}
    total = 0
    for entry in directory.rglob("*"):
        info = entry.lstat()
        reparse = getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if stat.S_ISLNK(info.st_mode) or reparse or not entry.resolve().is_relative_to(resolved):
            raise RuntimeError("Artifact contém link, junção ou caminho fora da pasta autorizada.")
        relative = entry.relative_to(directory).as_posix()
        path = PurePosixPath(relative)
        if (path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts)
                or "\\" in relative or ":" in relative):
            raise RuntimeError("Caminho inseguro no artifact.")
        if stat.S_ISREG(info.st_mode):
            total += info.st_size
            files[relative] = entry
        elif not stat.S_ISDIR(info.st_mode):
            raise RuntimeError("Artifact contém uma entrada não regular.")
        if len(files) > 20000 or total > MAX_BYTES:
            raise RuntimeError("Artifact excede limites de arquivos/tamanho.")
    return files


def required(files, relative):
    if relative not in files:
        raise RuntimeError(f"Derivado obrigatório ausente: {relative}")
    return files[relative]


def safe_destination(root, relative):
    destination = root / relative
    for entry in (destination, *destination.parents):
        if entry == root:
            break
        if entry.is_symlink():
            raise RuntimeError("Destino de restauração contém link simbólico.")
    if not destination.resolve().is_relative_to(root):
        raise RuntimeError("Destino de restauração fora do checkout.")
    return destination


def restore(root, directory, repository, token, run_id):
    root = root.resolve()
    directory = directory.absolute()
    if not directory.resolve().is_relative_to(root / "work"):
        raise RuntimeError("O artifact precisa estar em work/ dentro do checkout.")
    run, artifact = verify_source_run(repository, token, run_id)
    current_sha = git(root, "rev-parse", "HEAD")
    source_sha = run["head_sha"]
    git(root, "fetch", "--no-tags", "origin", source_sha)
    git(root, "diff", "--quiet", "HEAD", "--", *CRITICAL_PATHS)
    git(root, "diff", "--quiet", source_sha, current_sha, "--", *CRITICAL_PATHS)
    files = safe_tree(directory)
    current_project = load(root / "video/data/daily.json")
    project_text = canonical(current_project)
    original_text = canonical(json.loads(git(root, "show", f"{source_sha}:video/data/daily.json")))
    artifact_source_text = canonical(load(required(files, "video/data/daily.json")))
    artifact_text = canonical(load(required(files, "video/generated/daily-project.json")), current_project)
    if project_text != original_text or project_text != artifact_source_text or project_text != artifact_text:
        raise RuntimeError("Projeto atual, projeto no Git original e projeto do artifact divergem.")
    project = json.loads(project_text)
    timeline = load(required(files, "video/generated/daily-render-input.json"))
    manifest = load(required(files, "video/generated/daily-aligned-tts-manifest.json"))
    qa = load(required(files, "video/generated/daily-delivery-qa.json"))
    video = required(files, "render-output/daily-video.mp4")
    video_sha = digest(video)
    if qa.get("status") not in {"pass", "warn"} or qa.get("failures") != [] or (qa.get("video") or {}).get("sha256") != video_sha:
        raise RuntimeError("QA original não aprovou exatamente este MP4.")
    scene_ids = [item["id"] for item in project["scenes"]]
    if (timeline.get("fps") != 30 or not isinstance(timeline.get("duration_in_frames"), int)
            or timeline["duration_in_frames"] <= 0
            or [item.get("id") for item in timeline.get("scenes", [])] != scene_ids
            or [item.get("id") for item in manifest.get("scenes", [])] != scene_ids
            or [item.get("id") for item in qa.get("scenes", [])] != scene_ids):
        raise RuntimeError("Timeline, voz e QA não correspondem às cenas atuais.")
    for audio in manifest["scenes"]:
        name = audio.get("file", "")
        if not name or Path(name).name != name or not name.endswith(".wav"):
            raise RuntimeError("Caminho do áudio original inseguro.")
        raw = required(files, f"public/generated-audio/daily/{name}")
        processed = required(files, f"public/processed-audio/daily/{name}")
        expected = audio.get("audio_sha256")
        if not SHA256.fullmatch(str(expected)) or digest(raw) != expected or digest(processed) != expected:
            raise RuntimeError("WAV original/processado não é byte-idêntico ao manifesto aprovado.")
    master_name = Path(timeline.get("narration_master_audio", "")).name
    master = required(files, f"public/processed-audio/daily/{master_name}")
    if digest(master) != (timeline.get("voice_master") or {}).get("master_sha256"):
        raise RuntimeError("Trilha contínua original ausente ou adulterada.")
    required(files, "render-output/daily-youtube.json")
    required(files, "render-output/daily-youtube.txt")
    plan = [(relative, path, safe_destination(root, relative)) for relative, path in files.items()
            if relative in DERIVED_FILES or any(relative.startswith(prefix + "/") for prefix in DERIVED_ROOTS)]
    restored = []
    for relative, source, destination in plan:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if digest(source) != digest(destination):
            raise RuntimeError("A cópia de um derivado divergiu do artifact.")
        restored.append(relative)
    receipt = {"version": "1.0", "source_run_id": int(run_id), "source_head_sha": source_sha,
               "resume_head_sha": current_sha, "source_artifact_id": artifact["id"],
               "source_artifact_digest": artifact["digest"], "video_sha256": video_sha,
               "project_sha256": hashlib.sha256(project_text.encode()).hexdigest(),
               "source_qa_status": qa["status"], "restored_files": sorted(restored),
               "new_synthesis": False, "new_render": False,
               "restored_at": datetime.now(timezone.utc).isoformat()}
    output = root / "video/generated/daily-resume-receipt.json"
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"MP4 aprovado restaurado: {video_sha}; {len(restored)} derivados; nenhuma síntese/render.")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", default="work/completed-render")
    args = parser.parse_args()
    restore(Path.cwd(), Path(args.artifact_dir), os.environ.get("GITHUB_REPOSITORY", ""),
            os.environ.get("GITHUB_TOKEN", ""), os.environ.get("ODE_SOURCE_RUN_ID", ""))
