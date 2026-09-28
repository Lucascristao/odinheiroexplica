import os
from pathlib import Path
from xml.sax.saxutils import escape

import requests

SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY", "").strip()
SPEECH_REGION = os.environ.get("AZURE_SPEECH_REGION", "").strip()

SAMPLE_TEXT = """
Imagine descobrir que a parte mais conhecida de uma empresa não é a que mais coloca dinheiro no caixa.
Quando um roteiro fala em Selic, Pix, EBITDA, Nubank, Banco Central, um bilhão e oitocentos milhões de reais ou doze vírgula sete por cento, a pronúncia precisa continuar natural.
Neste vídeo, vamos entender o que os números revelam e por que isso importa para quem acompanha empresas e economia.
""".strip()

VOICES = [
    ("francisca", "pt-BR-FranciscaNeural"),
    ("fabio", "pt-BR-FabioNeural"),
    ("nicolau", "pt-BR-NicolauNeural"),
]

OUTPUT_DIR = Path("public/voice-tests")


def synthesize(voice_name: str, output_name: str) -> None:
    endpoint = (
        f"https://{SPEECH_REGION}.tts.speech.microsoft.com/"
        "cognitiveservices/v1"
    )

    ssml = f"""<speak version="1.0" xml:lang="pt-BR">
  <voice name="{voice_name}">
    <prosody rate="-2%" pitch="0%">
      {escape(SAMPLE_TEXT)}
    </prosody>
  </voice>
</speak>"""

    response = requests.post(
        endpoint,
        headers={
            "Ocp-Apim-Subscription-Key": SPEECH_KEY,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
            "User-Agent": "odinheiroexplica-tts",
        },
        data=ssml.encode("utf-8"),
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Azure Speech falhou para {voice_name}: "
            f"{response.status_code} {response.text[:500]}"
        )

    output_path = OUTPUT_DIR / f"{output_name}.mp3"
    output_path.write_bytes(response.content)
    print(f"Gerado: {output_path} ({voice_name})")


def main() -> None:
    if not SPEECH_KEY:
        raise RuntimeError("AZURE_SPEECH_KEY não configurado.")
    if not SPEECH_REGION:
        raise RuntimeError("AZURE_SPEECH_REGION não configurado.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for output_name, voice_name in VOICES:
        synthesize(voice_name, output_name)


if __name__ == "__main__":
    main()
