"""Locked presenter assets: no face generation, matching or identity substitution."""
import json
import hashlib
from datetime import date, datetime, timezone
from pathlib import Path


def news_presenter_contract(news_date, root=None, *, reviewed_at=None, expression=None, variant_key=None):
    root = Path(root) if root else Path(__file__).resolve().parent.parent
    policy = json.loads((root / "worker/presenter-identity.json").read_text(encoding="utf-8"))
    if news_date < policy["news_enabled_since"]:
        return None  # Historical projects retain their exact original contracts.
    identity_id = policy["default_news_presenter"]
    reviewed = None
    if reviewed_at:
        reviewed = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
        if reviewed.tzinfo is None:
            reviewed = reviewed.replace(tzinfo=timezone.utc)
    cutoff = policy.get("expressions_enabled_after_utc")
    if cutoff and reviewed:
        if reviewed >= datetime.fromisoformat(cutoff):
            identity_id = policy.get("default_new_news_presenter", identity_id)
    allowed = {policy["default_news_presenter"], policy.get("default_new_news_presenter")}
    variants = policy.get("news_variant_ids", [])
    variants_cutoff = policy.get("variants_enabled_after_utc")
    if variants_cutoff and reviewed and reviewed >= datetime.fromisoformat(variants_cutoff):
        allowed.update(variants)
        # Stable per date/window: retries reuse the same contract and portrait pixels.
        # Editorial choice below takes precedence over this fallback.
        slots = ("manha", "meio-dia", "noite")
        slot_index = next((i for i, slot in enumerate(slots) if str(variant_key).endswith("-" + slot)), None)
        if variants and slot_index is not None:
            identity_id = variants[(date.fromisoformat(news_date).toordinal() + slot_index) % len(variants)]
    if expression is not None:
        if expression not in allowed:
            raise ValueError("thumbnail: expressão não pertence ao catálogo conferido do Roberto.")
        identity_id = expression
    item = policy["identities"][identity_id]
    return {"id": identity_id, "mode": item["mode"],
            "reference_path": item["reference_path"], "reference_sha256": item["reference_sha256"]}


def validate_locked_portrait(root, identity):
    root = Path(root).resolve()
    policy = json.loads((root / "worker/presenter-identity.json").read_text(encoding="utf-8"))
    item = policy["identities"].get(identity.get("id"))
    expected = ({"id": identity["id"], "mode": "locked_asset",
                 "reference_path": item["reference_path"], "reference_sha256": item["reference_sha256"]}
                if item else None)
    if identity != expected or item.get("mode") != "locked_asset":
        raise ValueError("thumbnail: referência do apresentador diverge da identidade oficial.")
    portrait = (root / identity["reference_path"]).resolve()
    if not portrait.is_relative_to(root) or not portrait.is_file():
        raise ValueError("thumbnail: retrato oficial ausente ou fora do repositório.")
    if hashlib.sha256(portrait.read_bytes()).hexdigest() != identity["reference_sha256"]:
        raise ValueError("thumbnail: retrato oficial alterado; não substituir o rosto.")
    return portrait


def validate_presenter_composition(root, identity, project_id, contract_hash, image_hash):
    validate_locked_portrait(root, identity)
    receipt = Path(root) / "production" / project_id / "thumbnail-composition.json"
    if not receipt.is_file():
        raise ValueError("thumbnail: falta recibo da composição com o rosto fixo.")
    data = json.loads(receipt.read_text(encoding="utf-8"))
    expected = {"version": "locked-presenter-cover-v1", "project_id": project_id,
                "contract_sha256": contract_hash, "identity_id": identity["id"],
                "portrait_sha256": identity["reference_sha256"], "image_sha256": image_hash}
    if any(data.get(key) != value for key, value in expected.items()):
        raise ValueError("thumbnail: composição não corresponde ao rosto/capa/contrato aprovados.")
    if (data.get("portrait_side") not in ("left", "right")
        or data.get("headline_position") not in ("upper", "middle", "lower")
        or data.get("portrait_size") not in ("compact", "standard", "close")):
        raise ValueError("thumbnail: composição do retrato inválida.")
    background = (Path(root) / str(data.get("background_path", ""))).resolve()
    if (not background.is_relative_to(Path(root).resolve()) or not background.is_file()
        or hashlib.sha256(background.read_bytes()).hexdigest() != data.get("background_sha256")):
        raise ValueError("thumbnail: fundo alterado depois da composição.")
    return receipt
