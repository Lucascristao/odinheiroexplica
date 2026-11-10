"""Free, source-backed thumbnail composition with actual multimodal pixel review.

No paid image model, no invented photos, no replacement of official Roberto.
Failure is OPTIONAL and does not block video release.
"""
import argparse
import base64
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import requests
import time

from thumbnail_contract import (
    REQUIRED_CHECKS, REQUIRED_OBSERVATIONS, read_contract, contract_sha256,
    file_sha256, normalized_project_sha256, validate_thumbnail_audit,
)


def make_background(root, project, episode):
    docs = episode["documentary_evidence"]
    real = []
    for doc in docs:
        candidate = root / doc["capture_file"]
        if candidate.is_file() and candidate.stat().st_size > 5000:
            real.append(candidate)
    if not real:
        raise ValueError("Capa: nenhum documento real capturado; não inventar cenário.")
    directory = root / "production" / episode["episode_id"]
    directory.mkdir(parents=True, exist_ok=True)
    output = directory / "thumbnail-background.png"
    with Image.open(real[0]) as src:
        original = src.convert("RGB")
        source = ImageOps.fit(original, (1280, 720), method=Image.Resampling.LANCZOS)
    washed = ImageEnhance.Color(source).enhance(0.65).filter(ImageFilter.GaussianBlur(11))
    charcoal = Image.new("RGB", (1280, 720), "#090B0D")
    merged = Image.blend(charcoal, washed, 0.52)
    # Keep an unaltered, sharp documentary object above the headline, on the
    # side opposite Roberto. The washed copy supplies depth, not the evidence.
    document = ImageOps.contain(original, (590, 330), method=Image.Resampling.LANCZOS)
    framed = ImageOps.expand(document, border=3, fill="#D4D8DC")
    column_x = 42 if episode.get("thumbnail_text_side") != "right" else 648
    x, y = column_x + (590 - document.width) // 2, 58
    shadow = Image.new("RGBA", (1280, 720))
    shadow.paste((0, 0, 0, 180), (x-8, y+10, x+framed.width+8, y+framed.height+26))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    merged = Image.alpha_composite(merged.convert("RGBA"), shadow)
    merged.paste(framed, (x, y))
    merged = merged.convert("RGB")
    merged.save(output)
    print("THUMBNAIL_VERIFIED_DOCUMENT_BACKGROUND", str(real[0]), flush=True)
    return output


