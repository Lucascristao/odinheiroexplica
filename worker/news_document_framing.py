"""Source-camera views derived from measured proof, without invented marks."""
import re
import copy
import math


def apply_documentary_sequence(prepared, beats, candidates):
    """Cut between relevant authentic captures, then show and mark their proof.

    Coordinates come only from source capture provenance, never a language model.
    """
    current = prepared
    last_change = -3
    available = [a for a in candidates if a.get('type') == 'source_excerpt' and a.get('proof_region')
                 and a.get('expected_text') and a.get('public_file')]
    for index, beat in enumerate(beats):
        terms = set(re.findall(r'\w{5,}', (beat.get('anchor', '') + ' ' + beat.get('headline', '')).casefold()))
        scored = [(len(terms & set(re.findall(r'\w{5,}', a['expected_text'].casefold()))), a) for a in available]
        scored.sort(key=lambda row: row[0], reverse=True)
        changed = False
        if scored and scored[0][0] >= 2 and scored[0][1]['id'] != current['id'] and index-last_change >= 3:
            current, changed, last_change = scored[0][1], True, index
        proof = current.get('proof_region')
        if not proof:
            continue
        wide, close = contextual_proof_views(proof)
        phase = 0 if changed else (index-last_change) % 4
        # Establish, approach, read marked evidence, restore article context.
        # This is not the old endless two-view oscillation over the headline.
        beat['view'] = dict({'x': 0, 'y': 0, 'width': 100, 'height': 100} if phase == 0 else wide if phase in (1, 3) else close)
        can_mark = all(isinstance(proof.get(k), (int, float)) and math.isfinite(proof[k]) for k in ('x', 'y', 'width', 'height')) and (
            proof['x'] >= 0 and proof['y'] >= 0 and proof['width'] >= 1 and proof['height'] >= 1
            and proof['x'] + proof['width'] <= 100 and proof['y'] + proof['height'] <= 100)
        annotation = {'id': 'auto-source-proof', 'style': 'highlight', 'region': dict(proof)}
        beat['document_shot'] = {'asset_id': current['id'], 'asset_file': current['public_file'],
            'asset_width': current['width'], 'asset_height': current['height'], 'annotations': [annotation] if can_mark else []}
        beat['mark_ids'] = ['auto-source-proof'] if phase == 2 and can_mark else []
        beat['motion_seconds'] = .85 if phase == 1 else .45



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


def apply_news_document_views(element: dict, prepared: dict, beats: list[dict], candidates=()) -> None:
    proof = prepared.get("proof_region")
    if not proof or not beats or any(beat.get("view") for beat in beats):
        return
    if element.get("document_context_seconds") is None:
        # Preserve historical resumes and non-news source framing.
        beats[0]["view"] = dict(proof)
        return
    if candidates:
        original = copy.deepcopy(beats)
        try:
            apply_documentary_sequence(prepared, beats, candidates)
            for beat in beats:
                shot = beat.get('document_shot') or {}
                if (not re.fullmatch(r'generated-assets/[A-Za-z0-9._-]+', shot.get('asset_file', ''))
                        or not shot.get('asset_width') or not shot.get('asset_height')):
                    raise ValueError('Optional documentary sequence lacks prepared image metadata')
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            beats[:] = original
            for beat in beats:
                beat['view'] = {'x': 0, 'y': 0, 'width': 100, 'height': 100}
            print('NEWS_VISUAL_ADVISORY: simple authentic page fallback after', type(error).__name__, flush=True)
        return
    wide, close = contextual_proof_views(proof)
    for index, beat in enumerate(beats):
        # Each speech cue revisits context or approaches the verified passage.
        # No arrows/highlights or unverified crop targets are synthesized.
        beat["view"] = dict(wide if index % 2 == 0 else close)
