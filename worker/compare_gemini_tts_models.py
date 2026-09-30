"""One-call-per-model listening test for the same Charon narration.

This is deliberately separate from the daily rendering pipeline. It never
retries, changes voices, or uploads anything outside the GitHub Actions artifact.
"""

import argparse
import base64
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import re
import sys
import time
import wave


MODELS = (
    "gemini-3.8-flash-tts",
    "gemini-3.8-flash-lite-tts",
    "gemini-3.1-flash-tts-preview",
)
VOICE = "Charon"
TEXT = (
    "O dólar caiu para cinco reais e vinte centavos. Mas o preço do pão depende "
    "também do trigo, do frete e do tempo. É assim que o dinheiro chega ao seu dia a dia."
)
MINIMUM_INTERVAL_SECONDS = 22.0
HOST = "generativelanguage.googleapis.com"


def payload_for(model: str) -> dict:
    # Match the single-speaker payload that already worked in production.
    # The 3.1 preview also documents this prebuilt voice form.
    voice_config = {"prebuiltVoiceConfig": {"voiceName": VOICE}}
    return {
        "contents": [{"role": "user", "parts": [{"text": TEXT}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": voice_config},
        },
    }


def post_once(model: str, api_key: str) -> tuple[int, bytes]:
    """Send precisely one POST; http.client does not follow redirects or retry."""
    connection = http.client.HTTPSConnection(HOST, timeout=120)
    try:
        connection.request(
            "POST",
            f"/v1beta/models/{model}:generateContent",
            body=json.dumps(payload_for(model), ensure_ascii=False).encode("utf-8"),
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json; charset=utf-8",
            },
        )
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def api_failure(status: int, response_body: bytes) -> dict:
    """Keep structured quota identifiers; never put arbitrary API text in logs."""
    result = {"status": "error", "http_status": status}
    try:
        body = json.loads(response_body)
        error = body.get("error", {})
        api_status = error.get("status", "")
        if isinstance(api_status, str) and re.fullmatch(r"[A-Z_]{1,64}", api_status):
            result["api_status"] = api_status
        quota_ids = []
        for detail in error.get("details", []):
            if detail.get("@type") != "type.googleapis.com/google.rpc.QuotaFailure":
                continue
            for violation in detail.get("violations", []):
                quota_id = violation.get("quotaId", "")
                if isinstance(quota_id, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", quota_id):
                    quota_ids.append(quota_id)
        if quota_ids:
            result["quota_ids"] = quota_ids[:5]
    except (TypeError, ValueError, AttributeError):
        pass
    return result


def wav_from_response(response_body: bytes, model: str) -> tuple[bytes, float, str]:
    body = json.loads(response_body)
    candidates = body.get("candidates") or []
    if not candidates:
        raise ValueError("Resposta sem áudio")
    parts = candidates[0].get("content", {}).get("parts") or []
    inline = next((part.get("inlineData") for part in parts if part.get("inlineData")), None)
    if not isinstance(inline, dict) or not inline.get("data"):
        raise ValueError("Resposta sem áudio")
    audio = base64.b64decode(inline["data"], validate=True)
    mime_type = inline.get("mimeType", "")
    if not isinstance(mime_type, str):
        mime_type = ""
    is_legacy_pcm = not mime_type and model == "gemini-3.1-flash-tts-preview"
    if audio.startswith(b"RIFF") and audio[8:12] == b"WAVE":
        wav_bytes = audio
    elif (model_is_pcm(mime_type) or is_legacy_pcm) and len(audio) >= 2000 and len(audio) % 2 == 0:
        sample_rate_match = re.search(r"(?:^|;)\s*rate=(\d+)", mime_type, re.IGNORECASE)
        sample_rate = int(sample_rate_match.group(1)) if sample_rate_match else 24000
        if not 8000 <= sample_rate <= 96000:
            raise ValueError("Taxa PCM inesperada")
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio)
        wav_bytes = buffer.getvalue()
    else:
        raise ValueError("Formato de áudio não suportado")
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        duration = wav_file.getnframes() / wav_file.getframerate()
    if duration < 0.1:
        raise ValueError("Áudio vazio")
    return wav_bytes, round(duration, 3), mime_type


def model_is_pcm(mime_type: str) -> bool:
    return mime_type.lower().startswith(("audio/l16", "audio/pcm"))


def run(output_dir: Path, api_key: str) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "purpose": "Comparação auditiva do preset Charon entre modelos Gemini TTS",
        "voice": VOICE,
        "text": TEXT,
        "minimum_request_start_interval_seconds": MINIMUM_INTERVAL_SECONDS,
        "maximum_attempts_per_model": 1,
        "results": [],
    }
    last_started_at = None
    for model in MODELS:
        item = {"model": model, "voice": VOICE, "attempts": 0}
        if not api_key:
            item.update({"status": "not_attempted", "reason": "GEMINI_API_KEY ausente"})
            manifest["results"].append(item)
            continue
        if last_started_at is not None:
            remaining = MINIMUM_INTERVAL_SECONDS - (time.monotonic() - last_started_at)
            if remaining > 0:
                time.sleep(remaining)
        last_started_at = time.monotonic()
        item["attempts"] = 1
        print(f"Testando {model} com {VOICE} (uma tentativa)...", flush=True)
        try:
            status, response_body = post_once(model, api_key)
            if status != 200:
                item.update(api_failure(status, response_body))
            else:
                wav_bytes, duration, mime_type = wav_from_response(response_body, model)
                filename = f"{model}-Charon.wav"
                (output_dir / filename).write_bytes(wav_bytes)
                item.update({
                    "status": "ok",
                    "file": filename,
                    "duration_seconds": duration,
                    "source_mime_type": mime_type,
                    "sha256": hashlib.sha256(wav_bytes).hexdigest(),
                })
        except Exception as exc:
            item.update({"status": "error", "reason": type(exc).__name__})
        manifest["results"].append(item)
        print(f"{model}: {item['status']}", flush=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = run(args.output_dir, os.environ.get("GEMINI_API_KEY", "").strip())
    return 0 if all(item["status"] == "ok" for item in manifest["results"]) else 1


if __name__ == "__main__":
    sys.exit(main())
