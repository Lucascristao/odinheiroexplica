import argparse
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
import wave

import requests

from tts_config import (
    DEFAULT_PRESENTER,
    DEFAULT_TTS_PITCH,
    DEFAULT_TTS_RATE,
    DEFAULT_TTS_VOICE,
    PRESENTER_NAMES,
    PRESENTER_VOICES,
)


PRIMARY_TTS_MODEL = "gemini-3.8-flash-tts"
FALLBACK_TTS_MODEL = "gemini-3.1-flash-tts-preview"
# Measured against the user's three Charon samples: 3.1 has more energy above
# 4 kHz, less around 1.5 kHz, and nearly identical overall RMS to 3.8.
# This is deliberately mild EQ, not pitch or timing manipulation.
FALLBACK_VOICE_TREATMENT = "charon-3.1-to-3.8-eq-v1"
FALLBACK_AUDIO_FILTER = (
    "lowshelf=f=160:g=-1.0,"
    "equalizer=f=1500:t=q:w=0.8:g=1.5,"
    "highshelf=f=4200:g=-2.5"
)
NO_VOICE_TREATMENT = "none"


@dataclass(frozen=True)
class SynthesisOutcome:
    model: str | None
    failure: str | None = None


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


def audio_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as audio:
        for chunk in iter(lambda: audio.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cached_duration(
    output_file: Path, narration_hash: str, model: str, voice: str,
    voice_treatment: str = NO_VOICE_TREATMENT,
) -> float | None:
    sidecar = output_file.with_suffix(".tts.json")
    if not output_file.is_file() or not sidecar.is_file():
        return None
    try:
        metadata = json.loads(sidecar.read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            return None
        if any((
            metadata.get("engine") != "google-gemini-tts",
            metadata.get("narration_sha256") != narration_hash,
            metadata.get("model") != model,
            metadata.get("voice") != voice,
            metadata.get("voice_treatment", NO_VOICE_TREATMENT) != voice_treatment,
            output_file.stat().st_size <= 1000,
            metadata.get("audio_sha256") != audio_sha256(output_file),
        )):
            return None
        actual_duration = duration_seconds(output_file)
        recorded_duration = float(metadata["duration_seconds"])
        if not math.isfinite(actual_duration) or actual_duration <= 0:
            return None
        if not math.isfinite(recorded_duration) or abs(actual_duration - recorded_duration) > 0.05:
            return None
        return actual_duration
    except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError):
        return None


def save_audio_sidecar(
    output_file: Path, narration_hash: str, model: str, voice: str, duration: float,
    voice_treatment: str = NO_VOICE_TREATMENT,
    fallback_reason: str | None = None,
) -> None:
    sidecar = output_file.with_suffix(".tts.json")
    metadata = {
        "engine": "google-gemini-tts",
        "model": model,
        "voice": voice,
        "voice_treatment": voice_treatment,
        "fallback_reason": fallback_reason,
        "narration_sha256": narration_hash,
        "audio_sha256": audio_sha256(output_file),
        "duration_seconds": duration,
    }
    temporary = sidecar.with_name(sidecar.name + ".tmp")
    temporary.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(sidecar)


def retry_after_seconds(header: str) -> float | None:
    if not header:
        return None
    try:
        return max(0.0, float(header))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(header)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


class GeminiRequestPacer:
    """Keep requests under the Free tier's three-starts-per-minute limit."""

    def __init__(self, minimum_interval_seconds: float = 22.0) -> None:
        self.minimum_interval_seconds = minimum_interval_seconds
        self.last_started_at: float | None = None

    def wait_before_request(self) -> None:
        now = time.monotonic()
        if self.last_started_at is not None:
            wait = max(0.0, self.last_started_at + self.minimum_interval_seconds - now)
            if wait > 0:
                print(f"    [Gemini RPM] Aguardando {wait:.1f}s entre requisições.", flush=True)
                time.sleep(wait)
                now = time.monotonic()
        self.last_started_at = now


def _safe_quota_field(value: object, gemini_key: str, max_length: int = 160) -> str:
    """Only log structured identifiers; never echo arbitrary API error text or URLs."""
    if not isinstance(value, str) or len(value) > max_length:
        return ""
    if gemini_key and gemini_key in value:
        return ""
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", value):
        return ""
    return value


def _google_retry_delay_seconds(value: object) -> float | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"(\d+(?:\.\d+)?)s", value)
    if not match:
        return None
    delay = float(match.group(1))
    return delay if math.isfinite(delay) else None


