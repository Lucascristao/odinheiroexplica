import argparse
import json
import math
import re
import unicodedata
from pathlib import Path


FPS = 30
SCENE_TAIL_SECONDS = 0.28
FINAL_SCENE_TAIL_SECONDS = 2.15



def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).lower())
    normalized = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", normalized).strip()


def resolve_visual_beats(scene: dict, audio_duration_seconds: float) -> list[dict]:
    visual = scene.get("visual") or {}
    beats = visual.get("beats") or []
    if not isinstance(beats, list) or not beats:
        return []

    narration = str(scene.get("narration") or "")
    normalized_narration = normalize_text(narration)
    audio_frames = max(1, math.ceil(audio_duration_seconds * FPS))
    resolved = []

    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            continue

        explicit_at = beat.get("at")
        ratio = None

        if isinstance(explicit_at, (int, float)):
            ratio = float(explicit_at)

        anchor = str(beat.get("anchor") or "").strip()
        if ratio is None and anchor and normalized_narration:
            normalized_anchor = normalize_text(anchor)
            position = normalized_narration.find(normalized_anchor)
            if position >= 0:
                ratio = position / max(1, len(normalized_narration))

        if ratio is None:
            ratio = (index + 1) / (len(beats) + 1)

        ratio = max(0.03, min(0.94, ratio))
        frame = min(audio_frames - 1, max(0, round(ratio * audio_frames)))

        resolved.append(
            {
                **beat,
                "resolved_ratio": round(ratio, 4),
                "resolved_frame": frame,
            }
        )

    resolved.sort(key=lambda item: item["resolved_frame"])

    # Evita que dois cards informativos entrem praticamente juntos.
    # Não muda a ordem editorial, apenas garante uma leitura visual mínima.
    minimum_gap = max(18, round(FPS * 0.75))
    previous = -minimum_gap
    for item in resolved:
        item["resolved_frame"] = min(
            audio_frames - 1,
            max(item["resolved_frame"], previous + minimum_gap),
        )
        previous = item["resolved_frame"]

    return resolved


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--tts-manifest", required=True)
    parser.add_argument("--audio-public-prefix", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    project = json.loads(Path(args.project).read_text(encoding="utf-8"))
    manifest = json.loads(Path(args.tts_manifest).read_text(encoding="utf-8"))

    audio_by_id = {item["id"]: item for item in manifest["scenes"]}

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
            float(audio["duration_seconds"]),
        )
        scene_with_resolved_visual = {
            **scene,
            "visual": {
                **(scene.get("visual") or {}),
                "beats": resolved_beats,
            },
        }

        output_scenes.append(
            {
                **scene_with_resolved_visual,
                "id": scene_id,
                "scene_index": scene_index,
                "start_frame": cursor,
                "duration_frames": duration_frames,
                "audio_duration_seconds": audio["duration_seconds"],
                "audio_file": (
                    f"{args.audio_public_prefix.rstrip('/')}/{audio['file']}"
                ),
            }
        )
        cursor += duration_frames

    payload = {
        "project_id": project.get("project_id", "project"),
        "title": project.get("title", "O Dinheiro Explica"),
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
