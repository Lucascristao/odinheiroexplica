"""Generate all presenter narration with one Gemini 3.8 Live voice model."""

import argparse
import asyncio
from difflib import SequenceMatcher
import hashlib
import importlib.metadata
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
    GOOGLE_GENAI_REQUIRED_VERSION,
    LIVE_EXPECTED_SPEECH_WPM,
    LIVE_FIRST_AUDIO_TIMEOUT_SECONDS,
    LIVE_MAX_ATTEMPTS,
    LIVE_PATHOLOGICAL_DURATION_EXTRA_SECONDS,
    LIVE_PATHOLOGICAL_DURATION_FLOOR_SECONDS,
    LIVE_PATHOLOGICAL_DURATION_MULTIPLIER,
    LIVE_POST_GENERATION_GRACE_SECONDS,
    LIVE_ACCEPT_GENERATION_COMPLETE_WITHOUT_TURN_COMPLETE,
    LIVE_RETRY_BACKOFF_SECONDS,
    LIVE_STREAM_IDLE_TIMEOUT_SECONDS,
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
    scene_voice_direction,
    scene_direction_fingerprint,
    live_turn_text,
)
from editorial_project import normalize_project
from gemini_live_fidelity import evaluate_transcription, canonical_tokens

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


def transcription_similarity(reference: str, transcript: str, pronunciations=None) -> float:
    return evaluate_transcription(reference, transcript, pronunciations)["similarity"]


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
    *,
    narration: str | None = None,
    pronunciations: dict | None = None,
    direction_fingerprint: str | None = None,
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
            metadata.get("scene_direction_fingerprint") != direction_fingerprint,
            float(metadata.get("output_transcription_similarity", 0))
            < MINIMUM_TRANSCRIPTION_SIMILARITY,
            output_file.stat().st_size <= 1000,
            metadata.get("audio_sha256") != audio_sha256(output_file),
        )):
            return None
        if narration is not None and not evaluate_transcription(narration, metadata.get("output_transcription") or "", pronunciations, MINIMUM_TRANSCRIPTION_SIMILARITY)["passed"]:
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
    *,
    direction_fingerprint: str | None = None,
    fidelity: dict | None = None,
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
        "scene_direction_fingerprint": direction_fingerprint,
        "output_fidelity": fidelity,
    }
    temporary = sidecar.with_name(sidecar.name + ".tmp")
    temporary.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(sidecar)


class RetryableLiveError(RuntimeError):
    """Transient Live failure that is safe to retry in a fresh session."""


