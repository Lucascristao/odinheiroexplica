import html
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
    {
        "slug": "nicolau",
        "label": "Nicolau",
        "voice": "pt-BR-NicolauNeural",
        "group": "Referência",
        "optional": False,
    },
    {
        "slug": "antonio",
        "label": "Antonio",
        "voice": "pt-BR-AntonioNeural",
        "group": "Neural padrão",
        "optional": False,
    },
    {
        "slug": "donato",
        "label": "Donato",
        "voice": "pt-BR-DonatoNeural",
        "group": "Neural padrão",
        "optional": False,
    },
    {
        "slug": "humberto",
        "label": "Humberto",
        "voice": "pt-BR-HumbertoNeural",
        "group": "Neural padrão",
        "optional": False,
    },
    {
        "slug": "julio",
        "label": "Julio",
        "voice": "pt-BR-JulioNeural",
        "group": "Neural padrão",
        "optional": False,
    },
    {
        "slug": "valerio",
        "label": "Valerio",
        "voice": "pt-BR-ValerioNeural",
        "group": "Neural padrão",
        "optional": False,
    },
    {
        "slug": "macerio",
        "label": "Macerio",
        "voice": "pt-BR-MacerioMultilingualNeural",
        "group": "Multilingual",
        "optional": False,
    },
    {
        "slug": "caio-hd",
        "label": "Caio HD",
        "voice": "pt-BR-Caio:MAI-Voice-2",
        "group": "Neural HD",
        "optional": True,
    },
    {
        "slug": "pedro-hd",
        "label": "Pedro HD",
        "voice": "pt-BR-Pedro:MAI-Voice-2",
        "group": "Neural HD",
        "optional": True,
    },
    {
        "slug": "rafael-hd",
        "label": "Rafael HD",
        "voice": "pt-BR-Rafael:MAI-Voice-2",
        "group": "Neural HD",
        "optional": True,
    },
    {
        "slug": "luana-hd",
        "label": "Luana HD",
        "voice": "pt-BR-Luana:MAI-Voice-2",
        "group": "Neural HD",
        "optional": True,
    },
]

OUTPUT_DIR = Path("public/voice-tests")


def endpoint() -> str:
    return (
        f"https://{SPEECH_REGION}.tts.speech.microsoft.com/"
        "cognitiveservices/v1"
    )


def synthesize(item: dict) -> tuple[bool, str]:
    ssml = f"""<speak version="1.0"
  xmlns="http://www.w3.org/2001/10/synthesis"
  xmlns:mstts="http://www.w3.org/2001/mstts"
  xml:lang="pt-BR">
  <voice xml:lang="pt-BR" name="{item['voice']}">
    <prosody rate="-2%" pitch="0%">
      {escape(SAMPLE_TEXT)}
    </prosody>
  </voice>
</speak>"""

    response = requests.post(
        endpoint(),
        headers={
            "Ocp-Apim-Subscription-Key": SPEECH_KEY,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
            "User-Agent": "odinheiroexplica-tts",
        },
        data=ssml.encode("utf-8"),
        timeout=90,
    )

    if response.status_code != 200:
        return False, f"HTTP {response.status_code}"

    output_path = OUTPUT_DIR / f"{item['slug']}.mp3"
    output_path.write_bytes(response.content)
    return True, "ok"


def build_page(results: list[dict]) -> None:
    groups: dict[str, list[dict]] = {}
    for result in results:
        groups.setdefault(result["group"], []).append(result)

    sections = []
    for group, items in groups.items():
        cards = []
        for item in items:
            if item["ok"]:
                body = (
                    f'<audio controls preload="metadata" '
                    f'src="./{html.escape(item["slug"])}.mp3"></audio>'
                )
                badge = '<span class="badge ok">Gerada</span>'
            else:
                body = (
                    '<div class="unavailable">'
                    'Não disponível neste recurso F0 ou nesta região.'
                    '</div>'
                )
                badge = '<span class="badge no">Indisponível</span>'

            cards.append(
                f"""
                <section class="voice">
                  <div class="voice-head">
                    <div>
                      <strong>{html.escape(item["label"])}</strong>
                      <span>{html.escape(item["voice"])}</span>
                    </div>
                    {badge}
                  </div>
                  {body}
                </section>
                """
            )

        sections.append(
            f"""
            <section class="group">
              <h2>{html.escape(group)}</h2>
              {''.join(cards)}
            </section>
            """
        )

    page = f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="robots" content="noindex,nofollow" />
    <title>Teste de vozes | O Dinheiro Explica</title>
    <style>
      :root {{
        font-family: Inter, system-ui, sans-serif;
        color: #f5f5f5;
        background: #090b0d;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        min-height: 100vh;
        padding: 30px 20px 70px;
      }}
      main {{
        width: min(800px, 100%);
        margin: 0 auto;
      }}
      h1 {{
        margin: 0 0 8px;
        font-size: clamp(28px, 5vw, 44px);
      }}
      .intro {{
        margin: 0 0 32px;
        color: #a5adb6;
        line-height: 1.6;
      }}
      .group {{
        margin-top: 30px;
      }}
      h2 {{
        margin: 0 0 12px;
        font-size: 16px;
        color: #d9dfe5;
      }}
      .voice {{
        padding: 18px;
        margin: 12px 0;
        border: 1px solid #282d33;
        border-radius: 16px;
        background: #111418;
      }}
      .voice-head {{
        display: flex;
        justify-content: space-between;
        gap: 16px;
        align-items: flex-start;
        margin-bottom: 13px;
      }}
      .voice strong {{
        display: block;
        color: #ffbd19;
        margin-bottom: 5px;
      }}
      .voice span {{
        display: block;
        color: #a5adb6;
        font-size: 13px;
      }}
      .badge {{
        padding: 5px 8px;
        border-radius: 999px;
        font-size: 11px !important;
        font-weight: 800;
        white-space: nowrap;
      }}
      .badge.ok {{
        color: #7ce0a0;
        background: rgba(124, 224, 160, .08);
      }}
      .badge.no {{
        color: #ffcc66;
        background: rgba(255, 204, 102, .08);
      }}
      .unavailable {{
        padding: 12px;
        border: 1px dashed #3b4148;
        border-radius: 10px;
        color: #a5adb6;
        font-size: 13px;
      }}
      audio {{ width: 100%; }}
    </style>
  </head>
  <body>
    <main>
      <h1>Teste de vozes brasileiras</h1>
      <p class="intro">
        Nicolau fica como referência. Abaixo estão as demais vozes masculinas
        disponíveis e as novas vozes HD que o recurso conseguir sintetizar.
      </p>
      {''.join(sections)}
    </main>
  </body>
</html>
"""
    (OUTPUT_DIR / "index.html").write_text(page, encoding="utf-8")


def main() -> None:
    if not SPEECH_KEY:
        raise RuntimeError("AZURE_SPEECH_KEY não configurado.")
    if not SPEECH_REGION:
        raise RuntimeError("AZURE_SPEECH_REGION não configurado.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    hard_failures = []

    for item in VOICES:
        ok, status = synthesize(item)
        print(f"{item['label']}: {status}")

        result = {**item, "ok": ok, "status": status}
        results.append(result)

        if not ok and not item["optional"]:
            hard_failures.append(f"{item['label']} ({status})")

    build_page(results)

    if hard_failures:
        raise RuntimeError(
            "Falha em vozes padrão: " + ", ".join(hard_failures)
        )


if __name__ == "__main__":
    main()
