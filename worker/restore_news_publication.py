"""Restore an uploaded news video's original proof, without rendering or uploading."""
import argparse
import base64
import hashlib
import io
import json
import os
import re
from pathlib import Path
import zipfile

def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate_bundle(files, receipt_bytes, current_episode, source_episode):
    """Only a matching, previously passed production may release an existing ID."""
    project = json.loads(files["video/generated/daily-project.json"])
    qa = json.loads(files["video/generated/daily-delivery-qa.json"])
    metadata = json.loads(files["render-output/daily-youtube.json"])
    receipt = json.loads(receipt_bytes)
    project_id = project.get("project_id", "")
    if not re.fullmatch(r"noticia-\d{4}-\d{2}-\d{2}-[a-z0-9-]+", project_id):
        raise ValueError("Artefato não é uma notícia única identificada.")
    if current_episode.replace(b"\r\n", b"\n") != source_episode.replace(b"\r\n", b"\n"):
        raise ValueError("Episódio mudou desde o render; não liberar a revisão anterior.")
    episode = json.loads(current_episode)
    if episode.get("episode_id") != project_id or episode.get("editorial_status") != "autonomous_fact_checked":
        raise ValueError("Apuração não corresponde ao projeto original.")
    media_hash = digest(files["render-output/daily-video.mp4"])
    if qa.get("status") not in ("pass", "warn") or qa.get("failures") != []:
        raise ValueError("QA original não autoriza publicação.")
    if (qa.get("video") or {}).get("sha256") != media_hash:
        raise ValueError("MP4 difere do vídeo aprovado pelo QA.")
    if (receipt.get("project_id") != project_id or receipt.get("video_sha256") != media_hash
            or receipt.get("destination") != "youtube" or receipt.get("privacy_requested") != "private"
            or not re.fullmatch(r"[A-Za-z0-9_-]{11}", str(receipt.get("video_id", "")))):
        raise ValueError("Recibo não comprova o upload deste MP4 e episódio.")
    if metadata.get("title") != project.get("title"):
        raise ValueError("Título do pacote difere do projeto original.")
    return project_id, receipt["video_id"]


def restore(repo, run_id, root, token):
    import requests
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or not str(run_id).isdigit():
        raise ValueError("Repositório ou run inválidos.")
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token,
                            "Accept": "application/vnd.github+json"})
    api = "https://api.github.com/repos/" + repo

    def get(path):
        response = session.get(api + path, timeout=90)
        response.raise_for_status()
        return response.json()

    run = get(f"/actions/runs/{run_id}")
    if (run.get("id") != int(run_id) or run.get("head_branch") != "main" or run.get("status") != "completed"
            or not re.fullmatch(r"[0-9a-f]{40}", str(run.get("head_sha", "")))
            or run.get("event") not in ("push", "workflow_dispatch")
            or run.get("path", "").split("@")[0] != ".github/workflows/render-news-single.yml"
            or (run.get("repository") or {}).get("full_name") != repo
            or (run.get("head_repository") or {}).get("full_name") != repo):
        raise ValueError("Run não é uma produção concluída da main deste repositório.")
    jobs = get(f"/actions/runs/{run_id}/jobs?filter=latest").get("jobs", [])
    if len(jobs) != 1:
        raise ValueError("Produção original ambígua.")
    steps = {step["name"]: step.get("conclusion") for step in jobs[0].get("steps", [])}
    for name in ("Render Remotion", "Garantia técnica e vocal", "Entregar vídeo privado sem Google Drive"):
        if steps.get(name) != "success":
            raise ValueError("Produção original não concluiu: " + name)
    artifacts = get(f"/actions/runs/{run_id}/artifacts").get("artifacts", [])

    def archive(name):
        matches = [item for item in artifacts if item["name"] == name and not item.get("expired")]
        if len(matches) != 1:
            raise ValueError("Artefato ausente ou ambíguo: " + name)
        item = matches[0]
        origin = item.get("workflow_run") or {}
        if origin.get("id") != int(run_id) or origin.get("head_sha") != run["head_sha"]:
            raise ValueError("Artefato não pertence à revisão original: " + name)
        response = session.get(api + f"/actions/artifacts/{item['id']}/zip", timeout=90)
        response.raise_for_status()
        if item.get("digest") != "sha256:" + digest(response.content):
            raise ValueError("Hash do artefato diverge: " + name)
        return zipfile.ZipFile(io.BytesIO(response.content))

    names = ("video/generated/daily-project.json", "video/generated/daily-delivery-qa.json",
             "render-output/daily-video.mp4", "render-output/daily-youtube.json")
    with archive("news-single-production-review") as bundle:
        files = {name: bundle.read(name) for name in names}
    with archive("news-single-youtube-private-receipt") as bundle:
        receipt = bundle.read("daily-youtube-private.json")
    project_id = json.loads(files[names[0]]).get("project_id", "")
    if not re.fullmatch(r"noticia-\d{4}-\d{2}-\d{2}-[a-z0-9-]+", project_id):
        raise ValueError("ID de episódio inválido.")
    episode_path = "news/episodes/" + project_id.removeprefix("noticia-") + ".json"
    source = get("/contents/" + episode_path + "?ref=" + run["head_sha"])
    source_episode = base64.b64decode(source["content"])
    current_episode = (root / episode_path).read_bytes()
    project_id, video_id = validate_bundle(files, receipt, current_episode, source_episode)
    files["render-output/daily-youtube-private.json"] = receipt
    for name, data in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    proof = {"source_run_id": int(run_id), "source_commit": run["head_sha"],
             "episode_path": episode_path, "project_id": project_id, "video_id": video_id,
             "video_sha256": digest(files["render-output/daily-video.mp4"]),
             "project_sha256": digest(files["video/generated/daily-project.json"]),
             "rendered_again": False, "uploaded_again": False}
    (root / "render-output/news-publication-recovery.json").write_text(
        json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as env:
        env.write("NEWS_EDITION=" + episode_path + "\n")
    print("ORIGINAL_NEWS_UPLOAD_RESTORED:", json.dumps(proof, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    restore(os.environ["GITHUB_REPOSITORY"], args.run_id, Path(args.root).resolve(), os.environ["GITHUB_TOKEN"])
