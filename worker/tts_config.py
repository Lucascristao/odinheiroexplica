"""Canonical voice policy and the actual Gemini REST request adapters."""

import hashlib
import json
from pathlib import Path

VOICE_POLICY_PATH = Path(__file__).with_name("voice-policy.json")
VOICE_POLICY = json.loads(VOICE_POLICY_PATH.read_text(encoding="utf-8"))
VOICE_POLICY_VERSION = VOICE_POLICY["version"]
TTS_MODEL_CASCADE = tuple(VOICE_POLICY["model_cascade"])
if len(TTS_MODEL_CASCADE) != 3 or len(set(TTS_MODEL_CASCADE)) != 3:
    raise RuntimeError("Política de voz deve definir três modelos distintos em ordem.")
PRIMARY_TTS_MODEL, SECONDARY_TTS_MODEL, FALLBACK_TTS_MODEL = TTS_MODEL_CASCADE
ELIGIBLE_FALLBACK_FAILURES = frozenset(VOICE_POLICY["fallback_failures"])
PRESENTER_VOICES = {key: value["voice"] for key, value in VOICE_POLICY["presenters"].items()}
PRESENTER_NAMES = {key: value["name"] for key, value in VOICE_POLICY["presenters"].items()}
DEFAULT_PRESENTER = VOICE_POLICY["default_presenter"]
DEFAULT_TTS_VOICE = PRESENTER_VOICES[DEFAULT_PRESENTER]
VOICE_LANGUAGE = VOICE_POLICY["language"]
VOICE_DELIVERY_STYLE = VOICE_POLICY["delivery_style"]
NO_VOICE_TREATMENT = VOICE_POLICY["raw_audio_treatment"]
# Compatibility exports only: actual pace/pitch is directed semantically.
DEFAULT_TTS_RATE = "0%"
DEFAULT_TTS_PITCH = "0%"
GLOBAL_PRONUNCIATIONS = {}

def gemini_speech_request(narration: str, voice: str, model: str) -> tuple[str, dict]:
    """Separate transcript from direction using each model's documented API."""
    if model not in VOICE_POLICY["models"] or voice not in PRESENTER_VOICES.values():
        raise ValueError("Modelo ou voz não previsto na política de voz do canal.")
    spec = VOICE_POLICY["models"][model]
    style, language = VOICE_POLICY["delivery_style"], VOICE_POLICY["language"]
    base = "https://generativelanguage.googleapis.com/v1beta"
    if spec["endpoint"] == "interactions" and spec["style_transport"] == "speech_metadata":
        return f"{base}/interactions", {
            "model": model,
            "input": [{"type": "user_input", "content": [{
                "type": "text", "text": narration,
                "annotations": [{"type": "speech_metadata", "style": style}],
            }]}],
            "response_format": {"type": "audio", "mime_type": "audio/wav", "sample_rate": 24000},
            "generation_config": {"speech_config": [{"voice": voice, "language": language}]},
        }
    if spec["endpoint"] == "generate-content" and spec["style_transport"] == "directed_prompt":
        # 3.1 preview predates speech_metadata: direction precedes an unmodified
        # script. Neither instructions nor delimiters enter the narration hash.
        prompt = (
            f"Read aloud in Brazilian Portuguese ({language}). Delivery: {style}\n"
            "Speak only the transcript below, exactly as written. Do not read the "
            "instructions or the transcript delimiters. Do not add introductions, "
            "comments or a closing.\n<transcript>\n" + narration + "\n</transcript>"
        )
        return f"{base}/models/{model}:generateContent", {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
            },
        }
    raise RuntimeError("Adapter Gemini incompatível com a política de voz.")

def voice_policy_fingerprint(model: str, voice: str) -> str:
    """Invalidate audio whenever the actual non-transcript request changes."""
    endpoint, payload = gemini_speech_request("__VERBATIM_TRANSCRIPT__", voice, model)
    canonical = json.dumps({
        "version": VOICE_POLICY["version"], "endpoint": endpoint,
        "payload": payload, "raw_audio_treatment": VOICE_POLICY["raw_audio_treatment"],
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

VOICE_POLICY_CACHE_KEY = hashlib.sha256(json.dumps(
    VOICE_POLICY, ensure_ascii=False, sort_keys=True, separators=(",", ":")
).encode("utf-8")).hexdigest()[:16]
