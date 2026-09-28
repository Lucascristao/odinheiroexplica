import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import requests

from tts_config import (
    DEFAULT_PRESENTER,
    DEFAULT_TTS_PITCH,
    DEFAULT_TTS_RATE,
    DEFAULT_TTS_VOICE,
    GLOBAL_PRONUNCIATIONS,
    PRESENTER_VOICES,
)


def duration_seconds(path: Path) -> float:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return round(float(completed.stdout.strip()), 3)


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def percent_value(value: str, default: int = 0) -> int:
    match = re.fullmatch(r"([+-]?\d+)%", str(value).strip())
    return int(match.group(1)) if match else default


def percent_text(value: int) -> str:
    return f"{value:+d}%" if value else "0%"


def render_pronunciations(text: str, tts: dict) -> str:
    pronunciations = dict(GLOBAL_PRONUNCIATIONS)
    pronunciations.update(
        {
            str(key).lower(): str(value)
            for key, value in (tts.get("pronunciations") or {}).items()
        }
    )

    if not pronunciations:
        return escape(text)

    terms = sorted(pronunciations, key=len, reverse=True)
    pattern = re.compile(
        r"(?<!\w)(" + "|".join(re.escape(term) for term in terms) + r")(?!\w)",
        re.IGNORECASE,
    )

    parts = []
    last = 0
    for match in pattern.finditer(text):
        parts.append(escape(text[last:match.start()]))
        spoken = pronunciations.get(match.group(0).lower(), match.group(0))
        parts.append(
            f"<sub alias={quoteattr(spoken)}>{escape(match.group(0))}</sub>"
        )
        last = match.end()

    parts.append(escape(text[last:]))
    return "".join(parts)


def build_ssml(text: str, voice: str, tts: dict) -> str:
    base_rate = percent_value(tts.get("rate", DEFAULT_TTS_RATE), 0)
    base_pitch = percent_value(tts.get("pitch", DEFAULT_TTS_PITCH), 0)
    pause_ms = max(90, min(240, int(tts.get("pause_ms", 120))))

    sentences = split_sentences(text)
    rendered = []

    for index, sentence in enumerate(sentences):
        words = sentence.split()
        rate = base_rate
        pitch = base_pitch

        # Variações mínimas de cadência para evitar leitura mecânica,
        # sem exagerar pitch ou velocidade.
        if sentence.endswith("?"):
            pitch += 1
            rate -= 1
        elif len(words) <= 7:
            rate += 1
        elif index % 3 == 1:
            rate += 1
        elif index % 3 == 2:
            rate -= 1

        rendered.append(
            f'<s><lang xml:lang="pt-BR"><prosody rate="{percent_text(rate)}" '
            f'pitch="{percent_text(pitch)}">{render_pronunciations(sentence, tts)}</prosody></lang></s>'
        )

        if index < len(sentences) - 1:
            extra = 35 if sentence.endswith("?") else 0
            rendered.append(f'<break time="{pause_ms + extra}ms"/>')

    body = "\n      ".join(rendered)
    return f"""<speak version="1.0"
  xmlns="http://www.w3.org/2001/10/synthesis"
  xml:lang="pt-BR">
  <voice xml:lang="pt-BR" name="{voice}">
      {body}
  </voice>
</speak>"""


def synthesize(
    text: str,
    output: Path,
    key: str,
    region: str,
    voice: str,
    tts: dict | None = None,
) -> None:
    endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    ssml = build_ssml(text, voice, tts or {})

    response = requests.post(
        endpoint,
        headers={
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-48khz-192kbitrate-mono-mp3",
            "User-Agent": "odinheiroexplica-scene-tts",
        },
        data=ssml.encode("utf-8"),
        timeout=90,
    )
    response.raise_for_status()
    output.write_bytes(response.content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    key = os.environ["AZURE_SPEECH_KEY"].strip()
    region = os.environ["AZURE_SPEECH_REGION"].strip()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    scenes = payload.get("scenes") or payload.get("script", {}).get("scenes", [])
    if not scenes:
        raise RuntimeError("Nenhuma cena recebida.")

    presenter = payload.get("presenter") or {}
    presenter_key = str(
        presenter.get("gender")
        or presenter.get("voice_id")
        or DEFAULT_PRESENTER
    )
    project_voice = PRESENTER_VOICES.get(presenter_key, DEFAULT_TTS_VOICE)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "voice": project_voice,
        "presenter": presenter_key,
        "rate": DEFAULT_TTS_RATE,
        "pitch": DEFAULT_TTS_PITCH,
        "output_format": "audio-48khz-192kbitrate-mono-mp3",
        "scenes": [],
        "total_duration_seconds": 0.0,
    }

    for position, scene in enumerate(scenes):
        scene_index = scene.get("scene_index", scene.get("index", position))
        scene_id = str(scene.get("id") or f"scene-{int(scene_index):02d}")
        narration = str(scene["narration"]).strip()
        if not narration:
            raise RuntimeError(f"Cena {scene_id} sem narração.")

        tts = dict(scene.get("tts") or {})
        narration_hash = hashlib.sha256(narration.encode("utf-8")).hexdigest()
        output = output_dir / f"{scene_id}.mp3"
        synthesize(narration, output, key, region, project_voice, tts)
        duration = duration_seconds(output)

        manifest["scenes"].append(
            {
                "id": scene_id,
                "scene_index": scene_index,
                "file": output.name,
                "duration_seconds": duration,
                "narration_sha256": narration_hash,
                "tts": tts,
            }
        )
        manifest["total_duration_seconds"] += duration

    manifest["total_duration_seconds"] = round(
        manifest["total_duration_seconds"], 3
    )
    Path(args.manifest).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