def gemini_429_diagnostic(response: object, gemini_key: str) -> tuple[str, float | None, bool]:
    """Extract safe quota details and suggested wait from a Google 429 response."""
    fragments = []
    retry_delay = retry_after_seconds(response.headers.get("Retry-After", ""))
    if retry_delay is not None:
        fragments.append(f"Retry-After={retry_delay:.1f}s")
    daily_quota_exceeded = False

    try:
        payload = response.json()
    except (TypeError, ValueError):
        payload = None
    error = payload.get("error") if isinstance(payload, dict) else None
    if not isinstance(error, dict):
        return ("; ".join(fragments) or "detalhes de cota indisponíveis", retry_delay, False)

    status = _safe_quota_field(error.get("status"), gemini_key)
    if status:
        fragments.insert(0, f"status={status}")
    details = error.get("details")
    if not isinstance(details, list):
        details = []
    for detail in details[:8]:
        if not isinstance(detail, dict):
            continue
        detail_type = detail.get("@type", "")
        if detail_type == "type.googleapis.com/google.rpc.RetryInfo":
            suggested = _google_retry_delay_seconds(detail.get("retryDelay"))
            if suggested is not None:
                retry_delay = max(retry_delay or 0.0, suggested)
                fragments.append(f"RetryInfo={suggested:.1f}s")
        elif detail_type == "type.googleapis.com/google.rpc.QuotaFailure":
            violations = detail.get("violations")
            if not isinstance(violations, list):
                continue
            for violation in violations[:3]:
                if not isinstance(violation, dict):
                    continue
                metric = _safe_quota_field(violation.get("quotaMetric"), gemini_key)
                quota_id = _safe_quota_field(violation.get("quotaId"), gemini_key)
                quota_value = _safe_quota_field(violation.get("quotaValue"), gemini_key, 24)
                kind = ""
                lower_id = quota_id.lower()
                if "perday" in lower_id and "request" in lower_id:
                    kind = "RPD"
                    daily_quota_exceeded = True
                elif "perminute" in lower_id and "token" in lower_id:
                    kind = "TPM"
                elif "perminute" in lower_id and "request" in lower_id:
                    kind = "RPM"
                quota_fields = [
                    f"tipo={kind}" if kind else "",
                    f"métrica={metric}" if metric else "",
                    f"cota={quota_id}" if quota_id else "",
                    f"limite={quota_value}" if quota_value else "",
                ]
                fragments.extend(field for field in quota_fields if field)

    return ("; ".join(fragments) or "detalhes de cota indisponíveis", retry_delay, daily_quota_exceeded)


