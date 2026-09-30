import argparse
import json
import math
import re
import unicodedata
import copy
from pathlib import Path


FPS = 30
SCENE_TAIL_SECONDS = 0.28
FINAL_SCENE_TAIL_SECONDS = 1.9

REAL_BOOKMARK_SOURCES = {"azure-bookmark", "tts-bookmark"}
ESTIMATED_ANCHOR_SOURCES = {"estimated-text-alignment", "text-fallback"}



def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).lower())
    normalized = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", normalized).strip()


def resolve_visual_beats(
    scene: dict,
    audio: dict,
) -> list[dict]:
    visual = scene.get("visual") or {}
    beats = visual.get("beats") or []
    if not isinstance(beats, list) or not beats:
        return []

    audio_duration_seconds = float(audio["duration_seconds"])
    audio_frames = max(1, math.ceil(audio_duration_seconds * FPS))
    timing_by_index = {
        int(item["beat_index"]): item
        for item in (audio.get("beat_timings") or [])
        if isinstance(item, dict) and "beat_index" in item
    }

    narration = str(scene.get("narration") or "")
    normalized_narration = normalize_text(narration)
    resolved = []

    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            continue

        explicit_at = beat.get("at")
        frame = None
        ratio = None
        timing_source = None

        if index in timing_by_index:
            seconds = float(timing_by_index[index]["audio_offset_seconds"])
            frame = min(audio_frames - 1, max(0, round(seconds * FPS)))
            ratio = frame / max(1, audio_frames - 1)
            timing_source = timing_by_index[index].get("timing_source") or "estimated-text-alignment"
            # Manifests antigos chamavam a estimativa textual de bookmark Gemini.
            if timing_source == "gemini-bookmark":
                timing_source = "estimated-text-alignment"

        elif isinstance(explicit_at, (int, float)):
            ratio = max(0.0, min(1.0, float(explicit_at)))
            frame = min(audio_frames - 1, max(0, round(ratio * audio_frames)))
            timing_source = "explicit-at"

        else:
            anchor = str(beat.get("anchor") or "").strip()
            if anchor and normalized_narration:
                normalized_anchor = normalize_text(anchor)
                position = normalized_narration.find(normalized_anchor)
                if position >= 0:
                    ratio = position / max(1, len(normalized_narration))
                    frame = min(
                        audio_frames - 1,
                        max(0, round(ratio * audio_frames)),
                    )
                    timing_source = "text-fallback"

        if frame is None or ratio is None:
            ratio = (index + 1) / (len(beats) + 1)
            frame = min(audio_frames - 1, max(0, round(ratio * audio_frames)))
            timing_source = "distributed-fallback"

        resolved.append(
            {
                **beat,
                "resolved_ratio": round(ratio, 4),
                "resolved_frame": frame,
                "timing_source": timing_source,
            }
        )

    resolved.sort(key=lambda item: item["resolved_frame"])

    # Tempos estimados recebem proteção contra colisão. Bookmarks medidos pelo
    # TTS preservam o offset fornecido pelo serviço.
    minimum_gap = max(12, round(FPS * 0.35))
    previous = -minimum_gap
    for item in resolved:
        if item.get("timing_source") not in REAL_BOOKMARK_SOURCES:
            item["resolved_frame"] = min(
                audio_frames - 1,
                max(item["resolved_frame"], previous + minimum_gap),
            )
        previous = item["resolved_frame"]

    return resolved


def validate_stage_timing(scene: dict, resolved_beats: list[dict], scene_id: str) -> None:
    beats = ((scene.get("visual") or {}).get("beats") or [])
    if len(resolved_beats) != len(beats):
        raise RuntimeError(f"Palco persistente tem beats inválidos: {scene_id}")

    narration = normalize_text(scene.get("narration") or "")
    previous_position = -1
    for beat in beats:
        anchor = normalize_text(beat.get("anchor") or "")
        if not anchor or narration.count(anchor) != 1:
            raise RuntimeError(f"Palco persistente exige âncora única na narração: {scene_id}")
        position = narration.find(anchor)
        if position <= previous_position:
            raise RuntimeError(f"Âncoras fora da ordem da narração: {scene_id}")
        previous_position = position

    for beat in resolved_beats:
        if beat.get("timing_source") not in REAL_BOOKMARK_SOURCES | ESTIMATED_ANCHOR_SOURCES:
            raise RuntimeError(f"Palco persistente exige tempo estimado por âncora ou bookmark real: {scene_id}")
    frames = [beat["resolved_frame"] for beat in resolved_beats]
    if len(frames) != len(set(frames)):
        raise RuntimeError(f"Eventos visuais simultâneos em {scene_id}; agrupe as mudanças no mesmo beat.")


