"""Free, source-backed thumbnail composition with actual multimodal pixel review.

No paid image model, no invented photos, no replacement of official Roberto.
Failure is OPTIONAL and does not block video release.
"""
import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from google import genai
from google.genai import types

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
        source = ImageOps.fit(src.convert("RGB"), (1280, 720), method=Image.Resampling.LANCZOS)
    washed = ImageEnhance.Color(source).enhance(0.65).filter(ImageFilter.GaussianBlur(11))
    charcoal = Image.new("RGB", (1280, 720), "#090B0D")
    merged = Image.blend(charcoal, washed, 0.52)
    # Keep center/subject visually anchored in authentic document pixels.
    # No logo, headline or new object is generated in the source-backed background.
    merged.save(output)
    print("THUMBNAIL_VERIFIED_DOCUMENT_BACKGROUND", str(real[0]), flush=True)
    return output


def inspect_real_pixels(client, image_path, contract):
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
A imagem de fundo deriva de screenshot editorial autêntico, não de documento fabricado.
Apenas marque true em checks se a respectiva verificação for perceptualmente óbvia.
Cheque texto literalmente palavra por palavra e legibilidade na imagem pequena.
Em cada observations descreva o que efetivamente viu, não a intenção do prompt.
Se não souber se o assunto principal é representado, marque false.
Não alegue inspeção humana nem crie informações ausentes nos pixels."""
    response = client.models.generate_content(
        model=os.getenv("ODE_NEWS_VISION_MODEL", "gemini-3.8-flash"),
        contents=[types.Part.from_bytes(data=full, mime_type="image/jpeg"),
                  types.Part.from_bytes(data=tiny, mime_type="image/jpeg"), prompt],
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0),
    )
    result = json.loads(response.text)
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
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("Auditoria multimodal sem chave; rejeitar capa sem prejudicar publicação.")
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    checks, observations = inspect_real_pixels(client, cover, contract)
    audit = {
        "version": "1.0", "project_id": project["project_id"],
        "project_sha256": normalized_project_sha256(project_path),
        "contract_sha256": contract_sha256(contract),
        "image_sha256": file_sha256(cover),
        "headline": contract["exact_headline"], "approval_status": "approved",
        "reviewer": "Gemini multimodal automated pixel reviewer",
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
