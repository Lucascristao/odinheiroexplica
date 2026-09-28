from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

SAMPLE_TEXT = """
Imagine descobrir que a parte mais famosa de uma empresa não é a que realmente coloca mais dinheiro no caixa.
É justamente aí que os números começam a contar uma história diferente.
Hoje, O Dinheiro Explica mostra de onde vem o dinheiro, o que mudou e por que isso importa.
""".strip()

VOICES = ["pf_dora", "pm_alex", "pm_santa"]
OUTPUT_DIR = Path("artifacts/voice-tests")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="p", device="cpu")

    for voice in VOICES:
        chunks = []
        for result in pipeline(
            SAMPLE_TEXT,
            voice=voice,
            speed=1.0,
            split_pattern=r"\n+",
        ):
            audio = getattr(result, "audio", None)
            if audio is None:
                continue

            if hasattr(audio, "detach"):
                audio = audio.detach().cpu().numpy()

            chunks.append(np.asarray(audio, dtype=np.float32))

        if not chunks:
            raise RuntimeError(f"Nenhum áudio gerado para {voice}")

        full_audio = np.concatenate(chunks)
        output = OUTPUT_DIR / f"{voice}.wav"
        sf.write(output, full_audio, 24000)
        print(f"Gerado: {output}")


if __name__ == "__main__":
    main()
