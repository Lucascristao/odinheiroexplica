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
        parts.append(f"<sub alias={quoteattr(spoken)}>{escape(match.group(0))}</sub>")
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


# Editorial direction uses standard prosody, without voice-specific acting styles.
DELIVERY = {
    "hook": (1, 1, 0), "explain": (0, 0, 0),
    "contrast": (0, 0, 0), "question": (0, 1, 0),
    "closing": (0, -1, 0),
}
CUE_DELIVERY = {"emphasis": (-1, 1), "number": (-2, 0), "contrast": (0, 1)}


def build_ssml(
    text: str,
    voice: str,
    tts: dict,
    beats: list[dict] | None = None,
) -> tuple[str, dict[str, dict]]:
    delivery = tts.get("delivery", "explain")
    if delivery not in DELIVERY:
        raise RuntimeError(f"Direção de voz desconhecida: {delivery}")
    dr, dp, default_pause = DELIVERY[delivery]
    base_rate = percent_value(tts.get("rate", DEFAULT_TTS_RATE)) + dr
    base_pitch = percent_value(tts.get("pitch", DEFAULT_TTS_PITCH)) + dp
    pause_ms = max(0, min(250, int(tts.get("sentence_gap_ms", default_pause))))
    # Legacy pause_ms added silence on top of natural punctuation; no longer applied.
    # Validate anchors using the same literal contract, but emit XML events at
    # original text offsets. Tokens adjacent to a word can break pronunciation.
    _, metadata = inject_bookmark_tokens(text, beats or [])
    marks: dict[int, list[str]] = {}
    for mark, meta in metadata.items():
        marks.setdefault(text.index(meta["anchor"]), []).append(mark)

    sentences = []
    cursor = 0
    for sentence in split_sentences(text):
        start = text.index(sentence, cursor)
        sentences.append((start, start + len(sentence), sentence))
        cursor = start + len(sentence)

    cues = []
    raw_cues = tts.get("cues") or []
    if len(raw_cues) > 6:
        raise RuntimeError("Use no máximo seis direções de voz por cena.")
    for cue in raw_cues:
        phrase = str(cue.get("text", ""))
        kind = cue.get("kind", "emphasis")
        if not phrase.strip() or text.count(phrase) != 1 or kind not in CUE_DELIVERY:
            raise RuntimeError(f"Direção de voz precisa de trecho literal único e tipo válido: {phrase!r}")
        start = text.index(phrase)
        end = start + len(phrase)
        if not any(a <= start and end <= b for a, b, _ in sentences):
            raise RuntimeError("Cada direção de voz deve ficar dentro de uma frase.")
        if (start and text[start-1].isalnum() and phrase[0].isalnum()) or (end < len(text) and text[end].isalnum() and phrase[-1].isalnum()):
            raise RuntimeError("Direção de voz não pode cortar uma palavra.")
        cues.append((start, end, kind, max(0, min(300, int(cue.get("pause_before_ms", 0))))))
    cues.sort()
    if any(a[1] > b[0] for a, b in zip(cues, cues[1:])):
        raise RuntimeError("Direções de voz não podem se sobrepor.")

    boundaries = set(marks) | {n for a, b, _, _ in cues for n in (a, b)}
    pronunciations = {**GLOBAL_PRONUNCIATIONS, **(tts.get("pronunciations") or {})}
    for term in pronunciations:
        if not term:
            continue
        for match in re.finditer(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.IGNORECASE):
            if any(match.start() < n < match.end() for n in boundaries):
                raise RuntimeError(f"Direção/bookmark corta pronúncia cadastrada: {term!r}")

    def prosody(rate: int, pitch: int) -> str:
        # Limits preserve the presenter's identity and keep data understandable.
        return f'<prosody rate="{percent_text(max(-6, min(6, rate)))}" pitch="{percent_text(max(-3, min(3, pitch)))}">'

    rendered = []
    for index, (start, end, sentence) in enumerate(sentences):
        question = sentence.endswith("?")
        # A number slows only its explicit cue, never the entire sentence.
        rate = base_rate
        pitch = base_pitch + (1 if question else 0)
        local_cues = [cue for cue in cues if start <= cue[0] < end]
        points = sorted({start, end} | {n for n in boundaries if start <= n <= end})
        chunks = ["<s>", prosody(rate, pitch)]
        for i, point in enumerate(points):
            ending = next((c for c in local_cues if c[1] == point), None)
            beginning = next((c for c in local_cues if c[0] == point), None)
            if ending:
                chunks.append("</prosody>")
                chunks.append(prosody(rate, pitch))
            if beginning:
                chunks.append("</prosody>")
                # Pause before bookmark: the visual event must follow the pause.
                if beginning[3]:
                    chunks.append(f'<break time="{beginning[3]}ms"/>')
                cr, cp = CUE_DELIVERY[beginning[2]]
                chunks.append(prosody(rate + cr, pitch + cp))
            if point < end:
                chunks.extend(f'<bookmark mark="{mark}"/>' for mark in marks.get(point, []))
            if i + 1 < len(points):
                chunks.append(render_pronunciations(text[point:points[i+1]], tts))
        chunks.append("</prosody></s>")
        rendered.append("".join(chunks))
        if index < len(sentences) - 1:
            next_cue = next((c for c in cues if c[0] == sentences[index+1][0]), None)
            # Avoid stacking a sentence break with an explicit cue pause.
            gap = max(0, pause_ms - (next_cue[3] if next_cue else 0))
            if gap:
                rendered.append(f'<break time="{gap}ms"/>')
    body = "\n      ".join(rendered)
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="pt-BR">'
        f'<voice xml:lang="pt-BR" name={quoteattr(voice)}>{body}</voice></speak>',
        metadata,
    )


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
        "delivery_version": "editorial-v3-conversational",
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
        tts.setdefault("delivery", "hook" if position == 0 else "closing" if position == len(scenes) - 1 else "explain")
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
