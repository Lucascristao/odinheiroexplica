"""Generate all presenter narration with one Gemini 3.8 Live voice model."""

import argparse
import asyncio
from difflib import SequenceMatcher
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import unicodedata
import wave

from tts_config import (
    DEFAULT_PRESENTER,
    DEFAULT_TTS_VOICE,
    FALLBACK_TTS_MODEL,
    MINIMUM_TRANSCRIPTION_SIMILARITY,
    NO_VOICE_TREATMENT,
    PRESENTER_NAMES,
    PRESENTER_VOICES,
    PRIMARY_TTS_MODEL,
    SECONDARY_TTS_MODEL,
    TTS_MODEL_CASCADE,
    VOICE_DELIVERY_STYLE,
    VOICE_LANGUAGE,
    VOICE_POLICY,
    VOICE_POLICY_VERSION,
    live_session_config,
    project_pronunciations,
    project_speech_fingerprint,
    voice_policy_fingerprint,
)

SAMPLE_RATE = 24000
CHANNELS = 1
SAMPLE_WIDTH = 2
ENGINE = "google-gemini-live"
FALLBACK_VOICE_TREATMENT = "legacy-charon-3.1-to-3.8-eq-v1"


def voice_treatment_for_model(model: str, voice: str) -> str:
    return NO_VOICE_TREATMENT


def configured_fallback_models(primary_model: str) -> list[str]:
    if primary_model != PRIMARY_TTS_MODEL:
        raise RuntimeError("Modelo Gemini Live diferente da política canônica.")
    return []


def duration_seconds(path: Path) -> float:
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
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


def normalize_transcript(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text).casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", value))


def transcription_similarity(reference: str, transcript: str) -> float:
    left = normalize_transcript(reference)
    right = normalize_transcript(transcript)
    if not left or not right:
        return 0.0
    return round(SequenceMatcher(None, left, right).ratio(), 6)


def write_pcm_wav(path: Path, pcm: bytes) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with wave.open(str(temporary), "wb") as handle:
        handle.setnchannels(CHANNELS)
        handle.setsampwidth(SAMPLE_WIDTH)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm)
    temporary.replace(path)


def cached_duration(
    output_file: Path,
    narration_hash: str,
    model: str,
    voice: str,
    voice_treatment: str = NO_VOICE_TREATMENT,
    speech_profile_fingerprint: str | None = None,
) -> float | None:
    sidecar = output_file.with_suffix(".tts.json")
    if not output_file.is_file() or not sidecar.is_file():
        return None
    try:
        metadata = json.loads(sidecar.read_text(encoding="utf-8"))
        if any((
            metadata.get("engine") != ENGINE,
            metadata.get("narration_sha256") != narration_hash,
            metadata.get("model") != model,
            metadata.get("voice") != voice,
            metadata.get("voice_treatment", NO_VOICE_TREATMENT)
            != voice_treatment,
            metadata.get("voice_policy_fingerprint")
            != voice_policy_fingerprint(model, voice),
            metadata.get("speech_profile_fingerprint")
            != speech_profile_fingerprint,
            float(metadata.get("output_transcription_similarity", 0))
            < MINIMUM_TRANSCRIPTION_SIMILARITY,
            output_file.stat().st_size <= 1000,
            metadata.get("audio_sha256") != audio_sha256(output_file),
        )):
            return None
        actual_duration = duration_seconds(output_file)
        recorded_duration = float(metadata["duration_seconds"])
        if (
            not math.isfinite(actual_duration)
            or actual_duration <= 0
            or not math.isfinite(recorded_duration)
            or abs(actual_duration - recorded_duration) > 0.05
        ):
            return None
        return actual_duration
    except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError):
        return None


