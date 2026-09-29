import argparse
import base64
import json
import os
import subprocess
import time
import wave
from pathlib import Path
import requests

VOICES = [
    # Masculinas
    {
        "id": "M1",
        "gender": "masculina",
        "voice": "Puck",
        "label": "Puck (Jovem, dinâmico e conversacional - estilo Creator)",
        "description": "Tom moderno, ágil e descontraído, ótimo para YouTube."
    },
    {
        "id": "M2",
        "gender": "masculina",
        "voice": "Charon",
        "label": "Charon (Firme, encorpado e informativo - estilo Âncora)",
        "description": "Tom maduro, seguro e confiável para análises de mercado."
    },
    {
        "id": "M3",
        "gender": "masculina",
        "voice": "Fenrir",
        "label": "Fenrir (Vibrante, enérgico e assertivo)",
        "description": "Tom expressivo e marcante para notícias quentes."
    },
    {
        "id": "M4",
        "gender": "masculina",
        "voice": "Orus",
        "label": "Orus (Sóbrio, equilibrado e institucional)",
        "description": "Tom neutro e profissional."
    },
    {
        "id": "M5",
        "gender": "masculina",
        "voice": "Enceladus",
        "label": "Enceladus (Tranquilo, pausado e didático)",
        "description": "Tom suave e explicativo para tutoriais e conceitos."
    },
    # Femininas
    {
        "id": "F1",
        "gender": "feminina",
        "voice": "Aoede",
        "label": "Aoede (Natural, calorosa e fluida - alta expressividade)",
        "description": "Uma das vozes mais naturais em português brasileiro, tom empático e envolvente."
    },
    {
        "id": "F2",
        "gender": "feminina",
        "voice": "Kore",
        "label": "Kore (Firme, moderna, segura e articulada)",
        "description": "Dicção muito clara, autoridade amigável para finanças."
    },
    {
        "id": "F3",
        "gender": "feminina",
        "voice": "Zephyr",
        "label": "Zephyr (Brilhante, alegre e cativante)",
        "description": "Tom leve, comunicativo e dinâmico."
    },
    {
        "id": "F4",
        "gender": "feminina",
        "voice": "Leda",
        "label": "Leda (Jovem, empática e descontraída)",
        "description": "Tom amigável em formato de conversa próxima."
    },
    {
        "id": "F5",
        "gender": "feminina",
        "voice": "Autonoe",
        "label": "Autonoe (Refinada, jornalística e clara)",
        "description": "Postura jornalística elegante com articulação precisa."
    },
]

TEST_TEXT = (
    "Fala, pessoal! Hoje eu quero te mostrar o que mudou com as bets e por que isso mexe "
    "diretamente com o seu dinheiro. Quando eu digo bets, estou falando das plataformas de apostas de quota fixa. "
    "E tem mais: fintech, Pix, spread bancário, holding e inteligência artificial são termos que aparecem "
    "o tempo todo quando a gente explica dinheiro no Brasil. Imagine um saldo de mil duzentos e cinquenta reais. "
    "O prazo vai até cinco de outubro, e a devolução pode acontecer entre nove e quatorze de outubro. "
    "Parece simples, mas tem um detalhe nos bastidores que muda tudo. E é justamente isso que eu vou te explicar agora."
)


