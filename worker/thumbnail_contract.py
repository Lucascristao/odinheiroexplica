"""Thumbnail editorial review contract: deterministic provenance gate before Drive upload.

No pixel classifier is run here. The recorded visual observations are made by
an agent or person who inspected the actual image. Hash and contract checks
make that attestation episode-specific and stale-image resistant.
"""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

REQUIRED_CHECKS = (
    "headline_exact", "primary_subject", "secondary_subject", "forbidden_absent",
    "identity_and_mobile", "no_fabricated_data", "unique_composition",
)
REQUIRED_OBSERVATIONS = (
    "headline", "primary_subject", "secondary_subject", "forbidden_absent",
    "identity_and_mobile", "no_fabricated_data", "unique_composition",
)


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized_project_sha256(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def contract_sha256(contract):
    raw = json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def read_contract(project, production_dir):
    """Use the VideoProject contract; legacy episode may have an explicit snapshot."""
    episode_id = str(project.get("project_id") or "")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", episode_id):
        raise ValueError("thumbnail: project_id inválido.")
    thumbnail = ((project.get("packaging") or {}).get("thumbnails") or [None])[0]
    if not isinstance(thumbnail, dict):
        raise ValueError("thumbnail: packaging.thumbnails[0] ausente.")
    inline = thumbnail.get("contract")
    legacy_path = Path(production_dir) / "thumbnail-contract.json"
    snapshot = json.loads(legacy_path.read_text(encoding="utf-8")) if legacy_path.exists() else None
    if snapshot and (
        snapshot.get("project_id") != episode_id or
        snapshot.get("headline") != thumbnail.get("headline")
    ):
        raise ValueError("thumbnail: snapshot de outro episódio/embalagem.")
    if inline and snapshot and contract_sha256(inline) != contract_sha256(snapshot.get("contract")):
        raise ValueError("thumbnail: snapshot diverge do contrato do projeto.")
    contract = inline or (snapshot.get("contract") if snapshot else None)
    if not isinstance(contract, dict):
        raise ValueError("thumbnail: contrato não encontrado.")
    expected = {
        "version", "exact_headline", "primary_subject", "secondary_subject",
        "composition", "visual_tension", "forbidden_elements",
        "palette", "format", "no_extra_text",
    }
    if set(contract) != expected or contract.get("version") != "1.0":
        raise ValueError("thumbnail: esquema do contrato diferente da versão 1.0.")
    if contract["exact_headline"] != thumbnail.get("headline"):
        raise ValueError("thumbnail: headline diverge da embalagem aprovada.")
    for key in ("primary_subject", "composition", "visual_tension"):
        if not isinstance(contract[key], str) or len(contract[key].strip()) < 5:
            raise ValueError(f"thumbnail: {key} incompleto.")
    sec = contract["secondary_subject"]
    if sec is not None and (not isinstance(sec, str) or len(sec.strip()) < 5):
        raise ValueError("thumbnail: secondary_subject inválido.")
    blocked = contract["forbidden_elements"]
    if not isinstance(blocked, list) or not 2 <= len(blocked) <= 20 or any(
        not isinstance(x, str) or len(x.strip()) < 3 for x in blocked
    ) or len({x.strip().casefold() for x in blocked}) != len(blocked):
        raise ValueError("thumbnail: forbidden_elements inválido.")
    colors = contract["palette"]
    if not isinstance(colors, dict) or set(colors) != {"base", "accent", "text"}:
        raise ValueError("thumbnail: palette inválida.")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(colors["base"])) or colors["accent"] != "#FFBD19" or colors["text"] != "#F6F7F8":
        raise ValueError("thumbnail: identidade de cores incompatível.")
    if contract["format"] != {"width": 1280, "height": 720} or contract["no_extra_text"] is not True:
        raise ValueError("thumbnail: dimensão ou texto extra não autorizados.")
    return contract


def validate_thumbnail_audit(root, project, thumbnail_path):
    root = Path(root)
    episode_id = project.get("project_id")
    production_dir = root / "production" / str(episode_id)
    image = Path(thumbnail_path)
    if image.resolve().parent != production_dir.resolve() or image.name not in ("thumbnail.jpg", "thumbnail.png"):
        raise ValueError("thumbnail: arquivo fora do caminho canônico do episódio.")
    contract = read_contract(project, production_dir)
    audit_path = production_dir / "thumbnail-audit.json"
    if not audit_path.is_file():
        raise ValueError("thumbnail: auditoria visual ausente. Não enviar imagem não revisada.")
    data = json.loads(audit_path.read_text(encoding="utf-8"))
    project_path = root / "video" / "data" / "daily.json"
    required = {
        "version", "project_id", "project_sha256", "contract_sha256", "image_sha256",
        "headline", "approval_status", "reviewer", "reviewed_at",
        "checks", "observations", "checked_forbidden_elements", "observed_forbidden_elements",
    }
    if set(data) != required:
        raise ValueError("thumbnail: auditoria com campos faltantes ou não reconhecidos.")
    if data["version"] != "1.0" or data["project_id"] != episode_id:
        raise ValueError("thumbnail: auditoria pertence a outro projeto.")
    if data["project_sha256"] != normalized_project_sha256(project_path):
        raise ValueError("thumbnail: roteiro alterado depois da revisão; refaça a auditoria.")
    if data["contract_sha256"] != contract_sha256(contract):
        raise ValueError("thumbnail: contrato alterado depois da revisão; refaça a auditoria.")
    if data["image_sha256"] != file_sha256(image):
        raise ValueError("thumbnail: capa alterada depois da revisão; refaça a auditoria.")
    if data["headline"] != contract["exact_headline"]:
        raise ValueError("thumbnail: headline observada não corresponde à aprovada.")
    if data["approval_status"] != "approved":
        raise ValueError("thumbnail: auditoria não aprovou a capa.")
    if not isinstance(data["reviewer"], str) or len(data["reviewer"].strip()) < 3:
        raise ValueError("thumbnail: informe responsável pela inspeção visual.")
    try:
        datetime.fromisoformat(data["reviewed_at"].replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("thumbnail: data de inspeção inválida.") from None
    checks = data["checks"]
    if not isinstance(checks, dict) or set(checks) != set(REQUIRED_CHECKS) or not all(checks[k] is True for k in REQUIRED_CHECKS):
        raise ValueError("thumbnail: todos os critérios precisam estar confirmados após inspeção visual real.")
    observations = data["observations"]
    if not isinstance(observations, dict) or set(observations) != set(REQUIRED_OBSERVATIONS) or any(
        not isinstance(observations[k], str) or len(observations[k].strip()) < 12
        for k in REQUIRED_OBSERVATIONS
    ):
        raise ValueError("thumbnail: descreva evidência observada em cada critério, sem aprovações vazias.")
    if data["checked_forbidden_elements"] != contract["forbidden_elements"]:
        raise ValueError("thumbnail: nem todas as exclusões foram conferidas.")
    if data["observed_forbidden_elements"] != []:
        raise ValueError("thumbnail: imagem contém elemento proibido; gere nova capa e nova auditoria.")
    return {"audit_path": audit_path, "audit_sha256": file_sha256(audit_path), "contract_sha256": contract_sha256(contract)}
