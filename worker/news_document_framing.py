"""Source-camera views derived from measured proof, without invented marks."""


def contextual_proof_views(proof: dict) -> tuple[dict, dict]:
    def expanded(padding: float, minimum_height: float) -> dict:
        width = min(100.0, float(proof["width"]) + padding * 2)
        height = min(100.0, max(minimum_height, float(proof["height"]) + padding * 2))
        x = max(0.0, min(100.0 - width, float(proof["x"]) + float(proof["width"]) / 2 - width / 2))
        y = max(0.0, min(100.0 - height, float(proof["y"]) + float(proof["height"]) / 2 - height / 2))
        return {"x": x, "y": y, "width": width, "height": height}

    # Keep adjacent paragraphs and article structure, rather than making a
    # single line a thin card. Both views always contain the complete proof.
    return expanded(8, 58), expanded(3, 40)


def apply_news_document_views(element: dict, prepared: dict, beats: list[dict]) -> None:
    proof = prepared.get("proof_region")
    if not proof or not beats or any(beat.get("view") for beat in beats):
        return
    if element.get("document_context_seconds") is None:
        # Preserve historical resumes and non-news source framing.
        beats[0]["view"] = dict(proof)
        return
    wide, close = contextual_proof_views(proof)
    for index, beat in enumerate(beats):
        # Each speech cue revisits context or approaches the verified passage.
        # No arrows/highlights or unverified crop targets are synthesized.
        beat["view"] = dict(wide if index % 2 == 0 else close)