def synthesize_gemini_audio(
    narration: str,
    voice_name: str,
    output_path: Path,
    gemini_key: str,
    model: str,
    pacer: GeminiRequestPacer | None = None,
) -> SynthesisOutcome:
    if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
        raise ValueError("Identificador do modelo Gemini inválido.")
    pacer = pacer or GeminiRequestPacer()
    for model in [model]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
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

        max_attempts = 3
        retry_budget_seconds = 180.0
        for attempt in range(1, max_attempts + 1):
            try:
                pacer.wait_before_request()
                response = requests.post(
                    url, json=payload, timeout=180,
                    headers={"x-goog-api-key": gemini_key},
                )
                if response.status_code == 200:
                    data = response.json()
                    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    audio_part = next((p for p in parts if "inlineData" in p and "data" in p["inlineData"]), None)
                    if not audio_part:
                        print(f"    [Gemini TTS Aviso] Resposta sem inlineData em {model}.", flush=True)
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
                        return SynthesisOutcome(model)
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
                        return SynthesisOutcome(model)
                    except Exception as exc:
                        temp_wav.unlink(missing_ok=True)
                        print(f"    [Gemini TTS Erro] Conversão MP3 falhou ({type(exc).__name__}).", flush=True)
                        break

                elif response.status_code == 429:
                    diagnostic, suggested_retry, daily_quota_exceeded = gemini_429_diagnostic(response, gemini_key)
                    print(f"    [Gemini Quota 429] {diagnostic}", flush=True)
                    if daily_quota_exceeded:
                        print("    [Gemini Quota 429] Limite diário (RPD) atingido; interrompendo sem novas tentativas.", flush=True)
                        return SynthesisOutcome(None, "rpd")
                    if attempt == max_attempts or retry_budget_seconds <= 0:
                        print(f"    [Gemini TTS Erro] HTTP 429 persistente em {model} após {attempt} tentativas; limite de quota não liberado.", flush=True)
                        return SynthesisOutcome(None, "rate-limit-persistent")
                    delay = min(120, 15 * 2 ** (attempt - 1))
                    if suggested_retry is not None:
                        delay = max(delay, suggested_retry)
                    delay = min(delay, retry_budget_seconds)
                    print(f"    [Gemini Quota 429] Tentativa {attempt}/{max_attempts}; aguardando {delay:.0f}s (limite total de espera: 180s)...", flush=True)
                    time.sleep(delay)
                    retry_budget_seconds -= delay
                    continue
                elif response.status_code in (500, 502, 503, 504):
                    if attempt < max_attempts:
                        time.sleep(4 * attempt)
                        continue
                    return SynthesisOutcome(None, "server-unavailable")
                else:
                    print(f"    [Gemini Erro {response.status_code} em {model}] Resposta HTTP sem áudio.", flush=True)
                    break
            except requests.exceptions.Timeout:
                print(f"    [Gemini Tempo esgotado em {model}] tentativa {attempt}/{max_attempts}.", flush=True)
                if attempt < max_attempts:
                    time.sleep(3 * attempt)
                else:
                    return SynthesisOutcome(None, "request-timeout")
            except Exception as exc:
                print(f"    [Gemini Exceção em {model}] {type(exc).__name__}; tentativa {attempt}/{max_attempts}.", flush=True)
                if attempt < max_attempts:
                    time.sleep(3 * attempt)

    return SynthesisOutcome(None, "other")


