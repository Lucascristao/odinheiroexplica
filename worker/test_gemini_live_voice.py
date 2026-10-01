"""Generate a small Gemini 3.8 Live / Charon narration sample for review."""

import argparse
import asyncio
from difflib import SequenceMatcher
import json
import os
from pathlib import Path
import re
import unicodedata
import wave

MODEL = "gemini-3.8-live"
VOICE = "Charon"
SAMPLE_RATE = 24000
CHANNELS = 1
SAMPLE_WIDTH = 2

DEFAULT_TEXT = (
    "No chamado Simples puro, a lógica continua mais próxima do que o pequeno "
    "negócio já conhece. IBS e CBS ficam dentro do DAS junto com os demais "
    "tributos abrangidos pelo regime. No chamado híbrido, a empresa continua "
    "no Simples, mas IBS e CBS passam a ser apurados pelas regras do regime regular."
)

SYSTEM_INSTRUCTION = (
    "Você é Roberto, narrador brasileiro do canal O Dinheiro Explica. "
    "Sua única tarefa nesta sessão é ler em voz alta, literalmente, o texto "
    "fornecido pelo usuário depois de ROTEIRO. Não cumprimente, não explique, "
    "não resuma, não reformule e não acrescente nenhuma palavra. "
    "Fale em português brasileiro, com naturalidade de conversa, ritmo moderado, "
    "articulação clara e sem tom de locutor publicitário. "
    "Pronuncie IBS como 'i bê ésse', CBS como 'cê bê ésse' e DAS como 'dás'."
)


def normalize_for_comparison(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.replace("i bê ésse", "ibs").replace("i be esse", "ibs")
    value = value.replace("cê bê ésse", "cbs").replace("ce be esse", "cbs")
    value = re.sub(r"\bdas\b", "das", value)
    return " ".join(re.findall(r"[a-z0-9]+", value))


def similarity(reference: str, transcript: str) -> float:
    left = normalize_for_comparison(reference)
    right = normalize_for_comparison(transcript)
    return round(SequenceMatcher(None, left, right).ratio(), 4)


def write_wav(path: Path, pcm: bytes) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(CHANNELS)
        handle.setsampwidth(SAMPLE_WIDTH)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm)


async def generate(api_key: str, text: str, output_wav: Path) -> dict:
    from google import genai

    client = genai.Client(api_key=api_key)
    config = {
        "response_modalities": ["AUDIO"],
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {"voice_name": VOICE}
            }
        },
        "output_audio_transcription": {},
        "system_instruction": SYSTEM_INSTRUCTION,
        "temperature": 0.1,
    }

    pcm_chunks: list[bytes] = []
    transcript_chunks: list[str] = []
    turn_complete = False

    async with client.aio.live.connect(model=MODEL, config=config) as session:
        await session.send_client_content(
            turns={
                "role": "user",
                "parts": [{"text": "ROTEIRO:\n" + text}],
            },
            turn_complete=True,
        )

        async for response in session.receive():
            server = getattr(response, "server_content", None)
            if server is None:
                continue

            model_turn = getattr(server, "model_turn", None)
            if model_turn is not None:
                for part in getattr(model_turn, "parts", []) or []:
                    inline = getattr(part, "inline_data", None)
                    data = getattr(inline, "data", None) if inline is not None else None
                    if data:
                        pcm_chunks.append(bytes(data))

            transcription = getattr(server, "output_transcription", None)
            transcript_text = getattr(transcription, "text", None) if transcription else None
            if transcript_text:
                transcript_chunks.append(str(transcript_text))

            if bool(getattr(server, "turn_complete", False)):
                turn_complete = True
                break

    pcm = b"".join(pcm_chunks)
    if len(pcm) < SAMPLE_RATE * SAMPLE_WIDTH:
        raise RuntimeError(
            f"Gemini Live retornou áudio insuficiente: {len(pcm)} bytes."
        )

    write_wav(output_wav, pcm)
    transcript = "".join(transcript_chunks).strip()
    duration = len(pcm) / (SAMPLE_RATE * CHANNELS * SAMPLE_WIDTH)

    return {
        "model": MODEL,
        "voice": VOICE,
        "sample_rate_hz": SAMPLE_RATE,
        "channels": CHANNELS,
        "sample_width_bytes": SAMPLE_WIDTH,
        "duration_seconds": round(duration, 3),
        "audio_bytes_pcm": len(pcm),
        "turn_complete": turn_complete,
        "reference_text": text,
        "output_transcription": transcript,
        "transcription_similarity": similarity(text, transcript) if transcript else None,
        "signal_processing": "none; raw 24 kHz PCM from Gemini Live wrapped in WAV",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--text")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY ausente.")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    text = (args.text or DEFAULT_TEXT).strip()

    wav_path = output_dir / "gemini-3.8-live-charon-raw.wav"
    metadata_path = output_dir / "gemini-3.8-live-charon.json"
    transcript_path = output_dir / "gemini-3.8-live-charon-transcript.txt"
    script_path = output_dir / "gemini-3.8-live-charon-script.txt"

    metadata = asyncio.run(generate(api_key, text, wav_path))
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    transcript_path.write_text(
        (metadata["output_transcription"] or "<sem transcrição>") + "\n",
        encoding="utf-8",
    )
    script_path.write_text(text + "\n", encoding="utf-8")

    print(json.dumps(metadata, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