def installed_google_genai_version() -> str:
    try:
        return importlib.metadata.version("google-genai")
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def _jsonable(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        try:
            return _jsonable(model_dump(mode="json", exclude_none=True))
        except TypeError:
            return _jsonable(model_dump(exclude_none=True))
    result = {}
    for name in (
        "prompt_token_count",
        "response_token_count",
        "candidates_token_count",
        "total_token_count",
        "time_left",
        "new_handle",
        "resumable",
    ):
        item = getattr(value, name, None)
        if item is not None:
            result[name] = _jsonable(item)
    return result or str(value)


def estimated_audio_seconds(narration: str) -> float:
    words = max(1, len(re.findall(r"\S+", narration)))
    return words * 60.0 / LIVE_EXPECTED_SPEECH_WPM


def max_allowed_audio_seconds(narration: str) -> float:
    expected = estimated_audio_seconds(narration)
    return max(
        LIVE_PATHOLOGICAL_DURATION_FLOOR_SECONDS,
        expected * LIVE_PATHOLOGICAL_DURATION_MULTIPLIER
        + LIVE_PATHOLOGICAL_DURATION_EXTRA_SECONDS,
    )


def _exception_close_details(exc: Exception) -> dict:
    details = {
        "type": type(exc).__name__,
        "message": str(exc),
    }
    code = getattr(exc, "code", None)
    reason = getattr(exc, "reason", None)
    received = getattr(exc, "rcvd", None)
    if code is None and received is not None:
        code = getattr(received, "code", None)
    if reason is None and received is not None:
        reason = getattr(received, "reason", None)
    if code is not None:
        details["close_code"] = _jsonable(code)
    if reason is not None:
        details["close_reason"] = str(reason)
    return details


def is_retryable_live_error(exc: Exception) -> bool:
    if isinstance(exc, RetryableLiveError):
        return True
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError, ConnectionError)):
        return True

    details = _exception_close_details(exc)
    code = details.get("close_code")
    try:
        numeric_code = int(code) if code is not None else None
    except (TypeError, ValueError):
        numeric_code = None
    if numeric_code in {1006, 1011, 1012, 1013}:
        return True

    message = str(exc).casefold()
    markers = (
        "resource has been exhausted",
        "resource_exhausted",
        "temporarily unavailable",
        "service unavailable",
        "internal error",
        "connection closed",
        "closed with error",
        "no close frame",
        "keepalive ping timeout",
        "aborted",
        "unavailable",
        "timed out",
        "timeout",
        "1011",
        "1012",
        "1013",
        "status 429",
        "status 500",
        "status 502",
        "status 503",
        "status 504",
    )
    return any(marker in message for marker in markers)


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _new_attempt_diagnostics(
    scene_id: str,
    attempt: int,
    narration: str,
) -> dict:
    return {
        "scene_id": scene_id,
        "attempt": attempt,
        "status": "running",
        "started_at_utc": _utc_now(),
        "expected_audio_seconds": round(estimated_audio_seconds(narration), 3),
        "max_allowed_audio_seconds": round(
            max_allowed_audio_seconds(narration), 3
        ),
        "received_messages": 0,
        "pcm_bytes": 0,
        "audio_seconds_streamed": 0.0,
        "first_audio_latency_seconds": None,
        "usage_metadata": [],
        "go_away": [],
        "session_resumption_updates": [],
        "generation_complete_seen": False,
        "turn_complete_seen": False,
        "accepted_generation_complete_without_turn_complete": False,
    }


