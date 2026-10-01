"""Validate the canonical Gemini Live voice policy without provider calls."""

from pathlib import Path

from tts_config import (
    MINIMUM_TRANSCRIPTION_SIMILARITY,
    PRESENTER_VOICES,
    PRIMARY_TTS_MODEL,
    TTS_MODEL_CASCADE,
    VOICE_DELIVERY_STYLE,
    VOICE_LANGUAGE,
    VOICE_POLICY,
    VOICE_POLICY_VERSION,
    live_session_config,
    live_system_instruction,
    voice_policy_fingerprint,
)


def validate() -> None:
    if (
        not VOICE_POLICY_VERSION
        or VOICE_LANGUAGE != "pt-BR"
        or not VOICE_DELIVERY_STYLE.strip()
    ):
        raise RuntimeError(
            "Política exige versão, português brasileiro e direção vocal."
        )
    if VOICE_POLICY.get("raw_audio_treatment") != "none":
        raise RuntimeError("Áudio Gemini Live deve permanecer sem tratamento.")
    if TTS_MODEL_CASCADE != ("gemini-3.8-live",):
        raise RuntimeError("Somente gemini-3.8-live pode estar ativo.")
    if set(VOICE_POLICY["models"]) != {PRIMARY_TTS_MODEL}:
        raise RuntimeError("Política deve definir somente o adapter Live.")
    if VOICE_POLICY.get("fallback_failures") != []:
        raise RuntimeError("Gemini Live não deve alternar para outro modelo.")
    if PRESENTER_VOICES != {
        "male": "Charon",
        "female": "Autonoe",
    }:
        raise RuntimeError("Vozes aprovadas do canal foram alteradas.")
    if not 0.95 <= MINIMUM_TRANSCRIPTION_SIMILARITY <= 1.0:
        raise RuntimeError("Gate de fidelidade da transcrição é inválido.")

    fingerprints = set()
    for voice in PRESENTER_VOICES.values():
        config = live_session_config(voice, {"IBS": "i bê ésse"})
        if config["response_modalities"] != ["AUDIO"]:
            raise RuntimeError("Live deve responder somente em áudio.")
        actual_voice = (
            config["speech_config"]["voice_config"]
            ["prebuilt_voice_config"]["voice_name"]
        )
        if actual_voice != voice:
            raise RuntimeError("Preset Live diverge da voz aprovada.")
        if "output_audio_transcription" not in config:
            raise RuntimeError("Transcrição de saída deve estar ativada.")
        instruction = live_system_instruction({"IBS": "i bê ésse"})
        if (
            VOICE_DELIVERY_STYLE not in instruction
            or "IBS = i bê ésse" not in instruction
        ):
            raise RuntimeError("Direção vocal/pronúncia não chegou ao Live.")
        fingerprints.add(
            voice_policy_fingerprint(PRIMARY_TTS_MODEL, voice)
        )

    if len(fingerprints) != len(PRESENTER_VOICES):
        raise RuntimeError("Fingerprint não distingue as vozes.")

    root = Path(__file__).resolve().parent.parent
    for path in (
        "AGENTS.md",
        "prompts/daily-editorial.md",
        "docs/tts.md",
        "docs/editorial-voice.md",
    ):
        if "worker/voice-policy.json" not in (
            root / path
        ).read_text(encoding="utf-8"):
            raise RuntimeError(
                f"Instrução não referencia a política canônica: {path}"
            )

    print(
        f"Voice policy {VOICE_POLICY_VERSION}: Gemini 3.8 Live, "
        "single-model voices, literal-read gate and no DSP valid."
    )


if __name__ == "__main__":
    validate()
