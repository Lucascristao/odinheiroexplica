import argparse
import math
import random
import struct
import wave
from pathlib import Path


SAMPLE_RATE = 48_000


def envelope(t: float, duration: float, attack: float, release: float) -> float:
    attack_gain = min(1.0, t / max(attack, 1e-6))
    release_gain = min(1.0, max(0.0, (duration - t) / max(release, 1e-6)))
    return attack_gain * release_gain


def write_wav(path: Path, samples: list[float]) -> None:
    peak = max((abs(sample) for sample in samples), default=1.0)
    normalization = 0.95 / max(1.0, peak)

    pcm = [
        max(-32767, min(32767, int(sample * normalization * 32767)))
        for sample in samples
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(struct.pack("<" + "h" * len(pcm), *pcm))


def tick(duration: float = 0.12) -> list[float]:
    samples = []
    for n in range(int(SAMPLE_RATE * duration)):
        t = n / SAMPLE_RATE
        decay = math.exp(-28 * t)
        value = (
            0.28 * math.sin(2 * math.pi * 1400 * t)
            + 0.12 * math.sin(2 * math.pi * 900 * t)
        ) * decay
        samples.append(value)
    return samples


def soft_impact(duration: float = 0.50) -> list[float]:
    rng = random.Random(7)
    samples = []

    for n in range(int(SAMPLE_RATE * duration)):
        t = n / SAMPLE_RATE
        decay = math.exp(-7 * t)
        low = 0.26 * math.sin(2 * math.pi * (92 - 25 * t) * t) * decay
        body = 0.12 * math.sin(2 * math.pi * 150 * t) * math.exp(-10 * t)
        noise = 0.035 * (rng.random() * 2 - 1) * math.exp(-18 * t)
        gain = envelope(t, duration, attack=0.005, release=0.15)
        samples.append((low + body + noise) * gain)

    return samples


def soft_whoosh(duration: float = 0.55) -> list[float]:
    rng = random.Random(11)
    samples = []
    phase = 0.0

    for n in range(int(SAMPLE_RATE * duration)):
        t = n / SAMPLE_RATE
        x = t / duration
        frequency = 260 + 1300 * (x ** 1.7)
        phase += 2 * math.pi * frequency / SAMPLE_RATE
        gain = math.sin(math.pi * x) ** 1.7
        noise = (rng.random() * 2 - 1) * 0.08
        samples.append((0.12 * math.sin(phase) + noise) * gain)

    return samples


def subtle_alert(duration: float = 0.34) -> list[float]:
    samples = []

    for n in range(int(SAMPLE_RATE * duration)):
        t = n / SAMPLE_RATE
        gain = envelope(t, duration, attack=0.02, release=0.12) * math.exp(-1.8 * t)
        value = (
            0.11 * math.sin(2 * math.pi * 660 * t)
            + 0.08 * math.sin(2 * math.pi * 880 * t)
        ) * gain
        samples.append(value)

    return samples


def outro_signature(duration: float = 1.85) -> list[float]:
    notes = [220.0, 277.18, 329.63, 440.0]
    starts = [0.00, 0.22, 0.44, 0.78]
    rng = random.Random(19)
    samples = []

    for n in range(int(SAMPLE_RATE * duration)):
        t = n / SAMPLE_RATE
        value = 0.0

        for frequency, start in zip(notes, starts):
            if t < start:
                continue
            dt = t - start
            gain = min(1.0, dt / 0.035) * math.exp(-2.2 * dt)
            value += 0.075 * math.sin(2 * math.pi * frequency * dt) * gain
            value += 0.025 * math.sin(2 * math.pi * frequency * 2 * dt) * gain

        if t > 0.45:
            x = min(1.0, (t - 0.45) / max(0.01, duration - 0.45))
            value += 0.015 * (rng.random() * 2 - 1) * (math.sin(math.pi * x) ** 2)

        value *= envelope(t, duration, attack=0.01, release=0.35)
        samples.append(value)

    return samples


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    sounds = {
        "tick.wav": tick(),
        "soft-impact.wav": soft_impact(),
        "soft-whoosh.wav": soft_whoosh(),
        "subtle-alert.wav": subtle_alert(),
        "outro-signature.wav": outro_signature(),
    }

    for filename, samples in sounds.items():
        write_wav(output_dir / filename, samples)

    print(
        "Sound design gerado: "
        + ", ".join(sorted(sounds))
        + f" em {output_dir}"
    )


if __name__ == "__main__":
    main()