def write_live_diagnostics(path: Path, diagnostics: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(diagnostics, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


async def _receive_live_turn(
    session,
    *,
    narration: str = "",
    attempt_diagnostics: dict | None = None,
) -> tuple[bytes, str]:
    diagnostics = attempt_diagnostics if attempt_diagnostics is not None else {}
    diagnostics.setdefault("generation_complete_seen", False)
    diagnostics.setdefault("turn_complete_seen", False)
    diagnostics.setdefault(
        "accepted_generation_complete_without_turn_complete", False
    )
    pcm_chunks: list[bytes] = []
    transcript_chunks: list[str] = []
    pcm_bytes = 0
    turn_complete = False
    accepted_generation_complete = False
    generation_complete_at = None
    loop = asyncio.get_running_loop()
    started = loop.time()
    first_audio_at = None
    max_audio_seconds = max_allowed_audio_seconds(narration)
    wall_limit_seconds = max(
        120.0,
        max_audio_seconds + LIVE_STREAM_IDLE_TIMEOUT_SECONDS + 20.0,
    )
    iterator = session.receive().__aiter__()

    while True:
        elapsed = loop.time() - started
        if elapsed >= wall_limit_seconds:
            raise RetryableLiveError(
                f"Gemini Live excedeu {wall_limit_seconds:.1f}s sem concluir o turno."
            )

        if first_audio_at is None:
            remaining = LIVE_FIRST_AUDIO_TIMEOUT_SECONDS - elapsed
            if remaining <= 0:
                raise RetryableLiveError(
                    "Gemini Live não iniciou áudio dentro do prazo de primeiro frame."
                )
            wait_seconds = remaining
        elif generation_complete_at is not None:
            remaining = LIVE_POST_GENERATION_GRACE_SECONDS - (
                loop.time() - generation_complete_at
            )
            if remaining <= 0:
                if (
                    LIVE_ACCEPT_GENERATION_COMPLETE_WITHOUT_TURN_COMPLETE
                    and pcm_bytes >= SAMPLE_RATE * SAMPLE_WIDTH
                    and "".join(transcript_chunks).strip()
                ):
                    accepted_generation_complete = True
                    diagnostics[
                        "accepted_generation_complete_without_turn_complete"
                    ] = True
                    diagnostics["completion_signal"] = (
                        "generation_complete_after_grace"
                    )
                    break
                raise RetryableLiveError(
                    "Gemini Live concluiu a geração, mas não finalizou o turno "
                    "nem entregou áudio/transcrição utilizáveis."
                )
            wait_seconds = min(
                remaining,
                wall_limit_seconds - elapsed,
            )
        else:
            wait_seconds = min(
                LIVE_STREAM_IDLE_TIMEOUT_SECONDS,
                wall_limit_seconds - elapsed,
            )

        try:
            response = await asyncio.wait_for(
                iterator.__anext__(),
                timeout=max(0.1, wait_seconds),
            )
        except StopAsyncIteration:
            if (
                diagnostics.get("generation_complete_seen")
                and LIVE_ACCEPT_GENERATION_COMPLETE_WITHOUT_TURN_COMPLETE
                and pcm_bytes >= SAMPLE_RATE * SAMPLE_WIDTH
                and "".join(transcript_chunks).strip()
            ):
                accepted_generation_complete = True
                diagnostics[
                    "accepted_generation_complete_without_turn_complete"
                ] = True
                diagnostics["completion_signal"] = (
                    "generation_complete_stream_closed"
                )
            break
        except asyncio.TimeoutError as exc:
            if first_audio_at is None:
                raise RetryableLiveError(
                    "Gemini Live não iniciou áudio dentro do prazo de primeiro frame."
                ) from exc
            if (
                generation_complete_at is not None
                and LIVE_ACCEPT_GENERATION_COMPLETE_WITHOUT_TURN_COMPLETE
                and pcm_bytes >= SAMPLE_RATE * SAMPLE_WIDTH
                and "".join(transcript_chunks).strip()
            ):
                accepted_generation_complete = True
                diagnostics[
                    "accepted_generation_complete_without_turn_complete"
                ] = True
                diagnostics["completion_signal"] = (
                    "generation_complete_after_grace"
                )
                break
            raise RetryableLiveError(
                "Gemini Live ficou sem novos eventos durante a geração de áudio."
            ) from exc

        diagnostics["received_messages"] = (
            int(diagnostics.get("received_messages", 0)) + 1
        )

        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            diagnostics.setdefault("usage_metadata", []).append(
                _jsonable(usage)
            )

        go_away = getattr(response, "go_away", None)
        if go_away is not None:
            diagnostics.setdefault("go_away", []).append(
                _jsonable(go_away)
            )

        resumption = getattr(response, "session_resumption_update", None)
        if resumption is not None:
            diagnostics.setdefault(
                "session_resumption_updates", []
            ).append(_jsonable(resumption))

        server = getattr(response, "server_content", None)
        if server is None:
            continue
        if bool(getattr(server, "interrupted", False)):
            raise RetryableLiveError(
                "Gemini Live interrompeu a fala; o áudio parcial não será aceito."
            )

        if bool(getattr(server, "generation_complete", False)):
            diagnostics["generation_complete_seen"] = True
            if generation_complete_at is None:
                generation_complete_at = loop.time()
                diagnostics["generation_complete_at_seconds"] = round(
                    generation_complete_at - started, 3
                )

        model_turn = getattr(server, "model_turn", None)
        if model_turn is not None:
            for part in getattr(model_turn, "parts", []) or []:
                inline = getattr(part, "inline_data", None)
                data = (
                    getattr(inline, "data", None)
                    if inline is not None else None
                )
                if not data:
                    continue
                mime = str(getattr(inline, "mime_type", "") or "")
                if mime and (
                    not mime.startswith("audio/pcm")
                    or (
                        "rate=" in mime
                        and not re.search(r"rate=24000(?:;|$)", mime)
                    )
                ):
                    raise RuntimeError(
                        "Gemini Live retornou formato PCM diferente de 24 kHz bruto."
                    )
                if first_audio_at is None:
                    first_audio_at = loop.time()
                    diagnostics["first_audio_latency_seconds"] = round(
                        first_audio_at - started, 3
                    )
                chunk = bytes(data)
                pcm_chunks.append(chunk)
                pcm_bytes += len(chunk)
                audio_seconds = (
                    pcm_bytes / (SAMPLE_RATE * CHANNELS * SAMPLE_WIDTH)
                )
                diagnostics["pcm_bytes"] = pcm_bytes
                diagnostics["audio_seconds_streamed"] = round(
                    audio_seconds, 3
                )
                if audio_seconds > max_audio_seconds:
                    raise RetryableLiveError(
                        "Gemini Live entrou em geração de áudio anormalmente longa: "
                        f"{audio_seconds:.1f}s para um roteiro estimado em "
                        f"{estimated_audio_seconds(narration):.1f}s."
                    )

        transcription = getattr(server, "output_transcription", None)
        transcript_text = (
            getattr(transcription, "text", None)
            if transcription is not None else None
        )
        if transcript_text:
            transcript_chunks.append(str(transcript_text))

        if bool(getattr(server, "turn_complete", False)):
            diagnostics["turn_complete_seen"] = True
            diagnostics["completion_signal"] = "turn_complete"
            turn_complete = True
            break

    diagnostics["session_receive_seconds"] = round(loop.time() - started, 3)
    if not turn_complete and not accepted_generation_complete:
        raise RetryableLiveError(
            "Gemini Live encerrou a resposta sem turn_complete "
            "nem generation_complete aceitável."
        )

    pcm = b"".join(pcm_chunks)
    transcript = "".join(transcript_chunks).strip()
    if len(pcm) % SAMPLE_WIDTH or len(pcm) < SAMPLE_RATE * SAMPLE_WIDTH:
        raise RetryableLiveError(
            "Gemini Live concluiu o turno sem áudio utilizável."
        )
    if not transcript:
        raise RetryableLiveError(
            "Gemini Live não retornou a transcrição da própria saída."
        )
    return pcm, transcript


async def _synthesize_scene_with_retries(
    *,
    client,
    job: dict,
    config: dict,
    voice: str,
    pronunciations: dict[str, str],
    speech_fingerprint: str,
    diagnostics: dict,
    diagnostics_path: Path,
    session_holder: list | None = None,
    previous_context: str | None = None,
) -> dict:
    scene_id = job["scene_id"]
    for attempt in range(1, LIVE_MAX_ATTEMPTS + 1):
        attempt_diag = _new_attempt_diagnostics(
            scene_id, attempt, job["narration"]
        )
        diagnostics["attempts"].append(attempt_diag)
        write_live_diagnostics(diagnostics_path, diagnostics)
        started = asyncio.get_running_loop().time()

        session_ctx = None
        session = None
        session_reused = False

        if session_holder and session_holder[0] is not None and attempt == 1:
            session_ctx, session = session_holder[0], session_holder[1]
            session_reused = True
            attempt_diag["session_reused"] = True
            attempt_diag["session_opened"] = True

        try:
            if session is None:
                session_ctx = client.aio.live.connect(
                    model=PRIMARY_TTS_MODEL,
                    config=config,
                )
                session = await session_ctx.__aenter__()
                attempt_diag["session_opened"] = True
                attempt_diag["session_reused"] = False
                if session_holder is not None:
                    session_holder[0] = session_ctx
                    session_holder[1] = session

            turn_prompt = live_turn_text(
                job["narration"],
                job.get("direction") or {},
                previous_context=previous_context if not session_reused else None,
            )
            await session.send_client_content(
                turns={
                    "role": "user",
                    "parts": [{"text": turn_prompt}],
                },
                turn_complete=True,
            )
            pcm, transcript = await _receive_live_turn(
                session,
                narration=job["narration"],
                attempt_diagnostics=attempt_diag,
            )

            fidelity = evaluate_transcription(
                job["narration"],
                transcript,
                {
                    **pronunciations,
                    **(job.get("direction") or {}).get(
                        "pronunciations", {}
                    ),
                },
                MINIMUM_TRANSCRIPTION_SIMILARITY,
            )
            similarity = fidelity["similarity"]
            if not fidelity["passed"]:
                message = (
                    f"Gemini Live divergiu do roteiro em {scene_id}: "
                    f"similaridade {similarity:.4f}; alteração literal: "
                    f"{json.dumps(fidelity['differences'][:3], ensure_ascii=False)}."
                )
                mismatch_kind = (
                    "apenas numérica"
                    if fidelity.get("numeric_only_mismatch")
                    else "lexical"
                )
                raise RetryableLiveError(
                    message
                    + f" Divergência {mismatch_kind}; áudio rejeitado. "
                    "Retentativa na mesma cena/voz/modelo, limitada pela política Live."
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
                direction_fingerprint=job.get(
                    "direction_fingerprint"
                ),
                fidelity=fidelity,
            )
            attempt_diag["status"] = "success"
            attempt_diag["audio_duration_seconds"] = duration
            attempt_diag["transcription_similarity"] = similarity
            attempt_diag["completed_at_utc"] = _utc_now()
            attempt_diag["attempt_wall_seconds"] = round(
                asyncio.get_running_loop().time() - started, 3
            )
            diagnostics["completed_scene_ids"].append(scene_id)
            write_live_diagnostics(diagnostics_path, diagnostics)
            strategy_info = "sessão contínua" if session_reused else f"sessão {attempt}/{LIVE_MAX_ATTEMPTS}"
            print(
                f"    [Gemini Live] {duration:.2f}s; "
                f"fidelidade do texto={similarity:.4f}; áudio PCM bruto; "
                f"{strategy_info}.",
                flush=True,
            )
            return {
                "duration": duration,
                "transcript": transcript,
                "similarity": similarity,
                "fidelity": fidelity,
            }

        except Exception as exc:
            if session_holder is not None:
                if session_holder[0] is not None:
                    try:
                        await session_holder[0].__aexit__(None, None, None)
                    except Exception:
                        pass
                session_holder[0] = None
                session_holder[1] = None

            attempt_diag["status"] = "error"
            attempt_diag["error"] = _exception_close_details(exc)
            attempt_diag["retryable"] = is_retryable_live_error(exc)
            attempt_diag["attempt_wall_seconds"] = round(
                asyncio.get_running_loop().time() - started, 3
            )
            attempt_diag["completed_at_utc"] = _utc_now()
            write_live_diagnostics(diagnostics_path, diagnostics)

            if (
                not attempt_diag["retryable"]
                or attempt >= LIVE_MAX_ATTEMPTS
            ):
                diagnostics["failed_scene_id"] = scene_id
                diagnostics["status"] = "failed"
                write_live_diagnostics(diagnostics_path, diagnostics)
                raise

            delay = LIVE_RETRY_BACKOFF_SECONDS[
                min(attempt - 1, len(LIVE_RETRY_BACKOFF_SECONDS) - 1)
            ]
            attempt_diag["retry_delay_seconds"] = delay
            write_live_diagnostics(diagnostics_path, diagnostics)
            print(
                f"    [Gemini Live] {scene_id}: falha transitória "
                f"({attempt_diag['error']['message']}); nova sessão em "
                f"{delay}s.",
                flush=True,
            )
            await asyncio.sleep(delay)

    raise RuntimeError(f"Retries esgotados para {scene_id}.")  # pragma: no cover


async def synthesize_missing_jobs(
    jobs: list[dict],
    *,
    gemini_key: str,
    voice: str,
    pronunciations: dict[str, str],
    speech_fingerprint: str,
    diagnostics_path: Path,
) -> dict[str, dict]:
    sdk_version = installed_google_genai_version()
    if sdk_version != GOOGLE_GENAI_REQUIRED_VERSION:
        raise RuntimeError(
            "Versão google-genai incompatível com Gemini 3.8 Live: "
            f"instalada={sdk_version}, exigida={GOOGLE_GENAI_REQUIRED_VERSION}."
        )

    diagnostics = {
        "version": "gemini-live-diagnostics-v1",
        "model": PRIMARY_TTS_MODEL,
        "voice": voice,
        "sdk_package": "google-genai",
        "sdk_version": sdk_version,
        "session_strategy": "continuous-multi-turn-with-scene-checkpoints",
        "temperature_mode": "provider-default",
        "session_resumption_enabled": False,
        "max_attempts_per_scene": LIVE_MAX_ATTEMPTS,
        "retry_backoff_seconds": list(LIVE_RETRY_BACKOFF_SECONDS),
        "first_audio_timeout_seconds": LIVE_FIRST_AUDIO_TIMEOUT_SECONDS,
        "stream_idle_timeout_seconds": LIVE_STREAM_IDLE_TIMEOUT_SECONDS,
        "post_generation_grace_seconds": LIVE_POST_GENERATION_GRACE_SECONDS,
        "accept_generation_complete_without_turn_complete":
            LIVE_ACCEPT_GENERATION_COMPLETE_WITHOUT_TURN_COMPLETE,
        "requested_scene_ids": [job["scene_id"] for job in jobs],
        "completed_scene_ids": [],
        "attempts": [],
        "status": "running" if jobs else "no-requests",
    }
    write_live_diagnostics(diagnostics_path, diagnostics)
    if not jobs:
        return {}

    from google import genai

    client = genai.Client(api_key=gemini_key)
    config = live_session_config(voice, pronunciations)
    completed: dict[str, dict] = {}
    session_holder = [None, None]
    previous_context = None

    try:
        for position, job in enumerate(jobs):
            scene_id = job["scene_id"]
            reusing = session_holder[1] is not None
            print(
                f"  [Gemini Live {position + 1}/{len(jobs)}] {scene_id}: "
                f"{'reaproveitando sessão contínua...' if reusing else 'abrindo sessão...'}",
                flush=True,
            )
            completed[scene_id] = await _synthesize_scene_with_retries(
                client=client,
                job=job,
                config=config,
                voice=voice,
                pronunciations=pronunciations,
                speech_fingerprint=speech_fingerprint,
                diagnostics=diagnostics,
                diagnostics_path=diagnostics_path,
                session_holder=session_holder,
                previous_context=previous_context,
            )
            previous_context = job["narration"]
    finally:
        if session_holder[0] is not None:
            try:
                await session_holder[0].__aexit__(None, None, None)
            except Exception:
                pass

    diagnostics["status"] = "success"
    write_live_diagnostics(diagnostics_path, diagnostics)
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
    parser.add_argument("--diagnostics")
    args = parser.parse_args()

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        raise RuntimeError(
            "GEMINI_API_KEY não disponível; este render exige Gemini Live."
        )

    payload = normalize_project(json.loads(Path(args.input).read_text(encoding="utf-8")))
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
    if presenter_key not in PRESENTER_VOICES:
        raise ValueError("Apresentador não previsto na política vocal.")
    project_voice = PRESENTER_VOICES[presenter_key]
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
        # Check normalization dependencies before spending any Live requests.
        canonical_tokens(narration, {**pronunciations, **scene_voice_direction(scene).get("pronunciations", {})})
        jobs.append({
            "scene": scene,
            "scene_index": scene_index,
            "scene_id": scene_id,
            "narration": narration,
            "narration_hash": hashlib.sha256(
                narration.encode("utf-8")
            ).hexdigest(),
            "output_file": output_dir / f"{scene_id}.wav",
            "direction": scene_voice_direction(scene),
            "direction_fingerprint": scene_direction_fingerprint(scene),
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
            narration=job["narration"],
            pronunciations={**pronunciations, **job["direction"].get("pronunciations", {})},
            direction_fingerprint=job["direction_fingerprint"],
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

    diagnostics_path = (
        Path(args.diagnostics)
        if args.diagnostics
        else Path(args.manifest).with_name("daily-live-diagnostics.json")
    )
    generated = asyncio.run(
        synthesize_missing_jobs(
            missing,
            gemini_key=gemini_key,
            voice=project_voice,
            pronunciations=pronunciations,
            speech_fingerprint=speech_fingerprint,
            diagnostics_path=diagnostics_path,
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
        "delivery_version": "gemini-live-v4-continuous-session-diagnostics",
        "live_sdk_version": installed_google_genai_version(),
        "live_session_strategy": "continuous-multi-turn-with-scene-checkpoints",
        "live_temperature_mode": "provider-default",
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
            "scene_direction_fingerprint": job["direction_fingerprint"],
            "scene_voice_direction": job["direction"],
            "output_fidelity": evaluate_transcription(job["narration"], sidecar.get("output_transcription") or "", {**pronunciations, **job["direction"].get("pronunciations", {})}, MINIMUM_TRANSCRIPTION_SIMILARITY),
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