def save_audio_sidecar(
    output_file: Path,
    narration_hash: str,
    model: str,
    voice: str,
    duration: float,
    voice_treatment: str = NO_VOICE_TREATMENT,
    fallback_reason: str | None = None,
    speech_profile_fingerprint: str | None = None,
    output_transcription: str | None = None,
    output_transcription_similarity: float | None = None,
) -> None:
    sidecar = output_file.with_suffix(".tts.json")
    metadata = {
        "engine": ENGINE,
        "model": model,
        "voice": voice,
        "voice_treatment": voice_treatment,
        "fallback_reason": None,
        "voice_policy_version": VOICE_POLICY_VERSION,
        "voice_policy_fingerprint": voice_policy_fingerprint(model, voice),
        "speech_profile_fingerprint": speech_profile_fingerprint,
        "speech_endpoint": VOICE_POLICY["models"][model]["endpoint"],
        "narration_sha256": narration_hash,
        "audio_sha256": audio_sha256(output_file),
        "duration_seconds": duration,
        "output_transcription": output_transcription,
        "output_transcription_similarity": output_transcription_similarity,
    }
    temporary = sidecar.with_name(sidecar.name + ".tmp")
    temporary.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(sidecar)


async def _receive_live_turn(session) -> tuple[bytes, str]:
    pcm_chunks: list[bytes] = []
    transcript_chunks: list[str] = []
    turn_complete = False

    async for response in session.receive():
        server = getattr(response, "server_content", None)
        if server is None:
            continue

        model_turn = getattr(server, "model_turn", None)
        if model_turn is not None:
            for part in getattr(model_turn, "parts", []) or []:
                inline = getattr(part, "inline_data", None)
                data = (
                    getattr(inline, "data", None)
                    if inline is not None else None
                )
                if data:
                    pcm_chunks.append(bytes(data))

        transcription = getattr(server, "output_transcription", None)
        transcript_text = (
            getattr(transcription, "text", None)
            if transcription is not None else None
        )
        if transcript_text:
            transcript_chunks.append(str(transcript_text))

        if bool(getattr(server, "turn_complete", False)):
            turn_complete = True
            break

    if not turn_complete:
        raise RuntimeError("Gemini Live encerrou a resposta sem turn_complete.")

    pcm = b"".join(pcm_chunks)
    transcript = "".join(transcript_chunks).strip()
    if len(pcm) < SAMPLE_RATE * SAMPLE_WIDTH:
        raise RuntimeError("Gemini Live retornou menos de um segundo de áudio.")
    if not transcript:
        raise RuntimeError("Gemini Live não retornou a transcrição da própria saída.")
    return pcm, transcript


async def synthesize_missing_jobs(
    jobs: list[dict],
    *,
    gemini_key: str,
    voice: str,
    pronunciations: dict[str, str],
    speech_fingerprint: str,
) -> dict[str, dict]:
    if not jobs:
        return {}

    from google import genai

    client = genai.Client(api_key=gemini_key)
    config = live_session_config(voice, pronunciations)
    completed: dict[str, dict] = {}

    async with client.aio.live.connect(
        model=PRIMARY_TTS_MODEL,
        config=config,
    ) as session:
        for position, job in enumerate(jobs):
            scene_id = job["scene_id"]
            print(
                f"  [Gemini Live {position + 1}/{len(jobs)}] {scene_id}...",
                flush=True,
            )
            await session.send_client_content(
                turns={
                    "role": "user",
                    "parts": [{
                        "text": "ROTEIRO:\n" + job["narration"]
                    }],
                },
                turn_complete=True,
            )
            pcm, transcript = await _receive_live_turn(session)
            similarity = transcription_similarity(
                job["narration"], transcript
            )
            if similarity < MINIMUM_TRANSCRIPTION_SIMILARITY:
                raise RuntimeError(
                    f"Gemini Live divergiu do roteiro em {scene_id}: "
                    f"similaridade {similarity:.4f} < "
                    f"{MINIMUM_TRANSCRIPTION_SIMILARITY:.4f}."
                )

            write_pcm_wav(job["output_file"], pcm)
            duration = duration_seconds(job["output_file"])
            if not math.isfinite(duration) or duration <= 0:
                raise RuntimeError(
                    f"Gemini Live gerou áudio sem duração válida em {scene_id}."
                )

            save_audio_sidecar(
                job["output_file"],
                job["narration_hash"],
                PRIMARY_TTS_MODEL,
                voice,
                duration,
                NO_VOICE_TREATMENT,
                None,
                speech_fingerprint,
                transcript,
                similarity,
            )
            completed[scene_id] = {
                "duration": duration,
                "transcript": transcript,
                "similarity": similarity,
            }
            print(
                f"    [Gemini Live] {duration:.2f}s; "
                f"fidelidade do texto={similarity:.4f}; áudio PCM bruto.",
                flush=True,
            )

    return completed


