"""Create silent, estimated scene audio for a visual-only Remotion preview.

This is deliberately separate from synthesize_scenes.py. Its manifest is marked
preview_only and must never be accepted by a production render using
build_render_input.py --require-gemini.
"""

import argparse
import json
import re
import subprocess
from pathlib import Path

from build_render_input import normalize_text


WORDS_PER_MINUTE = 145
MINIMUM_SCENE_SECONDS = 7.0
MINIMUM_BEAT_GAP_SECONDS = 0.5


def estimated_duration(narration: str) -> float:
    words = len(re.findall(r"\b\w+\b", narration, flags=re.UNICODE))
    if words == 0:
        raise RuntimeError("A prévia precisa de narração escrita em todas as cenas.")
    return round(max(MINIMUM_SCENE_SECONDS, words * 60 / WORDS_PER_MINUTE + 1.0), 3)


def estimated_beat_timings(narration: str, beats: list[dict], duration: float) -> list[dict]:
    normalized_narration = normalize_text(narration)
    previous_offset = -MINIMUM_BEAT_GAP_SECONDS
    timings = []

    for index, beat in enumerate(beats):
        anchor = str(beat.get("anchor") or "").strip()
        normalized_anchor = normalize_text(anchor)
        position = normalized_narration.find(normalized_anchor) if normalized_anchor else -1
        if position < 0 or normalized_narration.count(normalized_anchor) != 1:
            raise RuntimeError(f"Beat {index}: âncora ausente ou repetida na narração.")

        midpoint = position + len(normalized_anchor) / 2
        offset = max(0.2, min(duration - 0.2, midpoint / len(normalized_narration) * duration))
        offset = max(offset, previous_offset + MINIMUM_BEAT_GAP_SECONDS)
        if offset >= duration - 0.1:
            raise RuntimeError(f"Beat {index}: duração estimada insuficiente para as âncoras.")

        timings.append({
            "beat_index": index,
            "anchor": anchor,
            "audio_offset_seconds": round(offset, 4),
            "timing_source": "estimated-text-alignment",
        })
        previous_offset = offset

    return timings


def write_silent_mp3(path: Path, duration: float) -> None:
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=24000",
            "-t", str(duration), "-codec:a", "libmp3lame", "-b:a", "16k", str(path),
        ],
        check=True,
    )


def create_preview(project: dict, output_dir: Path) -> dict:
    scenes = project.get("scenes") or project.get("script", {}).get("scenes", [])
    if not scenes:
        raise RuntimeError("Nenhuma cena para a prévia visual.")

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "preview_only": True,
        "engine": "silent-placeholder",
        "model": "none",
        "voice": "silence",
        "timing_basis": f"estimated-text-alignment-{WORDS_PER_MINUTE}-wpm",
        "notice": "Áudio silencioso; durações e beats estimados, sem Gemini TTS.",
        "project_id": project.get("project_id", "project"),
        "scenes": [],
        "total_duration_seconds": 0.0,
    }

    ids = set()
    for position, scene in enumerate(scenes):
        scene_index = scene.get("scene_index", scene.get("index", position))
        scene_id = str(scene.get("id") or f"scene-{int(scene_index):02d}")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", scene_id) or scene_id in ids:
            raise RuntimeError(f"ID de cena inválido ou duplicado: {scene_id}")
        ids.add(scene_id)

        narration = str(scene.get("narration") or "").strip()
        duration = estimated_duration(narration)
        beats = (scene.get("visual") or {}).get("beats") or []
        beat_timings = estimated_beat_timings(narration, beats, duration)
        filename = f"{scene_id}.mp3"
        write_silent_mp3(output_dir / filename, duration)
        manifest["scenes"].append({
            "id": scene_id,
            "scene_index": scene_index,
            "file": filename,
            "duration_seconds": duration,
            "engine": "silent-placeholder",
            "model": "none",
            "voice": "silence",
            "beat_timings": beat_timings,
        })
        manifest["total_duration_seconds"] += duration

    manifest["total_duration_seconds"] = round(manifest["total_duration_seconds"], 3)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    project = json.loads(Path(args.project).read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir)
    manifest = create_preview(project, output_dir)
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Prévia visual: {len(manifest['scenes'])} cenas silenciosas, "
        f"{manifest['total_duration_seconds']:.1f}s estimados; sem Gemini TTS."
    )


if __name__ == "__main__":
    main()
