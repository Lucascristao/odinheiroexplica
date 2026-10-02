"""Generate a 3-scene continuous Gemini 3.8 Live / Charon narration sample for review."""

import argparse
import asyncio
from difflib import SequenceMatcher
import json
import math
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

DEFAULT_TEST_SCENES = [
    {
        "id": "scene-00",
        "narration": "O dinheiro físico está acabando? Se quase tudo cabe no celular, por que a dona do Banco24Horas quer investir em atendimento presencial? Parece uma contradição. Eu sou o Roberto, do O Dinheiro Explica.",
    },
    {
        "id": "scene-01",
        "narration": "Mas o plano da Tecban ajuda a enxergar uma mudança maior: o dinheiro pode perder espaço sem desaparecer, e o caixa eletrônico pode ganhar outras funções. Na pesquisa do Banco Central de dois mil e vinte e quatro, muita gente combina cédulas e meios digitais.",
    },
    {
        "id": "scene-02",
        "narration": "Por trás de um saque existe uma operação inteira. Dividindo o custo pelo número de saques, cada operação fica mais pesada quando o volume diminui. É por isso que a empresa precisa reorganizar como ganha dinheiro.",
    },
]

SYSTEM_INSTRUCTION = (
    "Você é Roberto, narrador brasileiro do canal O Dinheiro Explica. "
    "Sua única tarefa nesta sessão é ler em voz alta, literalmente, o texto "
    "fornecido pelo usuário depois de ROTEIRO. Não cumprimente, não explique, "
    "não resuma, não reformule e não acrescente nenhuma palavra além do roteiro. "
    "Fale em português brasileiro, com naturalidade de conversa calorosa, ritmo moderado, "
    "articulação clara e sem tom de locutor publicitário. "
    "Mantenha rigorosa estabilidade vocal: mesma afinação fundamental (pitch), "
    "mesmo volume de locução e mesmo timbre conversado natural ao longo de todas as falas. "
    "Pronuncie Tecban como 'téc ban' e Banco24Horas como 'banco vinte e quatro horas'."
)