def synthesize_gemini(text: str, voice_name: str, api_key: str, output_path: Path) -> str:
    models_to_try = ["gemini-2.0-flash", "gemini-2.0-flash-exp"]
    last_error = None

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "Você é um motor de Text-to-Speech de alto nível em português do Brasil para o canal O Dinheiro Explica. "
                            "Sua única tarefa é narrar em voz alta exatamente o texto fornecido pelo usuário, com entonação humana impecável, ritmo natural, clareza e expressividade. "
                            "NUNCA adicione palavras antes ou depois. NUNCA diga saudações adicionais nem 'Claro', 'Aqui está' ou comentários. Apenas leia o texto fornecido."
                        )
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": text}]
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
                        raise RuntimeError(f"Resposta do Gemini não contém inlineData de áudio: {data}")

                    b64_audio = audio_part["inlineData"]["data"]
                    mime_type = audio_part["inlineData"].get("mimeType", "")
                    raw_bytes = base64.b64decode(b64_audio)

                    # Salva arquivo temporário de áudio
                    temp_wav = output_path.with_suffix(".temp.wav")
                    if raw_bytes.startswith(b"RIFF") or "wav" in mime_type:
                        temp_wav.write_bytes(raw_bytes)
                    elif raw_bytes.startswith(b"ID3") or raw_bytes[:2] == b"\xff\xfb" or "mp3" in mime_type:
                        output_path.write_bytes(raw_bytes)
                        return output_path.name
                    else:
                        # Raw PCM 24000Hz 16-bit mono
                        with wave.open(str(temp_wav), "wb") as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)
                            wf.setframerate(24000)
                            wf.writeframes(raw_bytes)

                    # Converte para MP3 com ffmpeg se disponível
                    try:
                        subprocess.run(
                            ["ffmpeg", "-y", "-i", str(temp_wav), "-b:a", "192k", str(output_path)],
                            check=True,
                            capture_output=True
                        )
                        temp_wav.unlink(missing_ok=True)
                        return output_path.name
                    except Exception:
                        # Se ffmpeg falhar, renomeia para wav
                        final_wav = output_path.with_suffix(".wav")
                        temp_wav.rename(final_wav)
                        return final_wav.name

                elif response.status_code in (429, 500, 503):
                    time.sleep(3 * attempt)
                    continue
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    break
            except Exception as exc:
                last_error = exc
                time.sleep(2 * attempt)

    raise RuntimeError(f"Falha ao sintetizar voz '{voice_name}': {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY não configurada no ambiente.")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for candidate in VOICES:
        item = dict(candidate)
        filename = f"{candidate['id']}_{candidate['voice']}.mp3"
        output_file = output_dir / filename
        item["file"] = filename

        print(f"[Gemini TTS] Testando voz {candidate['id']} - {candidate['label']}...", flush=True)
        try:
            actual_filename = synthesize_gemini(TEST_TEXT, candidate["voice"], api_key, output_file)
            item["file"] = actual_filename
            item["status"] = "ok"
            print(f"[Gemini TTS]  Sucesso: {actual_filename}", flush=True)
        except Exception as exc:
            item["status"] = "erro"
            item["error"] = str(exc)
            print(f"[Gemini TTS] ❌ Falhou: {exc}", flush=True)

        results.append(item)
        time.sleep(2)  # Respeita o limite de requisições por minuto

    ok_count = sum(1 for r in results if r["status"] == "ok")
    if ok_count == 0:
        raise RuntimeError("Nenhuma voz do Gemini foi sintetizada com sucesso.")

    manifest = {
        "purpose": "Escolha do apresentador masculino e da apresentadora feminina para O Dinheiro Explica usando Google Gemini 2.0.",
        "instruction": "Ouça os áudios e selecione 1 voz masculina (M1 a M5) e 1 voz feminina (F1 a F5).",
        "test_text": TEST_TEXT,
        "voices": results,
    }
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = output_dir / "LEIA-ME.txt"
    lines = [
        "============================================================",
        "TESTE DE VOZES GOOGLE GEMINI 2.0 - O DINHEIRO EXPLICA",
        "============================================================",
        "",
        "Instruções:",
        "1. Ouça as amostras nas pastas 'Masculinas' e 'Femininas'.",
        "2. Escolha o apresentador masculino e a apresentadora feminina preferidos.",
        "",
        "Todas as vozes leram rigorosamente o mesmo roteiro com termos do canal",
        "(bets, fintech, Pix, spread bancário, holding, IA, valores e datas).",
        "",
        "--- VOZES MASCULINAS ---",
    ]
    for item in results:
        if item["gender"] == "masculina":
            status = "OK" if item["status"] == "ok" else "FALHOU"
            lines.append(f"[{item['id']}] {item['label']} - Status: {status}")
            lines.append(f"     Detalhe: {item['description']}")
            lines.append("")

    lines.append("--- VOZES FEMININAS ---")
    for item in results:
        if item["gender"] == "feminina":
            status = "OK" if item["status"] == "ok" else "FALHOU"
            lines.append(f"[{item['id']}] {item['label']} - Status: {status}")
            lines.append(f"     Detalhe: {item['description']}")
            lines.append("")

    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[Gemini TTS] Concluído! {ok_count}/{len(VOICES)} vozes geradas com sucesso.", flush=True)


if __name__ == "__main__":
    main()