def inspect_real_pixels(image_path, contract):
    full = image_path.read_bytes()
    with Image.open(image_path) as image:
        small = image.convert("RGB").resize((320, 180), Image.Resampling.LANCZOS)
        from io import BytesIO
        stream = BytesIO()
        small.save(stream, "JPEG", quality=85)
        tiny = stream.getvalue()
    prompt = f"""Você é um auditor multimodal conservador. Inspecione realmente as DUAS imagens anexadas:
a thumbnail final de 1280x720 e sua redução real a 320x180 pixels.
Responda APENAS JSON com checks (booleanos) e observations (strings em pt-BR),
com exatamente as chaves {list(REQUIRED_CHECKS)} e {list(REQUIRED_OBSERVATIONS)}.
A headline exata que deve ser legível é {contract['exact_headline']!r}.
Protagonista exigido: {contract['primary_subject']}.
Elemento de apoio permitido: {contract['secondary_subject']!r}.
Identidade: carvão #090B0D, amarelo #FFBD19, texto claro; rosto oficial do Roberto,
sem deformação, e headline não encoberta. Exclusões: {contract['forbidden_elements']}.
A imagem contém documento real em primeiro plano e fundo derivado da mesma captura; textos do print são parte da fonte, não headline autoral extra.
Não exigir fotografia do personagem quando o contrato autoriza a prova documental como protagonista. Avalie legibilidade da headline e clareza do assunto; não reprovar por preferência estética pessoal.
Apenas marque true em checks se a respectiva verificação for perceptualmente óbvia.
Cheque texto literalmente palavra por palavra e legibilidade na imagem pequena.
Em cada observations descreva o que efetivamente viu, não a intenção do prompt.
Se não souber se o assunto principal é representado, marque false.
Não alegue inspeção humana nem crie informações ausentes nos pixels."""
    content = [{"type": "text", "text": prompt}]
    for pixels in (full, tiny):
        content.append({"type": "image_url", "image_url": {
            "url": "data:image/jpeg;base64," + base64.b64encode(pixels).decode("ascii")}})
    for attempt in range(2):
        response = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": "Bearer " + os.environ["GROQ_API_KEY"], "Content-Type": "application/json"},
            json={"model": os.getenv("ODE_NEWS_VISION_MODEL", "qwen/qwen3.8-27b"),
                  "messages": [{"role": "user", "content": content}],
                  "response_format": {"type": "json_object"}, "temperature": 0, "max_completion_tokens": 1600}, timeout=90)
        if response.status_code == 429 and attempt == 0:
            try:
                delay = float(response.headers.get("retry-after", "30"))
            except ValueError:
                delay = 30
            if delay > 60:
                raise ValueError("Capa opcional: quota de visão indisponível nesta janela")
            time.sleep(max(5, delay))
            continue
        if response.status_code != 200:
            raise ValueError("Capa opcional: revisão visual Groq HTTP " + str(response.status_code))
        payload = response.json()
        if payload["choices"][0].get("finish_reason") == "length":
            raise ValueError("Capa opcional: revisão visual truncada")
        result = json.loads(payload["choices"][0]["message"]["content"])
        break
    checks, observations = result.get("checks", {}), result.get("observations", {})
    if set(checks) != set(REQUIRED_CHECKS) or set(observations) != set(REQUIRED_OBSERVATIONS):
        raise ValueError("Revisão multimodal incompleta.")
    if not all(checks[k] is True for k in REQUIRED_CHECKS):
        raise ValueError("Revisão multimodal reprovou algum critério; não anexar.")
    if not all(isinstance(observations[k], str) and len(observations[k].strip()) >= 15
               for k in REQUIRED_OBSERVATIONS):
        raise ValueError("Observações sem evidência visual suficiente.")
    return checks, observations


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True)
    p.add_argument("--episode", required=True)
    args = p.parse_args()
    root = Path.cwd()
    project_path = root / args.project
    project = json.loads(project_path.read_text(encoding="utf-8"))
    episode = json.loads((root / args.episode).read_text(encoding="utf-8"))
    if project["project_id"] != episode["episode_id"]:
        raise ValueError("Projeto e episódio não correspondem.")
    folder = root / "production" / project["project_id"]
    contract = read_contract(project, folder)
    if not contract.get("presenter_identity"):
        raise ValueError("Edição sem identidade oficial do Roberto.")
    background = make_background(root, project, episode)
    side = "left" if episode.get("thumbnail_text_side") == "right" else "right"
    subprocess.run(["npx", "tsx", "scripts/compose-news-thumbnail.ts",
                    "--project", args.project, "--background", str(background.relative_to(root)),
                    "--portrait-side", side, "--headline-position", "lower",
                    "--portrait-size", "close"], check=True)
    cover = folder / "thumbnail.jpg"
    if not os.environ.get("GROQ_API_KEY"):
        raise ValueError("Revisão visual Groq indisponível; publicar com miniatura automática.")
    checks, observations = inspect_real_pixels(cover, contract)
    audit = {
        "version": "1.0", "project_id": project["project_id"],
        "project_sha256": normalized_project_sha256(project_path),
        "contract_sha256": contract_sha256(contract),
        "image_sha256": file_sha256(cover),
        "headline": contract["exact_headline"], "approval_status": "approved",
        "reviewer": "Groq multimodal automated pixel reviewer; " + os.getenv("ODE_NEWS_VISION_MODEL", "qwen/qwen3.8-27b"),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks, "observations": observations,
        "checked_forbidden_elements": contract["forbidden_elements"],
        "observed_forbidden_elements": [],
    }
    (folder / "thumbnail-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validate_thumbnail_audit(root, project, cover, project_source_path=project_path)
    print("FREE_NEWS_THUMBNAIL_AUDITED", str(cover), flush=True)


if __name__ == "__main__":
    main()