def compute_beat_timings(
    narration: str,
    beats: list[dict],
    duration: float,
) -> list[dict]:
    if not beats:
        return []

    char_weights = []
    for ch in narration:
        if ch in (".", "!", "?"):
            char_weights.append(5.0)
        elif ch in (",", ";", ":"):
            char_weights.append(3.0)
        elif ch == " ":
            char_weights.append(1.0)
        else:
            char_weights.append(1.2)

    total_weight = sum(char_weights) or float(len(narration) or 1)
    timings = []
    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            continue
        anchor = str(beat.get("anchor") or "").strip()
        if not anchor:
            continue
        pos = narration.find(anchor)
        if pos == -1:
            offset = duration * (index / max(len(beats), 1))
            timing_source = "estimated-distributed"
        else:
            midpoint = pos + len(anchor) / 2.0
            weight = sum(char_weights[: int(midpoint)])
            offset = (weight / total_weight) * duration
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
    previous = 0.0
    for item in timings:
        if item["audio_offset_seconds"] < previous + 0.4:
            item["audio_offset_seconds"] = min(
                max(0.0, duration - 0.1), previous + 0.4
            )
        item["audio_offset_seconds"] = round(
            item["audio_offset_seconds"], 4
        )
        previous = item["audio_offset_seconds"]
    timings.sort(key=lambda item: item["beat_index"])
    return timings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        raise RuntimeError(
            "GEMINI_API_KEY não disponível; este render exige Gemini Live."
        )

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    scenes = payload.get("scenes") or payload.get("script", {}).get(
        "scenes", []
    )
    if not scenes:
        raise RuntimeError("Nenhuma cena recebida.")

    presenter = payload.get("presenter") or {}
    presenter_key = str(
        presenter.get("gender")
        or presenter.get("voice_id")
        or DEFAULT_PRESENTER
    )
    project_voice = PRESENTER_VOICES.get(
        presenter_key, DEFAULT_TTS_VOICE
    )
    presenter_name = PRESENTER_NAMES.get(presenter_key, "Roberto")
    pronunciations = project_pronunciations(payload)
    speech_fingerprint = project_speech_fingerprint(payload)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    jobs = []
    for position, scene in enumerate(scenes):
        scene_index = scene.get(
            "scene_index", scene.get("index", position)
        )
        scene_id = str(
            scene.get("id") or f"scene-{int(scene_index):02d}"
        )
        narration = str(scene["narration"]).strip()
        if not narration:
            raise RuntimeError(f"Cena {scene_id} sem narração.")
        jobs.append({
            "scene": scene,
            "scene_index": scene_index,
            "scene_id": scene_id,
            "narration": narration,
            "narration_hash": hashlib.sha256(
                narration.encode("utf-8")
            ).hexdigest(),
            "output_file": output_dir / f"{scene_id}.wav",
        })

    print(
        f"[Audio Engine] Gemini 3.8 Live + {project_voice} "
        f"({presenter_name}); {len(jobs)} cenas.",
        flush=True,
    )
    print(
        f"[Audio Engine] Política {VOICE_POLICY_VERSION}; "
        f"{VOICE_DELIVERY_STYLE}",
        flush=True,
    )
    if pronunciations:
        print(
            f"[Audio Engine] {len(pronunciations)} pronúncias explícitas "
            "serão aplicadas como instrução, sem alterar o texto.",
            flush=True,
        )

    missing = []
    synthesis_by_id: dict[str, dict] = {}
    for job in jobs:
        duration = cached_duration(
            job["output_file"],
            job["narration_hash"],
            PRIMARY_TTS_MODEL,
            project_voice,
            NO_VOICE_TREATMENT,
            speech_fingerprint,
        )
        if duration is None:
            missing.append(job)
            continue

        sidecar = json.loads(
            job["output_file"].with_suffix(".tts.json").read_text(
                encoding="utf-8"
            )
        )
        job["duration"] = duration
        synthesis_by_id[job["scene_id"]] = sidecar
        print(
            f"  [Gemini Live Cache] {job['scene_id']} validado "
            f"({duration}s).",
            flush=True,
        )

    generated = asyncio.run(
        synthesize_missing_jobs(
            missing,
            gemini_key=gemini_key,
            voice=project_voice,
            pronunciations=pronunciations,
            speech_fingerprint=speech_fingerprint,
        )
    )
    for job in missing:
        data = generated[job["scene_id"]]
        job["duration"] = data["duration"]
        synthesis_by_id[job["scene_id"]] = json.loads(
            job["output_file"].with_suffix(".tts.json").read_text(
                encoding="utf-8"
            )
        )

    manifest = {
        "engine": ENGINE,
        "model": PRIMARY_TTS_MODEL,
        "fallback_model": None,
        "fallback_models": [],
        "model_cascade": list(TTS_MODEL_CASCADE),
        "models_used": [PRIMARY_TTS_MODEL],
        "voice": project_voice,
        "requested_voice": project_voice,
        "presenter": presenter_key,
        "presenter_name": presenter_name,
        "voice_policy_version": VOICE_POLICY_VERSION,
        "voice_language": VOICE_LANGUAGE,
        "voice_delivery_style": VOICE_DELIVERY_STYLE,
        "speech_profile_fingerprint": speech_fingerprint,
        "output_format": "pcm-s16le-24000-mono-wav",
        "timing_mode": "estimated-character-alignment",
        "delivery_version": "gemini-live-v1-exact-transcript",
        "fallback_scene_ids": [],
        "fallback_scene_ids_by_model": {},
        "model_transition_scene_ids": [],
        "model_transition_count": 0,
        "scenes": [],
        "total_duration_seconds": 0.0,
    }

    for job in jobs:
        scene = job["scene"]
        sidecar = synthesis_by_id[job["scene_id"]]
        beat_timings = compute_beat_timings(
            job["narration"],
            (scene.get("visual") or {}).get("beats") or [],
            job["duration"],
        )
        manifest["scenes"].append({
            "id": job["scene_id"],
            "scene_index": job["scene_index"],
            "file": job["output_file"].name,
            "duration_seconds": job["duration"],
            "narration_sha256": job["narration_hash"],
            "engine": ENGINE,
            "model": PRIMARY_TTS_MODEL,
            "voice": project_voice,
            "voice_treatment": NO_VOICE_TREATMENT,
            "fallback_reason": None,
            "voice_policy_version": VOICE_POLICY_VERSION,
            "voice_policy_fingerprint": sidecar[
                "voice_policy_fingerprint"
            ],
            "speech_profile_fingerprint": speech_fingerprint,
            "speech_endpoint": "live-websocket",
            "output_transcription": sidecar.get(
                "output_transcription"
            ),
            "output_transcription_similarity": sidecar.get(
                "output_transcription_similarity"
            ),
            "audio_sha256": sidecar["audio_sha256"],
            "beat_timings": beat_timings,
        })
        manifest["total_duration_seconds"] += job["duration"]

    manifest["total_duration_seconds"] = round(
        manifest["total_duration_seconds"], 3
    )
    Path(args.manifest).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "[Audio Engine] Concluído com um único modelo/voz, sem fallback "
        f"e sem DSP. Duração total: {manifest['total_duration_seconds']}s.",
        flush=True,
    )


if __name__ == "__main__":
    main()
