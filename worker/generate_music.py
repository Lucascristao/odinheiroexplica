#!/usr/bin/env python3
"""Generate curated editorial background music (bed music) for O Dinheiro Explica.

Vectorized audio synthesis using numpy and standard wave/struct.
Adapts to project duration, category, and visual_direction world.
"""

import argparse
import json
import math
from pathlib import Path
import numpy as np


SAMPLE_RATE = 48000

PROFILES = {
    "finance": {
        "name": "Editorial Finance",
        "bpm": 108,
        "chords": [
            [146.83, 220.00, 261.63, 329.63, 349.23],  # Dm9
            [116.54, 174.61, 220.00, 293.66, 349.23],  # Bbmaj7
            [98.00,  146.83, 174.61, 233.08, 293.66],  # Gm7
            [130.81, 196.00, 261.63, 293.66, 329.63],  # C9sus4
        ],
        "bass": [73.42, 58.27, 49.00, 65.41],
    },
    "market": {
        "name": "Dynamic Market",
        "bpm": 114,
        "chords": [
            [110.00, 164.81, 196.00, 246.94, 261.63],  # Am7
            [87.31,  130.81, 174.61, 220.00, 261.63],  # Fmaj9
            [146.83, 220.00, 261.63, 349.23, 440.00],  # Dm7
            [98.00,  146.83, 196.00, 261.63, 293.66],  # Gsus4
        ],
        "bass": [55.00, 43.65, 73.42, 49.00],
    },
    "alert": {
        "name": "Tension Alert",
        "bpm": 104,
        "chords": [
            [82.41,  123.47, 164.81, 196.00, 246.94],  # Em
            [130.81, 164.81, 196.00, 246.94, 329.63],  # Cmaj7
            [110.00, 164.81, 220.00, 261.63, 329.63],  # Am9
            [123.47, 185.00, 220.00, 293.66, 370.00],  # Bm7
        ],
        "bass": [41.20, 65.41, 55.00, 61.74],
    },
    "personal_finance": {
        "name": "Clear Financial Plan",
        "bpm": 106,
        "chords": [
            [98.00,  146.83, 196.00, 246.94, 293.66],  # Gmaj7
            [82.41,  123.47, 164.81, 246.94, 293.66],  # Em9
            [130.81, 164.81, 196.00, 246.94, 329.63],  # Cmaj7
            [146.83, 220.00, 261.63, 293.66, 370.00],  # D9sus4
        ],
        "bass": [49.00, 41.20, 65.41, 73.42],
    },
}


def generate_bed_track_numpy(
    duration_seconds: float,
    world: str = "finance",
    seed_str: str = "ode-default",
) -> bytes:
    total_samples = int(SAMPLE_RATE * duration_seconds)
    profile = PROFILES.get(world) or PROFILES["finance"]

    # Seed rng
    h = 0x811C9DC5
    for ch in seed_str:
        h = (h ^ ord(ch)) * 0x01000193 & 0xFFFFFFFF
    rng = np.random.default_rng(h)

    t = np.linspace(0, duration_seconds, total_samples, endpoint=False, dtype=np.float32)

    sec_per_beat = 60.0 / profile["bpm"]
    sec_per_bar = sec_per_beat * 4.0
    num_chords = len(profile["chords"])

    bar_idx_arr = (t / sec_per_bar).astype(np.int32) % num_chords
    bar_progress = (t % sec_per_bar) / sec_per_bar
    bar_fade = np.sin(np.pi * bar_progress).astype(np.float32)

    left = np.zeros(total_samples, dtype=np.float32)
    right = np.zeros(total_samples, dtype=np.float32)

    # 1. Pads synthesis per chord segment
    for b_idx in range(num_chords):
        mask = (bar_idx_arr == b_idx)
        if not np.any(mask):
            continue
        t_sub = t[mask]
        fade_sub = bar_fade[mask]
        chord = profile["chords"][b_idx]

        pad_l_sub = np.zeros(len(t_sub), dtype=np.float32)
        pad_r_sub = np.zeros(len(t_sub), dtype=np.float32)

        for freq in chord:
            fl = freq - 0.35
            fr = freq + 0.35
            phase_l = 2.0 * np.pi * fl * t_sub
            phase_r = 2.0 * np.pi * fr * t_sub
            pad_l_sub += np.sin(phase_l) * 0.7 + np.sin(phase_l * 2.0) * 0.15
            pad_r_sub += np.sin(phase_r) * 0.7 + np.sin(phase_r * 2.0) * 0.15

        pad_l_sub = (pad_l_sub / len(chord)) * (0.65 + 0.35 * fade_sub)
        pad_r_sub = (pad_r_sub / len(chord)) * (0.65 + 0.35 * fade_sub)

        # Bass per chord
        bass_freq = profile["bass"][b_idx]
        beat_in_bar = (t_sub % sec_per_bar) / sec_per_beat
        beat_frac = beat_in_bar % 1.0
        bass_env = np.exp(-3.5 * beat_frac).astype(np.float32)
        phase_bass = 2.0 * np.pi * bass_freq * t_sub
        bass_val = (np.sin(phase_bass) + 0.25 * np.sin(phase_bass * 2.0)) * bass_env * 0.55

        # Pluck
        chord_arr = np.array(chord, dtype=np.float32)
        sixteenth = (beat_in_bar * 4.0).astype(np.int32) % 16
        note_freq = chord_arr[sixteenth % len(chord)] * 2.0
        sixteenth_frac = (beat_in_bar * 4.0) % 1.0
        pluck_env = np.exp(-22.0 * sixteenth_frac).astype(np.float32)
        pluck_val = np.sin(2.0 * np.pi * note_freq * t_sub) * pluck_env * 0.18

        is_even = (sixteenth % 2 == 0)
        pluck_l = np.where(is_even, pluck_val * 1.0, pluck_val * 0.25)
        pluck_r = np.where(is_even, pluck_val * 0.25, pluck_val * 1.0)

        left[mask] += (pad_l_sub * 0.38 + bass_val * 0.32 + pluck_l)
        right[mask] += (pad_r_sub * 0.38 + bass_val * 0.32 + pluck_r)

    # 4. Organic studio air floor (lowpassed gentle noise at -52 dBFS)
    raw_noise = rng.uniform(-1.0, 1.0, total_samples).astype(np.float32)
    # Simple moving average filter for soft air texture
    air_noise = np.convolve(raw_noise, np.ones(32, dtype=np.float32) / 32.0, mode='same') * 0.003

    left += air_noise
    right += air_noise

    # Master fades
    fade_in = np.clip(t / 2.0, 0.0, 1.0)
    fade_out = np.clip((duration_seconds - t) / 3.5, 0.0, 1.0)
    master_gain = fade_in * fade_out * 0.32

    left *= master_gain
    right *= master_gain

    # Quantize to 16-bit PCM Stereo
    left = np.clip(left, -1.0, 1.0)
    right = np.clip(right, -1.0, 1.0)

    left_int16 = (np.where(left < 0, left * 32768.0, left * 32767.0)).astype(np.int16)
    right_int16 = (np.where(right < 0, right * 32768.0, right * 32767.0)).astype(np.int16)

    stereo_interleaved = np.empty((total_samples, 2), dtype=np.int16)
    stereo_interleaved[:, 0] = left_int16
    stereo_interleaved[:, 1] = right_int16

    return stereo_interleaved.tobytes()