def apply_fallback_voice_treatment(output_file: Path) -> None:
    """Apply the measured, fixed Charon EQ to 3.1 audio before caching it."""
    treated = output_file.with_name(output_file.stem + ".treated.mp3")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(output_file),
                "-af", FALLBACK_AUDIO_FILTER,
                "-ar", "48000", "-ac", "1", "-b:a", "192k", str(treated),
            ],
            check=True, capture_output=True,
        )
        if not treated.is_file() or treated.stat().st_size <= 1000:
            raise RuntimeError("Áudio tratado ausente ou vazio.")
        treated.replace(output_file)
    finally:
        treated.unlink(missing_ok=True)


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
            timing_source = "estimated-distributed"
        else:
            midpoint = pos + (len(anchor) / 2.0)
            weight_up_to_anchor = sum(char_weights[:int(midpoint)])
            offset = (weight_up_to_anchor / total_weight) * duration
            timing_source = "estimated-text-alignment"

        offset = max(0.2, min(duration - 0.2, offset))
        timings.append({
            "beat_index": index,
            "anchor": anchor,
            "mark": f"beat-{index}",
            "audio_offset_seconds": round(offset, 4),
            "timing_source": timing_source,
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
    gemini_model = os.environ.get("GEMINI_TTS_MODEL", PRIMARY_TTS_MODEL).strip()
    fallback_model = os.environ.get("GEMINI_TTS_FALLBACK_MODEL", FALLBACK_TTS_MODEL).strip()

    if not gemini_key:
        raise RuntimeError("GEMINI_API_KEY não disponível; este render aceita apenas voz Gemini.")
    if not gemini_model:
        raise RuntimeError("GEMINI_TTS_MODEL vazio.")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", gemini_model):
        raise RuntimeError("GEMINI_TTS_MODEL inválido.")
    if fallback_model and fallback_model != FALLBACK_TTS_MODEL:
        raise RuntimeError("GEMINI_TTS_FALLBACK_MODEL deve ser o Gemini 3.1 Flash TTS preview ou vazio.")

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
    fallback_enabled = (
        gemini_model == PRIMARY_TTS_MODEL
        and fallback_model == FALLBACK_TTS_MODEL
        and project_voice == "Charon"
    )
    if not fallback_enabled:
        fallback_model = ""

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "engine": "pending",
        "model": gemini_model,
        "fallback_model": fallback_model or None,
        "voice": project_voice,
        "requested_voice": project_voice,
        "presenter": presenter_key,
        "presenter_name": presenter_name,
        "rate": DEFAULT_TTS_RATE,
        "pitch": DEFAULT_TTS_PITCH,
        "output_format": "audio-48khz-192kbitrate-mono-mp3",
        "timing_mode": "estimated-character-alignment",
        "delivery_version": "tts-per-scene-v2",
        "scenes": [],
        "total_duration_seconds": 0.0,
    }

    print(f"[Audio Engine] Sintetizando {len(scenes)} cenas com voz solicitada '{project_voice}' ({presenter_name})...", flush=True)
    scene_jobs = []
    for position, scene in enumerate(scenes):
        scene_index = scene.get("scene_index", scene.get("index", position))
        scene_id = str(scene.get("id") or f"scene-{int(scene_index):02d}")
        narration = str(scene["narration"]).strip()
        if not narration:
            raise RuntimeError(f"Cena {scene_id} sem narração.")

        scene_jobs.append({
            "scene": scene,
            "scene_index": scene_index,
            "scene_id": scene_id,
            "narration": narration,
            "narration_hash": hashlib.sha256(narration.encode("utf-8")).hexdigest(),
            "output_file": output_dir / f"{scene_id}.mp3",
        })

    synthesis_by_id = {}
    request_pacer = GeminiRequestPacer()
    fallback_active = False
    for position, job in enumerate(scene_jobs):
        print(f"  [Gemini {position + 1}/{len(scene_jobs)}] {job['scene_id']}...", flush=True)
        duration = cached_duration(
            job["output_file"], job["narration_hash"], gemini_model, project_voice
        )
        if duration is not None:
            print(f"    [Gemini Cache] Áudio validado e reutilizado ({duration}s).", flush=True)
            job["duration"] = duration
            synthesis_by_id[job["scene_id"]] = {
                "engine": "google-gemini-tts", "model": gemini_model,
                "voice": project_voice, "voice_treatment": NO_VOICE_TREATMENT,
                "fallback_reason": None,
            }
            continue
        if fallback_enabled:
            duration = cached_duration(
                job["output_file"], job["narration_hash"], fallback_model,
                project_voice, FALLBACK_VOICE_TREATMENT,
            )
            if duration is not None:
                print(f"    [Gemini Cache] Fallback 3.1 tratado reutilizado ({duration}s).", flush=True)
                fallback_active = True
                sidecar = json.loads(
                    job["output_file"].with_suffix(".tts.json").read_text(encoding="utf-8")
                )
                job["duration"] = duration
                synthesis_by_id[job["scene_id"]] = {
                    "engine": "google-gemini-tts", "model": fallback_model,
                    "voice": project_voice,
                    "voice_treatment": FALLBACK_VOICE_TREATMENT,
                    "fallback_reason": sidecar.get("fallback_reason") or "cached-fallback",
                }
                continue

        model_to_request = fallback_model if fallback_active else gemini_model
        outcome = synthesize_gemini_audio(
            job["narration"], project_voice, job["output_file"], gemini_key,
            model_to_request, request_pacer,
        )
        fallback_reason = "earlier-primary-failure" if fallback_active else None
        if outcome.model is None and model_to_request == gemini_model:
            if fallback_enabled and outcome.failure in {
                "rpd", "rate-limit-persistent", "server-unavailable", "request-timeout",
            }:
                fallback_active = True
                fallback_reason = outcome.failure
                print(
                    f"    [Gemini Fallback] Primário indisponível ({fallback_reason}); "
                    f"completando as cenas restantes com {fallback_model}, voz {project_voice}.",
                    flush=True,
                )
                model_to_request = fallback_model
                outcome = synthesize_gemini_audio(
                    job["narration"], project_voice, job["output_file"],
                    gemini_key, fallback_model, request_pacer,
                )
        if outcome.model is None:
            raise RuntimeError(
                f"Gemini TTS falhou na cena {job['scene_id']} "
                f"({model_to_request}: {outcome.failure}); render interrompido."
            )
        model = outcome.model
        voice_treatment = (
            FALLBACK_VOICE_TREATMENT if model == fallback_model and fallback_enabled
            else NO_VOICE_TREATMENT
        )
        if voice_treatment != NO_VOICE_TREATMENT:
            apply_fallback_voice_treatment(job["output_file"])
        duration = duration_seconds(job["output_file"])
        if not math.isfinite(duration) or duration <= 0:
            raise RuntimeError(f"Gemini TTS gerou áudio sem duração válida em {job['scene_id']}.")
        save_audio_sidecar(
            job["output_file"], job["narration_hash"], model, project_voice,
            duration, voice_treatment, fallback_reason,
        )
        job["duration"] = duration
        synthesis_by_id[job["scene_id"]] = {
            "engine": "google-gemini-tts", "model": model,
            "voice": project_voice, "voice_treatment": voice_treatment,
            "fallback_reason": fallback_reason,
        }

    for job in scene_jobs:
        scene = job["scene"]
        scene_id = job["scene_id"]
        narration = job["narration"]
        output_file = job["output_file"]
        duration = job["duration"]
        narration_hash = job["narration_hash"]
        beat_timings = compute_beat_timings(
            narration, (scene.get("visual") or {}).get("beats") or [], duration
        )
        manifest["scenes"].append({
            "id": scene_id,
            "scene_index": job["scene_index"],
            "file": output_file.name,
            "duration_seconds": duration,
            "narration_sha256": narration_hash,
            **synthesis_by_id[scene_id],
            "beat_timings": beat_timings,
        })
        manifest["total_duration_seconds"] += duration

    manifest["total_duration_seconds"] = round(manifest["total_duration_seconds"], 3)
    engines = {scene["engine"] for scene in manifest["scenes"]}
    voices = {scene["voice"] for scene in manifest["scenes"]}
    if len(engines) != 1 or len(voices) != 1:
        raise RuntimeError("A síntese produziu motores ou vozes diferentes no mesmo vídeo.")
    manifest["engine"] = next(iter(engines))
    manifest["voice"] = next(iter(voices))
    manifest["models_used"] = sorted({scene["model"] for scene in manifest["scenes"]})
    manifest["fallback_scene_ids"] = [
        scene["id"] for scene in manifest["scenes"]
        if scene["model"] == FALLBACK_TTS_MODEL
    ]
    Path(args.manifest).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[Audio Engine] Concluído! Duração total: {manifest['total_duration_seconds']}s.", flush=True)


if __name__ == "__main__":
    main()