def normalize_for_comparison(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.replace("tecban", "tec ban").replace("téc ban", "tec ban")
    value = value.replace("banco24horas", "banco vinte e quatro horas")
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


def analyze_pcm_audio(pcm: bytes) -> dict:
    if not pcm:
        return {"rms_dbfs": -99.0, "pitch_hz": 0.0}
    samples = [
        int.from_bytes(pcm[i:i + 2], byteorder="little", signed=True) / 32768.0
        for i in range(0, len(pcm), 2)
    ]
    sum_sq = sum(s * s for s in samples)
    rms = math.sqrt(sum_sq / max(1, len(samples)))
    rms_db = 20 * math.log10(rms) if rms > 1e-9 else -99.0

    min_lag = int(SAMPLE_RATE / 300)
    max_lag = int(SAMPLE_RATE / 70)
    frame_size = 1024
    hop_size = 512
    total_pitch = 0.0
    pitch_count = 0

    for offset in range(0, len(samples) - frame_size, hop_size):
        frame = samples[offset:offset + frame_size]
        f_rms = math.sqrt(sum(s * s for s in frame) / frame_size)
        if f_rms < 0.03:
            continue
        r0 = sum(s * s for s in frame)
        best_r = 0.0
        best_lag = -1
        for lag in range(min_lag, max_lag):
            r = sum(frame[i] * frame[i + lag] for i in range(frame_size - lag))
            if r > best_r:
                best_r = r
                best_lag = lag
        if best_lag > 0 and (best_r / max(1e-9, r0)) > 0.45:
            total_pitch += SAMPLE_RATE / best_lag
            pitch_count += 1

    avg_pitch = total_pitch / pitch_count if pitch_count > 0 else 0.0
    return {
        "rms_dbfs": round(rms_db, 2),
        "pitch_hz": round(avg_pitch, 1),
        "duration_seconds": round(len(samples) / SAMPLE_RATE, 2),
    }


async def generate_continuous_pilot(api_key: str, scenes: list[dict], output_dir: Path) -> dict:
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
    }

    results = []
    stitched_pcm = bytearray()
    previous_narration = None

    async with client.aio.live.connect(model=MODEL, config=config) as session:
        for idx, scene in enumerate(scenes):
            scene_id = scene["id"]
            narration = scene["narration"].strip()
            print(f"  [Live Continuous Pilot] Gerando {scene_id} ({idx + 1}/{len(scenes)})...", flush=True)

            turn_text = (
                f"INSTRUÇÕES: Leia apenas o ROTEIRO com estabilidade vocal de afinação e volume.\n\n"
                f"ROTEIRO:\n{narration}"
            )
            await session.send_client_content(
                turns={"role": "user", "parts": [{"text": turn_text}]},
                turn_complete=True,
            )

            pcm_chunks = []
            transcript_chunks = []
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
                    break

            pcm = b"".join(pcm_chunks)
            scene_wav = output_dir / f"{scene_id}.wav"
            write_wav(scene_wav, pcm)

            transcript = "".join(transcript_chunks).strip()
            metrics = analyze_pcm_audio(pcm)
            sim = similarity(narration, transcript)

            results.append({
                "scene_id": scene_id,
                "narration": narration,
                "transcript": transcript,
                "similarity": sim,
                "audio_metrics": metrics,
                "file": scene_wav.name,
            })

            # Small 50ms pause/padding between scenes in stitched track
            stitched_pcm.extend(pcm)
            stitched_pcm.extend(b"\x00" * int(SAMPLE_RATE * 0.05 * SAMPLE_WIDTH))
            previous_narration = narration

    raw_wav_path = output_dir / "gemini-3.8-live-charon-raw.wav"
    write_wav(raw_wav_path, bytes(stitched_pcm))

    # Calculate transition jumps
    transitions = []
    for i in range(len(results) - 1):
        m1 = results[i]["audio_metrics"]
        m2 = results[i + 1]["audio_metrics"]
        d_pitch = round(abs(m2["pitch_hz"] - m1["pitch_hz"]), 1)
        d_rms = round(abs(m2["rms_dbfs"] - m1["rms_dbfs"]), 2)
        transitions.append({
            "from": results[i]["scene_id"],
            "to": results[i + 1]["scene_id"],
            "delta_pitch_hz": d_pitch,
            "delta_rms_db": d_rms,
            "pitch_stable": d_pitch <= 8.0,
            "volume_stable": d_rms <= 1.5,
        })

    summary = {
        "model": MODEL,
        "voice": VOICE,
        "session_strategy": "continuous-multi-turn",
        "scenes_tested": len(results),
        "scenes": results,
        "transitions": transitions,
        "all_pitch_stable": all(t["pitch_stable"] for t in transitions),
        "all_volume_stable": all(t["volume_stable"] for t in transitions),
        "output_file": raw_wav_path.name,
    }
    return summary


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

    if args.text:
        scenes = [{"id": "scene-custom", "narration": args.text.strip()}]
    else:
        scenes = DEFAULT_TEST_SCENES

    summary = asyncio.run(generate_continuous_pilot(api_key, scenes, output_dir))

    metadata_path = output_dir / "gemini-3.8-live-charon.json"
    report_path = output_dir / "continuity-report.json"
    transcript_path = output_dir / "gemini-3.8-live-charon-transcript.txt"
    script_path = output_dir / "gemini-3.8-live-charon-script.txt"

    metadata_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(json.dumps(summary["transitions"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    transcript_path.write_text("\n\n".join(s["transcript"] for s in summary["scenes"]) + "\n", encoding="utf-8")
    script_path.write_text("\n\n".join(s["narration"] for s in summary["scenes"]) + "\n", encoding="utf-8")

    print("[Continuous Live Pilot] Concluído com sucesso!", flush=True)
    print(json.dumps(summary["transitions"], ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
