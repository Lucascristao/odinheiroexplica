import argparse
import base64
import hashlib
import json
import os
import subprocess
import time
import wave
from pathlib import Path
import requests

from tts_config import (
    DEFAULT_PRESENTER,
    DEFAULT_TTS_PITCH,
    DEFAULT_TTS_RATE,
    DEFAULT_TTS_VOICE,
    PRESENTER_NAMES,
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


def synthesize_gemini_scene(
    narration: str,
    voice_name: str,
    output_path: Path,
    api_key: str,
) -> None:
    models_to_try = ["gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts", "gemini-3.8-flash"]
    last_error = None

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": narration}]
                }
            ],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": voice_name
                        }
                    }
                }
            }
        }

        for attempt in range(1, 4):
            try:
                response = requests.post(url, json=payload, timeout=90)
                if response.status_code == 200:
                    data = response.json()
                    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    audio_part = next((p for p in parts if "inlineData" in p and "data" in p["inlineData"]), None)
                    if not audio_part:
                        raise RuntimeError(f"Resposta do Gemini não contém inlineData de áudio: {data}")

                    b64_audio = audio_part["inlineData"]["data"]
                    mime_type = audio_part["inlineData"].get("mimeType", "")
                    raw_bytes = base64.b64decode(b64_audio)

                    temp_wav = output_path.with_suffix(".temp.wav")
                    if raw_bytes.startswith(b"RIFF") or "wav" in mime_type:
                        temp_wav.write_bytes(raw_bytes)
                    elif raw_bytes.startswith(b"ID3") or raw_bytes[:2] == b"\xff\xfb" or "mp3" in mime_type:
                        output_path.write_bytes(raw_bytes)
                        return
                    else:
                        with wave.open(str(temp_wav), "wb") as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)
                            wf.setframerate(24000)
                            wf.writeframes(raw_bytes)

                    # Converte para MP3 48kHz 192k mono (compatibilidade total com Remotion)
                    try:
                        subprocess.run(
                            [
                                "ffmpeg",
                                "-y",
                                "-i",
                                str(temp_wav),
                                "-ar",
                                "48000",
                                "-ac",
                                "1",
                                "-b:a",
                                "192k",
                                str(output_path),
                            ],
                            check=True,
                            capture_output=True,
                        )
                        temp_wav.unlink(missing_ok=True)
                        return
                    except Exception:
                        output_path.write_bytes(temp_wav.read_bytes())
                        temp_wav.unlink(missing_ok=True)
                        return

                elif response.status_code in (429, 500, 503):
                    time.sleep(2 * attempt)
                    continue
                else:
                    last_error = f"HTTP {response.status_code} ({model}): {response.text}"
                    break
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                time.sleep(2 * attempt)

    raise RuntimeError(f"Falha ao sintetizar cena com Gemini TTS ({voice_name}): {last_error}")


def compute_beat_timings(narration: str, beats: list[dict], duration: float) -> list[dict]:
    if not beats:
        return []

    # Ponderação fonética e pausas de respiração por pontuação
    char_weights = []
    for ch in narration:
        if ch in ('.', '!', '?'):
            char_weights.append(5.0)
        elif ch in (',', ';', ':'):
            char_weights.append(3.0)
        elif ch == ' ':
            char_weights.append(1.0)
        else:
            char_weights.append(1.0)

    total_weight = sum(char_weights) or 1.0
    normalized_narration = narration.lower()
    timings = []

    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            continue
        anchor = str(beat.get("anchor") or "").strip()
        explicit_at = beat.get("at")
        mark = f"beat-{index}"

        offset = None
        if isinstance(explicit_at, (int, float)):
            offset = max(0.0, min(duration, float(explicit_at) * duration))
        elif anchor:
            pos = normalized_narration.find(anchor.lower())
            if pos >= 0:
                weight_up_to_anchor = sum(char_weights[:pos])
                offset = (weight_up_to_anchor / total_weight) * duration
            else:
                offset = ((index + 1) / (len(beats) + 1)) * duration
        else:
            offset = ((index + 1) / (len(beats) + 1)) * duration

        timings.append({
            "beat_index": index,
            "anchor": anchor,
            "mark": mark,
            "audio_offset_seconds": round(float(offset), 4),
            "timing_source": "gemini-bookmark",
        })

    # Garante ordenação temporal estrita com espaçamento mínimo
    timings.sort(key=lambda item: item["audio_offset_seconds"])
    min_gap = 0.35
    prev = 0.0
    for item in timings:
        if item["audio_offset_seconds"] < prev + min_gap:
            item["audio_offset_seconds"] = min(max(0.0, duration - 0.1), prev + min_gap)
        item["audio_offset_seconds"] = round(item["audio_offset_seconds"], 4)
        prev = item["audio_offset_seconds"]

    timings.sort(key=lambda item: item["beat_index"])
    return timings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    api_key = (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("AZURE_SPEECH_KEY", "").strip()
    )
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY não configurada no ambiente.")

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
    presenter_name = PRESENTER_NAMES.get(presenter_key, "Roberto")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "engine": "google-gemini-3.8-flash-tts",
        "voice": project_voice,
        "presenter": presenter_key,
        "presenter_name": presenter_name,
        "rate": DEFAULT_TTS_RATE,
        "pitch": DEFAULT_TTS_PITCH,
        "output_format": "audio-48khz-192kbitrate-mono-mp3",
        "timing_mode": "gemini-anchor-alignment",
        "delivery_version": "gemini-neural-v1",
        "scenes": [],
        "total_duration_seconds": 0.0,
    }

    print(f"[Gemini TTS] Sintetizando {len(scenes)} cenas com voz '{project_voice}' ({presenter_name})...", flush=True)

    for position, scene in enumerate(scenes):
        scene_index = scene.get("scene_index", scene.get("index", position))
        scene_id = str(scene.get("id") or f"scene-{int(scene_index):02d}")
        narration = str(scene["narration"]).strip()
        if not narration:
            raise RuntimeError(f"Cena {scene_id} sem narração.")

        narration_hash = hashlib.sha256(narration.encode("utf-8")).hexdigest()
        output_file = output_dir / f"{scene_id}.mp3"
        visual = scene.get("visual") or {}
        visual_beats = visual.get("beats") or []

        print(f"  [Cena {scene_index + 1}/{len(scenes)}] {scene_id}...", flush=True)
        synthesize_gemini_scene(narration, project_voice, output_file, api_key)
        duration = duration_seconds(output_file)

        beat_timings = compute_beat_timings(narration, visual_beats, duration)

        manifest["scenes"].append({
            "id": scene_id,
            "scene_index": scene_index,
            "file": output_file.name,
            "duration_seconds": duration,
            "narration_sha256": narration_hash,
            "beat_timings": beat_timings,
        })
        manifest["total_duration_seconds"] += duration
        time.sleep(1)

    manifest["total_duration_seconds"] = round(manifest["total_duration_seconds"], 3)
    Path(args.manifest).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[Gemini TTS] Concluído! Duração total: {manifest['total_duration_seconds']}s.", flush=True)


if __name__ == "__main__":
    main()
