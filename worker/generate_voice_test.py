import argparse
import json
import os
from pathlib import Path
from xml.sax.saxutils import escape

import requests


VOICES = [
    {"id": "M1", "gender": "masculina", "voice": "pt-BR-MacerioMultilingualNeural", "label": "Macerio Multilingual (voz atual)"},
    {"id": "M2", "gender": "masculina", "voice": "pt-BR-Macerio:DragonHDLatestNeural", "label": "Macerio HD"},
    {"id": "M3", "gender": "masculina", "voice": "pt-BR-AntonioNeural", "label": "Antonio"},
    {"id": "M4", "gender": "masculina", "voice": "pt-BR-FabioNeural", "label": "Fabio"},
    {"id": "F1", "gender": "feminina", "voice": "pt-BR-ThalitaMultilingualNeural", "label": "Thalita Multilingual"},
    {"id": "F2", "gender": "feminina", "voice": "pt-BR-Thalita:DragonHDLatestNeural", "label": "Thalita HD"},
    {"id": "F3", "gender": "feminina", "voice": "pt-BR-FranciscaNeural", "label": "Francisca"},
    {"id": "F4", "gender": "feminina", "voice": "pt-BR-ManuelaNeural", "label": "Manuela"},
]

TEST_TEXT = (
    "Fala, pessoal. Hoje eu quero te mostrar o que mudou com as bets e por que isso mexe "
    "diretamente com o dinheiro que ficou nessas plataformas. Quando eu digo bets, eu estou "
    "falando das plataformas de apostas de quota fixa. E tem mais: fintech, Pix, spread, holding "
    "e inteligência artificial são termos que aparecem o tempo todo quando a gente explica dinheiro "
    "no Brasil. Imagine um saldo de mil duzentos e cinquenta reais. O prazo vai até cinco de outubro, "
    "e a devolução pode acontecer entre nove e quatorze de outubro. Parece simples, mas tem um detalhe "
    "que muda tudo. E é justamente isso que eu vou te explicar agora."
)


def ssml(text: str, voice: str) -> str:
    return f"""<speak version="1.0"
  xmlns="http://www.w3.org/2001/10/synthesis"
  xml:lang="pt-BR">
  <voice xml:lang="pt-BR" name="{voice}">
    <prosody rate="-2%" pitch="0%">{escape(text)}</prosody>
  </voice>
</speak>"""


def synthesize(text: str, voice: str, output: Path, key: str, region: str) -> None:
    endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    response = requests.post(
        endpoint,
        headers={
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
            "User-Agent": "odinheiroexplica-voice-test",
        },
        data=ssml(text, voice).encode("utf-8"),
        timeout=90,
    )
    response.raise_for_status()
    output.write_bytes(response.content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    key = os.environ["AZURE_SPEECH_KEY"].strip()
    region = os.environ["AZURE_SPEECH_REGION"].strip()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for candidate in VOICES:
        filename = f"{candidate['id']}_{candidate['label'].replace(' ', '_').replace('(', '').replace(')', '')}.mp3"
        output = output_dir / filename
        item = dict(candidate)
        item["file"] = filename
        try:
            print(f"[TTS] Gerando {candidate['id']} - {candidate['label']}...", flush=True)
            synthesize(TEST_TEXT, candidate["voice"], output, key, region)
            item["status"] = "ok"
        except Exception as exc:
            item["status"] = "erro"
            item["error"] = f"{type(exc).__name__}: {exc}"
            print(f"[TTS] Falhou {candidate['id']}: {exc}", flush=True)
        results.append(item)

    if not any(item["status"] == "ok" for item in results):
        raise RuntimeError("Nenhuma voz foi gerada com sucesso.")

    manifest = {
        "purpose": "Escolher um apresentador masculino e uma apresentadora feminina para O Dinheiro Explica.",
        "instruction": "Ouça os arquivos e escolha um código masculino (M1-M4) e um feminino (F1-F4).",
        "test_text": TEST_TEXT,
        "voices": results,
    }
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = output_dir / "LEIA-ME.txt"
    lines = [
        "TESTE DE VOZ - O DINHEIRO EXPLICA",
        "",
        "Escolha 1 voz masculina e 1 feminina pelo código.",
        "O teste usa o mesmo texto, velocidade e pitch para todas as vozes.",
        "A palavra 'bets' está sem correção fonética de propósito, para compararmos como cada voz lida com ela.",
        "Depois da escolha, o pipeline aplicará um dicionário de pronúncia para termos problemáticos.",
        "",
    ]
    for item in results:
        status = "OK" if item["status"] == "ok" else "FALHOU"
        lines.append(f"{item['id']} - {item['label']} - {status}")
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