def write_stereo_wav(path: Path, pcm_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> None:
    import wave
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm_bytes)


def main():
    parser = argparse.ArgumentParser(description="Generate editorial background music track")
    parser.add_argument("--project", help="Path to project.json")
    parser.add_argument("--render-input", help="Path to render-input.json")
    parser.add_argument("--output-dir", default="public/generated-music", help="Output directory")
    parser.add_argument("--duration", type=float, help="Explicit duration in seconds")
    parser.add_argument("--world", default=None, help="Explicit world/category")
    parser.add_argument("--seed", default=None, help="Explicit seed string")
    args = parser.parse_args()

    project_data = {}
    if args.project and Path(args.project).is_file():
        project_data = json.loads(Path(args.project).read_text(encoding="utf-8"))

    render_data = {}
    if args.render_input and Path(args.render_input).is_file():
        render_data = json.loads(Path(args.render_input).read_text(encoding="utf-8"))

    duration = args.duration
    if duration is None:
        if "duration_in_frames" in render_data and "fps" in render_data:
            duration = render_data["duration_in_frames"] / render_data["fps"]
        elif "scenes" in render_data:
            duration = sum(s.get("audio_duration_seconds", 30.0) for s in render_data["scenes"])
        else:
            duration = 180.0

    world = args.world
    if not world:
        visual_dir = project_data.get("visual_direction") or render_data.get("visual_direction") or {}
        world = visual_dir.get("world") or project_data.get("story", {}).get("category", "finance")

    seed_str = args.seed or project_data.get("project_id") or render_data.get("project_id") or "ode-music"

    out_dir = Path(args.output_dir)
    out_file = out_dir / "daily-bed.wav"

    print(f"[Music Engine] Sintetizando trilha temática:")
    print(f"  Mundo/Clima: {world}")
    print(f"  Duração: {duration:.2f}s")
    print(f"  Arquivo: {out_file}")

    pcm = generate_bed_track_numpy(duration_seconds=duration, world=world, seed_str=seed_str)
    write_stereo_wav(out_file, pcm)

    manifest_file = out_dir / "daily-music-manifest.json"
    manifest_file.write_text(
        json.dumps({
            "file": "generated-music/daily-bed.wav",
            "duration_seconds": duration,
            "sample_rate": SAMPLE_RATE,
            "channels": 2,
            "world": world,
            "profile": PROFILES.get(world, PROFILES["finance"])["name"],
            "seed": seed_str,
        }, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    print(f"[Music Engine] Concluído com sucesso: {out_file} ({len(pcm)/1024/1024:.2f} MB)")


if __name__ == "__main__":
    main()
