import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import azure.cognitiveservices.speech as speechsdk

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


def inject_bookmark_tokens(text: str, beats: list[dict]) -> tuple[str, dict[str, dict]]:
    positions: list[tuple[int, str]] = []
    metadata: dict[str, dict] = {}

    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            continue

        anchor = str(beat.get("anchor") or "").strip()
        if not anchor:
            continue

        occurrences = text.count(anchor)
        if occurrences != 1:
            raise RuntimeError(
                f"Anchor visual precisa aparecer exatamente uma vez na narração. "
                f"Recebido {occurrences} ocorrência(s): {anchor!r}"
            )

        mark = f"beat-{index}"
        positions.append((text.index(anchor), mark))
        metadata[mark] = {
            "beat_index": index,
            "anchor": anchor,
        }

    if not positions:
        return text, metadata

    positions.sort(key=lambda item: item[0])
    chunks: list[str] = []
    cursor = 0

    for position, mark in positions:
        chunks.append(text[cursor:position])
        chunks.append(f"ODEBOOKMARK{mark.replace('-', '')}ODE")
        cursor = position

    chunks.append(text[cursor:])
    return "".join(chunks), metadata


def restore_bookmarks(rendered: str, bookmark_metadata: dict[str, dict]) -> str:
    for mark in bookmark_metadata:
        token = f"ODEBOOKMARK{mark.replace('-', '')}ODE"
        rendered = rendered.replace(token, f'<bookmark mark="{mark}"/>')
    return rendered


def build_ssml(
    text: str,
    voice: str,
    tts: dict,
    beats: list[dict] | None = None,
) -> tuple[str, dict[str, dict]]:
    base_rate = percent_value(tts.get("rate", DEFAULT_TTS_RATE), 0)
    base_pitch = percent_value(tts.get("pitch", DEFAULT_TTS_PITCH), 0)
    pause_ms = max(90, min(240, int(tts.get("pause_ms", 120))))

    marked_text, bookmark_metadata = inject_bookmark_tokens(text, beats or [])
    sentences = split_sentences(marked_text)
    rendered = []

    for index, sentence in enumerate(sentences):
        words = sentence.split()
        rate = base_rate
        pitch = base_pitch

        if sentence.endswith("?"):
            pitch += 1
            rate -= 1
        elif len(words) <= 7:
            rate += 1
        elif index % 3 == 1:
            rate += 1
        elif index % 3 == 2:
            rate -= 1

        sentence_xml = render_pronunciations(sentence, tts)
        sentence_xml = restore_bookmarks(sentence_xml, bookmark_metadata)

        # A voz já é pt-BR. Evitamos envolver bookmarks em <lang>, pois o
        # serviço tem histórico de inconsistências de eventos nesse cenário.
        rendered.append(
            f'<s><prosody rate="{percent_text(rate)}" '
            f'pitch="{percent_text(pitch)}">{sentence_xml}</prosody></s>'
        )

        if index < len(sentences) - 1:
            extra = 35 if sentence.endswith("?") else 0
            rendered.append(f'<break time="{pause_ms + extra}ms"/>')

    body = "\n      ".join(rendered)
    ssml = f"""<speak version="1.0"
  xmlns="http://www.w3.org/2001/10/synthesis"
  xml:lang="pt-BR">
  <voice xml:lang="pt-BR" name="{voice}">
      {body}
  </voice>
</speak>"""
    return ssml, bookmark_metadata


def synthesize(
    text: str,
    output: Path,
    key: str,
    region: str,
    voice: str,
    tts: dict | None = None,
    beats: list[dict] | None = None,
) -> list[dict]:
    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
    )

    audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output))
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )

    ssml, bookmark_metadata = build_ssml(
        text,
        voice,
        tts or {},
        beats=beats or [],
    )
    reached: dict[str, float] = {}

    def on_bookmark(evt) -> None:
        mark = str(evt.text)
        reached[mark] = round(float(evt.audio_offset) / 10_000_000, 4)

    synthesizer.bookmark_reached.connect(on_bookmark)
    result = synthesizer.speak_ssml_async(ssml).get()

    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        details = getattr(result, "cancellation_details", None)
        detail_text = getattr(details, "error_details", None) or str(details or result.reason)
        raise RuntimeError(f"Falha no Azure Speech SDK: {detail_text}")

    expected = set(bookmark_metadata)
    missing = sorted(expected - set(reached))
    if missing:
        labels = [
            bookmark_metadata[mark]["anchor"]
            for mark in missing
            if mark in bookmark_metadata
        ]
        raise RuntimeError(
            "Azure TTS não devolveu todos os bookmarks visuais. "
            f"Anchors ausentes: {labels}"
        )

    timings = []
    for mark, meta in bookmark_metadata.items():
        timings.append(
            {
                **meta,
                "mark": mark,
                "audio_offset_seconds": reached[mark],
            }
        )

    timings.sort(key=lambda item: item["beat_index"])
    return timings


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

    project_speech = payload.get("speech") or {}
    project_pronunciations = {
        str(key).lower(): str(value)
        for key, value in (project_speech.get("pronunciations") or {}).items()
        if str(key).strip() and str(value).strip()
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "voice": project_voice,
        "presenter": presenter_key,
        "rate": DEFAULT_TTS_RATE,
        "pitch": DEFAULT_TTS_PITCH,
        "output_format": "audio-48khz-192kbitrate-mono-mp3",
        "timing_mode": "azure-ssml-bookmarks",
        "project_pronunciations": project_pronunciations,
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
        scene_pronunciations = {
            str(key).lower(): str(value)
            for key, value in (tts.get("pronunciations") or {}).items()
            if str(key).strip() and str(value).strip()
        }
        if project_pronunciations or scene_pronunciations:
            tts["pronunciations"] = {
                **project_pronunciations,
                **scene_pronunciations,
            }

        narration_hash = hashlib.sha256(narration.encode("utf-8")).hexdigest()
        output = output_dir / f"{scene_id}.mp3"
        visual = scene.get("visual") or {}
        visual_beats = visual.get("beats") or []

        beat_timings = synthesize(
            narration,
            output,
            key,
            region,
            project_voice,
            tts,
            beats=visual_beats,
        )
        duration = duration_seconds(output)

        manifest["scenes"].append(
            {
                "id": scene_id,
                "scene_index": scene_index,
                "file": output.name,
                "duration_seconds": duration,
                "narration_sha256": narration_hash,
                "tts": tts,
                "beat_timings": beat_timings,
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
