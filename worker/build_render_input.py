import argparse
import json
import math
from pathlib import Path


FPS = 30
SCENE_TAIL_SECONDS = 0.28
FINAL_SCENE_TAIL_SECONDS = 2.15


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

        output_scenes.append(
            {
                **scene,
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
