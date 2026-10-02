import argparse
import json
import math
import re
import unicodedata
import copy
import hashlib
import subprocess
from pathlib import Path

from tts_config import TTS_MODEL_CASCADE, PRESENTER_VOICES, VOICE_POLICY_VERSION, project_speech_fingerprint, voice_policy_fingerprint, scene_direction_fingerprint
from editorial_project import normalize_project
from editorial_caption_timing import build_caption_timing


FPS = 30
SCENE_TAIL_SECONDS = 0.28
FINAL_SCENE_TAIL_SECONDS = 1.9


def boundary_padding(audio: dict, following: dict | None, next_scene: dict | None = None) -> dict:
    """Reduce extra timeline silence only; preserve every raw audio sample."""
    if following is None:
        return {"padding_seconds": FINAL_SCENE_TAIL_SECONDS, "reason": "final-card-hold"}
    current_activity = audio.get("audio_activity") or {}
    next_activity = following.get("audio_activity") or {}
    if not current_activity.get("has_activity") or not next_activity.get("has_activity"):
        return {"padding_seconds": SCENE_TAIL_SECONDS, "reason": "activity-unavailable-kept-legacy-padding"}
    tail = float(current_activity.get("tail_seconds", 0))
    lead = float(next_activity.get("lead_seconds", 0))
    if not all(math.isfinite(v) and v >= 0 for v in (tail, lead)):
        raise ValueError("Bordas de atividade vocal inválidas.")
    delivery = ((next_scene or {}).get("tts") or {}).get("delivery")
    # This caps added silence, not speech speed or intrinsic pauses.
    budget = .8 if delivery in ("contrast", "question") else .65
    natural = tail + lead
    padding = round(min(SCENE_TAIL_SECONDS, max(0.0, budget-natural)), 4)
    return {"padding_seconds": padding, "natural_gap_seconds": round(natural, 4), "estimated_activity_gap_seconds": round(natural+padding, 4), "reason": "reduced-extra-padding-for-natural-silence" if padding < SCENE_TAIL_SECONDS else "kept-extra-padding", "measurement_caveat": "energy activity estimate; original WAV remains intact"}

REAL_BOOKMARK_SOURCES = {"azure-bookmark", "tts-bookmark", "audio-word-alignment"}
ESTIMATED_ANCHOR_SOURCES = {"estimated-text-alignment", "text-fallback", "estimated-between-audio-anchors"}



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
    engine = "google-gemini-live"
    if not scenes or manifest.get("engine") != engine:
        raise RuntimeError("Render diário exige manifesto de áudio exclusivamente Gemini.")

    primary_model = TTS_MODEL_CASCADE[0]
    allowed_models = set(TTS_MODEL_CASCADE)

    models = {item.get("model") for item in scenes}
    voices = {item.get("voice") for item in scenes}
    configured_fallbacks = manifest.get("fallback_models")
    if configured_fallbacks is None:
        single = manifest.get("fallback_model")
        configured_fallbacks = [single] if single else []
    configured_fallbacks = [model for model in configured_fallbacks if model]

    if (
        any(item.get("engine") != engine for item in scenes)
        or not models.issubset(allowed_models)
        or len(voices) != 1
        or None in voices
        or manifest.get("model") != primary_model
        or manifest.get("voice") not in voices
        or not voices.issubset(set(PRESENTER_VOICES.values()))
        or configured_fallbacks
        or models != {primary_model}
        or any(
            item.get("voice_treatment", "none") != "none"
            for item in scenes
        )
    ):
        raise RuntimeError("Manifesto contém outro motor, modelo ou voz em alguma cena.")


