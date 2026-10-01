"""Validate the shared voice contract without provider calls or dependencies."""

from pathlib import Path

from tts_config import (
    VOICE_POLICY, TTS_MODEL_CASCADE, PRESENTER_VOICES, VOICE_POLICY_VERSION,
    VOICE_LANGUAGE, VOICE_DELIVERY_STYLE, gemini_speech_request,
    voice_policy_fingerprint,
)


def validate():
    if not VOICE_POLICY_VERSION or VOICE_LANGUAGE != "pt-BR" or not VOICE_DELIVERY_STYLE.strip():
        raise RuntimeError("Política de voz exige versão, português brasileiro e direção explícita.")
    if VOICE_POLICY.get("raw_audio_treatment") != "none":
        raise RuntimeError("O cache deve preservar áudio sem tratamento prévio.")
    if not set(TTS_MODEL_CASCADE) == set(VOICE_POLICY["models"]):
        raise RuntimeError("Cascata e adapters devem definir os mesmos modelos.")
    if set(VOICE_POLICY["fallback_failures"]) != {"rpd", "rate-limit-persistent", "server-unavailable", "request-timeout"}:
        raise RuntimeError("Fallback só deve ocorrer após falhas elegíveis confirmadas.")
    if PRESENTER_VOICES != {"male": "Charon", "female": "Autonoe"}:
        raise RuntimeError("Política vocal alterou as vozes aprovadas do canal.")
    sample = "Teste literal da narração: dólar a cinco reais."
    fingerprints = set()
    for model in TTS_MODEL_CASCADE:
        for voice in PRESENTER_VOICES.values():
            endpoint, payload = gemini_speech_request(sample, voice, model)
            if not endpoint.startswith("https://generativelanguage.googleapis.com/v1beta/"):
                raise RuntimeError("Endpoint de voz não pertence ao serviço Gemini configurado.")
            spec = VOICE_POLICY["models"][model]
            if spec["endpoint"] == "interactions":
                content = payload["input"][0]["content"][0]
                config = payload["generation_config"]["speech_config"][0]
                if content["text"] != sample or content["annotations"][0]["style"] != VOICE_DELIVERY_STYLE or config != {"voice": voice, "language": VOICE_LANGUAGE}:
                    raise RuntimeError("Adapter Interactions diverge da política vocal.")
            else:
                text = payload["contents"][0]["parts"][0]["text"]
                actual_voice = payload["generationConfig"]["speechConfig"]["voiceConfig"]["prebuiltVoiceConfig"]["voiceName"]
                if f"<transcript>\n{sample}\n</transcript>" not in text or VOICE_DELIVERY_STYLE not in text or actual_voice != voice:
                    raise RuntimeError("Adapter legado diverge da direção/transcrição/voz aprovadas.")
            fingerprints.add(voice_policy_fingerprint(model, voice))
    if len(fingerprints) != len(TTS_MODEL_CASCADE) * len(PRESENTER_VOICES):
        raise RuntimeError("Fingerprint não distingue voz e adapter de cada modelo.")
    root = Path(__file__).resolve().parent.parent
    for path in ("AGENTS.md", "prompts/daily-editorial.md", "docs/tts.md", "docs/editorial-voice.md"):
        if "worker/voice-policy.json" not in (root / path).read_text(encoding="utf-8"):
            raise RuntimeError(f"Instrução não referencia a política canônica: {path}")
    print(f"Voice policy {VOICE_POLICY_VERSION}: cascade, adapters, presets and instructions valid.")


if __name__ == "__main__":
    validate()
