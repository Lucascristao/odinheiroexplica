"""Verify Gemini Live narration and copy it byte-for-byte for delivery."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from tts_config import PRIMARY_TTS_MODEL

VERSION = "gemini-live-passthrough-v1"
ENGINE = "google-gemini-live"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def duration_seconds(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-manifest", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-manifest", required=True)
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    input_manifest = json.loads(
        Path(args.input_manifest).read_text(encoding="utf-8")
    )
    scenes = input_manifest.get("scenes") or []
    if not scenes:
        raise RuntimeError("Manifesto sem cenas.")

    models = {scene.get("model") for scene in scenes}
    voices = {scene.get("voice") for scene in scenes}
    if models != {PRIMARY_TTS_MODEL} or len(voices) != 1 or None in voices:
        raise RuntimeError(
            "Gemini Live passthrough exige um único modelo e uma única voz."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    result = copy.deepcopy(input_manifest)
    delivered = []
    for scene in scenes:
        source = (source_dir / scene["file"]).resolve()
        if (
            not source.is_relative_to(source_dir)
            or not source.is_file()
            or source.suffix.lower() != ".wav"
        ):
            raise RuntimeError(f"Áudio Live inválido: {scene.get('id')}")

        destination = output_dir / source.name
        shutil.copy2(source, destination)
        source_hash = sha256(source)
        output_hash = sha256(destination)
        if source_hash != output_hash:
            raise RuntimeError(
                f"Passthrough alterou bytes da cena {scene.get('id')}."
            )

        actual_duration = duration_seconds(destination)
        registered = float(scene["duration_seconds"])
        if abs(actual_duration - registered) > 0.05:
            raise RuntimeError(
                f"Duração diverge no passthrough: {scene.get('id')}."
            )

        item = copy.deepcopy(scene)
        item["postprocess"] = {
            "version": VERSION,
            "mode": "byte-identical-passthrough",
            "effects_applied": False,
            "eq_applied": False,
            "gain_applied": False,
            "limiter_applied": False,
            "compressor_applied": False,
            "resampled": False,
            "reencoded": False,
            "source_sha256": source_hash,
            "output_sha256": output_hash,
            "byte_identical": True,
        }
        delivered.append(item)
        print(
            f"{scene['id']}: Gemini Live passthrough byte-identical; "
            "nenhum efeito aplicado.",
            flush=True,
        )

    result["scenes"] = delivered
    result["postprocess"] = {
        "version": VERSION,
        "mode": "byte-identical-passthrough",
        "effects_applied": False,
        "model": PRIMARY_TTS_MODEL,
        "voice": next(iter(voices)),
        "model_transition_count": 0,
        "rule": "Gemini Live audio is delivered without DSP",
    }
    output_manifest = Path(args.output_manifest)
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