def require_gemini_manifest(manifest: dict) -> None:
    scenes = manifest.get("scenes") or []
    engine = "google-gemini-tts"
    if not scenes or manifest.get("engine") != engine:
        raise RuntimeError("Render diário exige manifesto de áudio exclusivamente Gemini.")
    primary_model = "gemini-3.8-flash-tts"
    fallback_model = "gemini-3.1-flash-tts-preview"
    fallback_treatment = "charon-3.1-to-3.8-eq-v1"
    models = {item.get("model") for item in scenes}
    voices = {item.get("voice") for item in scenes}
    if (
        any(item.get("engine") != engine for item in scenes)
        or not models.issubset({primary_model, fallback_model})
        or len(voices) != 1
        or None in voices
        or manifest.get("model") != primary_model
        or manifest.get("voice") not in voices
        or (
            fallback_model in models
            and (
                manifest.get("fallback_model") != fallback_model
                or manifest.get("voice") != "Charon"
            )
        )
        or any(
            item.get("voice_treatment", "none") != (
                fallback_treatment if item.get("model") == fallback_model else "none"
            )
            for item in scenes
        )
    ):
        raise RuntimeError("Manifesto contém outro motor, modelo ou voz em alguma cena.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--tts-manifest", required=True)
    parser.add_argument("--audio-public-prefix", required=True)
    parser.add_argument("--visual-assets-manifest")
    parser.add_argument("--require-gemini", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    project = json.loads(Path(args.project).read_text(encoding="utf-8"))
    manifest = json.loads(Path(args.tts_manifest).read_text(encoding="utf-8"))
    if args.require_gemini:
        require_gemini_manifest(manifest)

    audio_by_id = {item["id"]: item for item in manifest["scenes"]}

    visual_assets_by_id = {}
    if args.visual_assets_manifest:
        visual_manifest_path = Path(args.visual_assets_manifest)
        if visual_manifest_path.exists():
            visual_manifest = json.loads(
                visual_manifest_path.read_text(encoding="utf-8")
            )
            visual_assets_by_id = {
                str(item["id"]): item
                for item in (visual_manifest.get("assets") or [])
            }

    output_scenes = []
    cursor = 0
    scenes = project.get("scenes") or project.get("script", {}).get("scenes", [])

    for position, scene in enumerate(scenes):
        scene_index = scene.get("scene_index", scene.get("index", position))
        scene_id = str(scene.get("id") or f"scene-{int(scene_index):02d}")
        audio = audio_by_id.get(scene_id)
        if audio is None:
            raise RuntimeError(f"Áudio não encontrado para {scene_id}")

        tail_seconds = (
            FINAL_SCENE_TAIL_SECONDS
            if position == len(scenes) - 1
            else SCENE_TAIL_SECONDS
        )
        duration_seconds = float(audio["duration_seconds"]) + tail_seconds
        duration_frames = max(30, math.ceil(duration_seconds * FPS))
        resolved_beats = resolve_visual_beats(
            scene,
            audio,
        )
        if (scene.get("visual") or {}).get("stage"):
            validate_stage_timing(scene, resolved_beats, scene_id)
        resolved_beats_with_assets = []
        for beat in resolved_beats:
            asset_id = str(beat.get("asset_id") or "").strip()
            if asset_id and asset_id in visual_assets_by_id:
                resolved_beats_with_assets.append(
                    {
                        **beat,
                        "asset_file": visual_assets_by_id[asset_id]["public_file"],
                        "asset_type": visual_assets_by_id[asset_id].get("type"),
                    }
                )
            else:
                resolved_beats_with_assets.append(beat)

        scene_with_resolved_visual = {
            **scene,
            "visual": {
                **(scene.get("visual") or {}),
                "beats": resolved_beats_with_assets,
            },
        }
        stage = copy.deepcopy((scene.get("visual") or {}).get("stage"))
        if stage:
            for element in stage.get("elements", []):
                asset_id = element.get("asset_id")
                if asset_id:
                    if asset_id not in visual_assets_by_id:
                        raise RuntimeError(f"Asset de palco não preparado: {asset_id}")
                    element["asset_file"] = visual_assets_by_id[asset_id]["public_file"]
                    if element.get("kind") == "source_excerpt":
                        prepared = visual_assets_by_id[asset_id]
                        if prepared.get("type") != "source_excerpt" or not prepared.get("width") or not prepared.get("height"):
                            raise RuntimeError(f"Recorte sem dimensões ou tipo documental: {asset_id}")
                        element["asset_width"] = prepared["width"]
                        element["asset_height"] = prepared["height"]
            scene_with_resolved_visual["visual"]["stage"] = stage

        output_scenes.append(
            {
                **scene_with_resolved_visual,
                "id": scene_id,
                "scene_index": scene_index,
                "start_frame": cursor,
                "duration_frames": duration_frames,
                "audio_duration_seconds": audio["duration_seconds"],
                "audio_model": audio.get("model"),
                "audio_voice": audio.get("voice"),
                "audio_voice_treatment": audio.get("voice_treatment", "none"),
                "audio_fallback_reason": audio.get("fallback_reason"),
                "audio_file": (
                    f"{args.audio_public_prefix.rstrip('/')}/{audio['file']}"
                ),
            }
        )
        cursor += duration_frames

    payload = {
        "project_id": project.get("project_id", "project"),
        "title": project.get("title", "O Dinheiro Explica"),
        "visual_direction": project.get("visual_direction") or {},
        "fps": FPS,
        "duration_in_frames": cursor,
        "voice": manifest["voice"],
        "scenes": output_scenes,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Render input criado: {len(output_scenes)} cenas, "
        f"{cursor} frames, {cursor / FPS:.2f}s"
    )


if __name__ == "__main__":
    main()