def validate_audio_integrity(scene: dict, audio: dict, audio_dir: Path, project: dict | None = None) -> None:
    narration_hash = hashlib.sha256(str(scene["narration"]).strip().encode("utf-8")).hexdigest()
    if audio.get("narration_sha256") != narration_hash:
        raise RuntimeError(f"Áudio não corresponde à narração atual: {audio['id']}")
    if audio.get("voice_policy_version") != VOICE_POLICY_VERSION or audio.get("voice_policy_fingerprint") != voice_policy_fingerprint(audio["model"], audio["voice"]):
        raise RuntimeError(f"Áudio não corresponde à política vocal atual: {audio['id']}")
    if project is not None and audio.get("speech_profile_fingerprint") != project_speech_fingerprint(project):
        raise RuntimeError(f"Áudio não corresponde às pronúncias atuais: {audio['id']}")
    if audio.get("scene_direction_fingerprint") != scene_direction_fingerprint(scene):
        raise RuntimeError(f"Áudio não corresponde à direção vocal da cena: {audio['id']}")
    root = audio_dir.resolve()
    path = (root / audio["file"]).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise RuntimeError(f"Áudio ausente ou caminho inválido: {audio['id']}")
    expected = (audio.get("postprocess") or {}).get("output_sha256")
    if not expected or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise RuntimeError(f"Hash do áudio processado diverge: {audio['id']}")
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], check=True, capture_output=True, text=True)
    duration = float(probe.stdout.strip())
    registered = float(audio["duration_seconds"])
    if not math.isfinite(duration) or not math.isfinite(registered) or duration <= 0 or registered <= 0 or abs(duration - registered) > .01:
        raise RuntimeError(f"Duração do áudio processado diverge: {audio['id']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--tts-manifest", required=True)
    parser.add_argument("--audio-public-prefix", required=True)
    parser.add_argument("--audio-dir")
    parser.add_argument("--visual-assets-manifest")
    parser.add_argument("--require-gemini", action="store_true")
    parser.add_argument("--require-voice-continuity", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    project = normalize_project(json.loads(Path(args.project).read_text(encoding="utf-8")))
    manifest = json.loads(Path(args.tts_manifest).read_text(encoding="utf-8"))
    if args.require_gemini:
        require_gemini_manifest(manifest)
    if args.require_voice_continuity:
        version = "gemini-live-passthrough-v1"
        if manifest.get("postprocess", {}).get("version") != version or any(
            scene.get("postprocess", {}).get("version") != version
            for scene in manifest.get("scenes", [])
        ):
            raise RuntimeError("Render diário exige continuidade de voz processada em todas as cenas.")

    audio_by_id = {item["id"]: item for item in manifest["scenes"]}
    if len(audio_by_id) != len(manifest["scenes"]):
        raise RuntimeError("Manifesto contém IDs de áudio duplicados.")
    audio_dir = Path(args.audio_dir or (Path("public") / args.audio_public_prefix))

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
        if args.require_voice_continuity:
            validate_audio_integrity(scene, audio, audio_dir, project)

        next_scene = scenes[position+1] if position+1 < len(scenes) else None
        next_audio = audio_by_id.get(next_scene["id"]) if next_scene else None
        gap = boundary_padding(audio, next_audio, next_scene)
        tail_seconds = gap["padding_seconds"]
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

        caption_words, caption_timing = ([], None)
        caption_settings = (stage or {}).get("captions")
        if isinstance(caption_settings, dict) and caption_settings.get("enabled", True):
            caption_words, caption_timing = build_caption_timing(
                scene, audio, FPS,
                {**((project.get("speech") or {}).get("pronunciations") or {}),
                 **((scene.get("tts") or {}).get("pronunciations") or {})},
            )
        activity = audio.get("audio_activity") or {}
        scene_rms = activity.get("rms_dbfs")
        if isinstance(scene_rms, (int, float)) and math.isfinite(scene_rms) and scene_rms > -60:
            target_rms = -17.5
            diff_db = target_rms - float(scene_rms)
            vol_mult = round(float(min(1.8, max(0.6, 10.0 ** (diff_db / 20.0)))), 4)
        else:
            vol_mult = 1.0

        output_scenes.append(
            {
                **scene_with_resolved_visual,
                "id": scene_id,
                "scene_index": scene_index,
                "start_frame": cursor,
                "duration_frames": duration_frames,
                "audio_duration_seconds": audio["duration_seconds"],
                "audio_volume_multiplier": vol_mult,
                "audio_model": audio.get("model"),
                "audio_voice": audio.get("voice"),
                "audio_voice_treatment": audio.get("voice_treatment", "none"),
                "audio_fallback_reason": audio.get("fallback_reason"),
                "audio_postprocess": audio.get("postprocess"),
                "audio_alignment": audio.get("alignment"),
                "audio_captions": caption_words,
                "caption_timing": caption_timing,
                "audio_activity": audio.get("audio_activity"),
                "audio_boundary": gap,
                "audio_scene_direction_fingerprint": audio.get("scene_direction_fingerprint"),
                "audio_voice_policy_fingerprint": audio.get("voice_policy_fingerprint"),
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
        "voice_postprocess": manifest.get("postprocess"),
        "voice_alignment": manifest.get("alignment"),
        "voice_policy_version": manifest.get("voice_policy_version"),
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
