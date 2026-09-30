import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import wave
from xml.sax.saxutils import escape

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


def synthesize_azure_scene(
    narration: str,
    gender: str,
    output_path: Path,
    azure_key: str,
    azure_region: str,
) -> bool:
    azure_voices = {
        "male": "pt-BR-MacerioMultilingualNeural",
        "female": "pt-BR-ThalitaMultilingualNeural",
    }
    voice_name = azure_voices.get(gender, "pt-BR-MacerioMultilingualNeural")
    url = f"https://{azure_region}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": azure_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-48khz-192kbitrate-mono-mp3",
        "User-Agent": "ODinheiroExplica",
    }
    escaped_text = escape(narration)
    ssml = (
        f"<speak version='1.0' xml:lang='pt-BR'>"
        f"<voice name='{voice_name}'>{escaped_text}</voice>"
        f"</speak>"
    )
    try:
        resp = requests.post(url, headers=headers, data=ssml.encode("utf-8"), timeout=60)
        if resp.status_code == 200 and len(resp.content) > 1000:
            output_path.write_bytes(resp.content)
            print(f"    [Azure Speech Fallback] Cena gerada com sucesso ({voice_name})!", flush=True)
            return True
        else:
            print(f"    [Azure Speech Erro] HTTP {resp.status_code}: {resp.text[:120]}", flush=True)
            return False
    except Exception as exc:
        print(f"    [Azure Speech Exceção] {exc}", flush=True)
        return False


def synthesize_gemini_audio(
    narration: str,
    voice_name: str,
    output_path: Path,
    gemini_key: str,
) -> bool:
    models_to_try = [
        "gemini-3.8-flash-tts",
        "gemini-3.8-flash-lite-tts",
        "gemini-2.0-flash",
    ]
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
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
                        print(f"    [Gemini TTS Aviso] Resposta sem inlineData em {model}: {str(data)[:100]}", flush=True)
                        break

                    b64_audio = audio_part["inlineData"]["data"]
                    mime_type = audio_part["inlineData"].get("mimeType", "")
                    raw_bytes = base64.b64decode(b64_audio)

                    temp_wav = output_path.with_suffix(".temp.wav")
                    if raw_bytes.startswith(b"RIFF") or "wav" in mime_type:
                        temp_wav.write_bytes(raw_bytes)
                    elif raw_bytes.startswith(b"ID3") or raw_bytes[:2] == b"\xff\xfb" or "mp3" in mime_type:
                        output_path.write_bytes(raw_bytes)
                        print(f"    [Gemini TTS Sucesso] Áudio direto via {model} (voz '{voice_name}')!", flush=True)
                        return True
                    else:
                        with wave.open(str(temp_wav), "wb") as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)
                            wf.setframerate(24000)
                            wf.writeframes(raw_bytes)

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
                        print(f"    [Gemini TTS Sucesso] Áudio convertido com sucesso via {model} (voz '{voice_name}')!", flush=True)
                        return True
                    except Exception:
                        output_path.write_bytes(temp_wav.read_bytes())
                        temp_wav.unlink(missing_ok=True)
                        print(f"    [Gemini TTS Sucesso] Áudio WAV preservado via {model} (voz '{voice_name}')!", flush=True)
                        return True

                elif response.status_code == 429:
                    print(f"    [Gemini Quota 429] Aguardando 15s para renovar quota...", flush=True)
                    time.sleep(15)
                    continue
                elif response.status_code in (500, 503):
                    time.sleep(4 * attempt)
                    continue
                else:
                    print(f"    [Gemini Erro {response.status_code} em {model}] {response.text[:120]}", flush=True)
                    break
            except Exception as exc:
                print(f"    [Gemini Exceção em {model}] {exc}", flush=True)
                time.sleep(3 * attempt)

    return False


def synthesize_scene_with_fallback(
    narration: str,
    voice_name: str,
    gender: str,
    output_path: Path,
    gemini_key: str,
    azure_key: str = "",
    azure_region: str = "eastus",
) -> None:
    # 1. Tenta sintetizar com Google Gemini TTS (modelos dedicados testados)
    if gemini_key:
        if synthesize_gemini_audio(narration, voice_name, output_path, gemini_key):
            return

    # 2. Se o Gemini não conseguiu ou não tem key, aciona Azure Speech como garantia absoluta
    if azure_key:
        print(f"    [Garantia de Entrega] Acionando Azure Speech para finalizar a cena...", flush=True)
        if synthesize_azure_scene(narration, gender, output_path, azure_key, azure_region):
            return

    raise RuntimeError(f"Falha ao sintetizar cena: nem Gemini nem Azure completaram o áudio.")


def compute_beat_timings(narration: str, beats: list[dict], duration: float) -> list[dict]:
    if not beats:
        return []

    char_weights = []
    for ch in narration:
        if ch in ('.', '!', '?'):
            char_weights.append(5.0)
        elif ch in (',', ';', ':'):
            char_weights.append(3.0)
        elif ch == ' ':
            char_weights.append(1.0)
        else:
            char_weights.append(1.2)

    total_weight = sum(char_weights)
    if total_weight <= 0:
        total_weight = float(len(narration) or 1)
        char_weights = [1.0] * len(narration)

    timings = []
    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            continue

        anchor = str(beat.get("anchor") or "").strip()
        if not anchor:
            continue

        pos = narration.find(anchor)
        if pos == -1:
            ratio = index / max(len(beats), 1)
            offset = duration * ratio
        else:
            midpoint = pos + (len(anchor) / 2.0)
            weight_up_to_anchor = sum(char_weights[:int(midpoint)])
            offset = (weight_up_to_anchor / total_weight) * duration

        offset = max(0.2, min(duration - 0.2, offset))
        timings.append({
            "beat_index": index,
            "anchor": anchor,
            "mark": f"beat-{index}",
            "audio_offset_seconds": round(offset, 4),
            "timing_source": "gemini-bookmark",
        })

    timings.sort(key=lambda item: item["audio_offset_seconds"])
    prev = 0.0
    min_gap = 0.4
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

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    azure_key = os.environ.get("AZURE_SPEECH_KEY", "").strip()
    azure_region = os.environ.get("AZURE_SPEECH_REGION", "eastus").strip()

    if not gemini_key and not azure_key:
        raise RuntimeError("Nenhuma credencial de áudio (GEMINI_API_KEY ou AZURE_SPEECH_KEY) disponível.")

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
        "engine": "google-gemini-tts-hybrid",
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

    print(f"[Audio Engine] Sintetizando {len(scenes)} cenas com voz oficial '{project_voice}' ({presenter_name})...", flush=True)

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
        synthesize_scene_with_fallback(
            narration=narration,
            voice_name=project_voice,
            gender=presenter_key,
            output_path=output_file,
            gemini_key=gemini_key,
            azure_key=azure_key,
            azure_region=azure_region,
        )
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
        # Intervalo de 3 segundos entre cenas para respeitar limites de requisições por minuto da Google API
        time.sleep(3)

    manifest["total_duration_seconds"] = round(manifest["total_duration_seconds"], 3)
    Path(args.manifest).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[Audio Engine] Concluído! Duração total: {manifest['total_duration_seconds']}s.", flush=True)


if __name__ == "__main__":
    main()
