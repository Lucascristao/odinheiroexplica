"""Stabilize voice continuity without changing the TTS cache or calling a provider.

Fallback timbre is matched to primary scenes with slow, overlapping spectral
windows. Loudness uses static gain plus a safety limiter, avoiding dynamic
loudness normalization/compression that can make timbre seem to pump.
"""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess

import numpy as np


VERSION = "adaptive-voice-continuity-v2"
PRIMARY_MODEL = "gemini-3.8-flash-tts"
SECONDARY_MODEL = "gemini-3.8-flash-lite-tts"
FALLBACK_MODEL = "gemini-3.1-flash-tts-preview"
FALLBACK_MODELS = {SECONDARY_MODEL, FALLBACK_MODEL}
SAMPLE_RATE = 48000
TRUE_PEAK_CEILING = -1.0
LOUDNESS_TOLERANCE = 0.8
MAX_STATIC_GAIN_DB = 4.0
MAX_LIMITER_REDUCTION_DB = 1.5
BANDS = [(80, 300), (300, 900), (900, 2500), (2500, 6000), (6000, 10000)]
MATCH_WINDOW_SECONDS = 5.0
MATCH_HOP_SECONDS = 2.5
SPECTRAL_MAX_GAIN_DB = 2.5
SPECTRAL_SHRINKAGE = 0.50
SPECTRAL_MAX_SLEW_DB = 0.65
STFT_SIZE = 4096
STFT_HOP = 2048


def run(ffmpeg, arguments):
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostats", *arguments],
        capture_output=True,
    )
    if result.returncode:
        raise RuntimeError(
            "ffmpeg failed: " + result.stderr.decode("utf-8", errors="replace")[-3000:]
        )
    return result


def decode(ffmpeg, path):
    raw = run(
        ffmpeg,
        [
            "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SAMPLE_RATE),
            "-f", "f32le", "-",
        ],
    ).stdout
    samples = np.frombuffer(raw, dtype="<f4").copy()
    if len(samples) < SAMPLE_RATE or not np.isfinite(samples).all():
        raise RuntimeError(f"Invalid or too short scene audio: {path}")
    return samples


def probe_audio_format(ffprobe, path):
    result = subprocess.run(
        [
            ffprobe, "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,sample_rate,channels",
            "-of", "json", str(path),
        ],
        capture_output=True,
    )
    if result.returncode:
        raise RuntimeError(
            "ffprobe failed: " + result.stderr.decode("utf-8", errors="replace")[-2000:]
        )
    try:
        streams = json.loads(result.stdout.decode("utf-8")).get("streams") or []
        stream = streams[0]
        return {
            "codec_name": str(stream["codec_name"]),
            "sample_rate": int(stream["sample_rate"]),
            "channels": int(stream["channels"]),
        }
    except (ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError):
        raise RuntimeError(f"Invalid ffprobe audio metadata: {path}") from None


def measure(ffmpeg, path, target=-19.0):
    # loudnorm is used only as a meter. It is never used to process the signal.
    result = run(
        ffmpeg,
        [
            "-i", str(path),
            "-af", f"loudnorm=I={target}:TP={TRUE_PEAK_CEILING}:LRA=11:print_format=json",
            "-f", "null", "-",
        ],
    )
    matches = re.findall(
        r'\{\s*"input_i".*?\}',
        result.stderr.decode("utf-8", errors="replace"),
        flags=re.S,
    )
    if not matches:
        raise RuntimeError(f"Loudness analysis did not return measurements: {path}")
    data = json.loads(matches[-1])
    keys = ["input_i", "input_tp", "input_lra", "input_thresh", "target_offset"]
    if not all(math.isfinite(float(data[key])) for key in keys):
        raise RuntimeError(f"Cannot measure silent or invalid audio: {path}")
    return data


def _profile_from_frames(frames, *, minimum_active_seconds):
    if len(frames) == 0:
        return None, {"reason": "too-short"}
    rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
    rms_db = 20 * np.log10(np.maximum(rms, 1e-12))
    gate_db = max(-45.0, float(np.percentile(rms_db, 75)) - 25.0)
    selected = frames[rms_db >= gate_db]
    active_seconds = len(selected) * STFT_HOP / SAMPLE_RATE
    details = {
        "activity_gate_dbfs": round(gate_db, 3),
        "active_frames": int(len(selected)),
        "active_seconds": round(active_seconds, 3),
    }
    if active_seconds < minimum_active_seconds or len(selected) < 16:
        return None, {**details, "reason": "insufficient-active-audio"}

    window = np.hanning(STFT_SIZE)
    power = np.abs(np.fft.rfft(selected * window, axis=1)) ** 2
    frequencies = np.fft.rfftfreq(STFT_SIZE, 1 / SAMPLE_RATE)
    bands = np.stack([
        power[:, (frequencies >= lo) & (frequencies < hi)].sum(axis=1)
        for lo, hi in BANDS
    ], axis=1)
    normalized = bands / np.maximum(bands.sum(axis=1, keepdims=True), 1e-20)
    profile = np.median(
        10 * np.log10(np.maximum(normalized, 1e-12)),
        axis=0,
    )
    return profile, {
        **details,
        "reason": "accepted",
        "profile_db": [round(float(value), 4) for value in profile],
    }


def speech_profile(samples, *, minimum_active_seconds=5.0):
    if len(samples) < STFT_SIZE:
        return None, {"reason": "too-short"}
    frames = np.lib.stride_tricks.sliding_window_view(samples, STFT_SIZE)[::STFT_HOP]
    return _profile_from_frames(frames, minimum_active_seconds=minimum_active_seconds)


def local_profile(samples):
    return speech_profile(samples, minimum_active_seconds=1.25)


def _raw_residual_gain(reference_profile, profile):
    residual = reference_profile - profile
    residual -= np.median(residual)
    return np.clip(
        residual * SPECTRAL_SHRINKAGE,
        -SPECTRAL_MAX_GAIN_DB,
        SPECTRAL_MAX_GAIN_DB,
    )


def build_adaptive_gain_windows(samples, reference_profile):
    """Build slow 5-second spectral corrections with 2.5-second overlap."""
    duration = len(samples) / SAMPLE_RATE
    centers = np.arange(0.0, duration + MATCH_HOP_SECONDS, MATCH_HOP_SECONDS)
    centers = np.clip(centers, 0.0, duration)
    centers = np.unique(centers)
    raw_gains = []
    diagnostics = []

    half = MATCH_WINDOW_SECONDS / 2
    for center in centers:
        start = max(0.0, center - half)
        end = min(duration, center + half)
        if end - start < MATCH_WINDOW_SECONDS and duration > MATCH_WINDOW_SECONDS:
            if start <= 0:
                end = min(duration, MATCH_WINDOW_SECONDS)
            elif end >= duration:
                start = max(0.0, duration - MATCH_WINDOW_SECONDS)
        segment = samples[
            int(round(start * SAMPLE_RATE)):int(round(end * SAMPLE_RATE))
        ]
        profile, details = local_profile(segment)
        if profile is None:
            gains = None
        else:
            gains = _raw_residual_gain(reference_profile, profile)
        raw_gains.append(gains)
        diagnostics.append({
            "center_seconds": round(float(center), 3),
            "analysis_start_seconds": round(float(start), 3),
            "analysis_end_seconds": round(float(end), 3),
            "profile": details,
        })

    # Fill weak/silent windows by interpolation from nearby valid speech windows.
    valid = [idx for idx, value in enumerate(raw_gains) if value is not None]
    if not valid:
        return centers, np.zeros((len(centers), len(BANDS))), diagnostics

    filled = np.zeros((len(centers), len(BANDS)), dtype=np.float64)
    for band in range(len(BANDS)):
        filled[:, band] = np.interp(
            np.arange(len(centers)),
            valid,
            [raw_gains[idx][band] for idx in valid],
        )

    # Three-point temporal smoothing, then a hard slew limit between analysis
    # windows. This prevents the audible "effect on/effect off" sensation.
    smoothed = filled.copy()
    if len(filled) > 2:
        smoothed[1:-1] = (
            0.25 * filled[:-2] + 0.50 * filled[1:-1] + 0.25 * filled[2:]
        )
    stable = smoothed.copy()
    for idx in range(1, len(stable)):
        delta = np.clip(
            stable[idx] - stable[idx - 1],
            -SPECTRAL_MAX_SLEW_DB,
            SPECTRAL_MAX_SLEW_DB,
        )
        stable[idx] = stable[idx - 1] + delta
    stable = np.clip(stable, -SPECTRAL_MAX_GAIN_DB, SPECTRAL_MAX_GAIN_DB)

    for idx, details in enumerate(diagnostics):
        details["eq_gains_db"] = [
            round(float(value), 4) for value in stable[idx]
        ]
    return centers, stable, diagnostics


def apply_slow_spectral_match(samples, centers, gains):
    """Apply interpolated broad-band gains with overlap-add STFT."""
    if not len(samples) or not np.any(np.abs(gains) > 1e-6):
        return samples.copy()

    pad = STFT_SIZE // 2
    padded = np.pad(samples.astype(np.float64), (pad, pad), mode="reflect")
    analysis_window = np.hanning(STFT_SIZE).astype(np.float64)
    frequencies = np.fft.rfftfreq(STFT_SIZE, 1 / SAMPLE_RATE)
    band_centers = np.array([
        math.sqrt(lo * hi) for lo, hi in BANDS
    ], dtype=np.float64)
    control_freqs = np.concatenate(([0.0], band_centers, [SAMPLE_RATE / 2]))
    output = np.zeros_like(padded, dtype=np.float64)
    weight = np.zeros_like(padded, dtype=np.float64)

    last_start = len(padded) - STFT_SIZE
    starts = list(range(0, max(1, last_start + 1), STFT_HOP))
    if starts[-1] != last_start:
        starts.append(last_start)

    for start in starts:
        frame = padded[start:start + STFT_SIZE]
        center_seconds = (start + STFT_SIZE / 2 - pad) / SAMPLE_RATE
        center_seconds = float(np.clip(center_seconds, 0.0, len(samples) / SAMPLE_RATE))
        temporal = np.array([
            np.interp(center_seconds, centers, gains[:, band])
            for band in range(len(BANDS))
        ])
        control_gains = np.concatenate(([0.0], temporal, [0.0]))
        frequency_gain_db = np.interp(frequencies, control_freqs, control_gains)
        spectrum = np.fft.rfft(frame * analysis_window)
        spectrum *= np.power(10.0, frequency_gain_db / 20.0)
        reconstructed = np.fft.irfft(spectrum, n=STFT_SIZE)
        output[start:start + STFT_SIZE] += reconstructed * analysis_window
        weight[start:start + STFT_SIZE] += analysis_window ** 2

    valid = weight > 1e-10
    output[valid] /= weight[valid]
    matched = output[pad:pad + len(samples)]
    if len(matched) != len(samples) or not np.isfinite(matched).all():
        raise RuntimeError("Adaptive spectral matching produced invalid samples.")
    return matched.astype(np.float32)


def safe_source(directory, filename):
    resolved = (directory / filename).resolve()
    if not resolved.is_relative_to(directory.resolve()) or not resolved.is_file():
        raise RuntimeError(f"Missing scene audio or unsafe filename: {filename}")
    return resolved


def write_float_premaster(ffmpeg, raw_path, wav_path):
    run(
        ffmpeg,
        [
            "-y", "-f", "f32le", "-ar", str(SAMPLE_RATE), "-ac", "1",
            "-i", str(raw_path), "-c:a", "pcm_f32le", str(wav_path),
        ],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-manifest", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-manifest", required=True)
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    input_manifest_path = Path(args.input_manifest).resolve()
    output_manifest_path = Path(args.output_manifest).resolve()
    if output_dir == source_dir or output_dir.is_relative_to(source_dir) or source_dir.is_relative_to(output_dir):
        raise RuntimeError("Processed audio must use a separate directory from source/cache audio.")
    if output_manifest_path == input_manifest_path:
        raise RuntimeError("Processed manifest must not overwrite the source manifest.")

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("ffmpeg and ffprobe are required for voice continuity processing.")

    source_manifest = json.loads(input_manifest_path.read_text(encoding="utf-8"))
    scenes = source_manifest.get("scenes") or []
    if not scenes:
        raise RuntimeError("Source TTS manifest has no scenes.")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    inspections = {}
    accepted_primary_profiles = []
    primary_loudness = []
    profile_rejections = []

    for scene in scenes:
        scene_id = str(scene["id"])
        if scene_id in inspections or not re.fullmatch(r"[A-Za-z0-9_-]+", scene_id):
            raise RuntimeError(f"Duplicate or unsafe scene ID: {scene_id}")
        source_path = safe_source(source_dir, scene["file"])
        samples = decode(ffmpeg, source_path)
        profile, details = speech_profile(samples)
        measurement = measure(ffmpeg, source_path)
        inspections[scene_id] = {
            "path": source_path,
            "samples": samples,
            "profile": profile,
            "profile_details": details,
            "measurement": measurement,
        }
        if profile is None:
            profile_rejections.append({"scene_id": scene_id, **details})
        if scene.get("model") == PRIMARY_MODEL:
            primary_loudness.append(float(measurement["input_i"]))
            if profile is not None:
                accepted_primary_profiles.append(
                    (scene_id, profile, details["active_seconds"])
                )

    reference_scene_ids = [item[0] for item in accepted_primary_profiles]
    reference_enough = (
        len(accepted_primary_profiles) >= 2
        and sum(item[2] for item in accepted_primary_profiles) >= 12
    )
    reference_profile = (
        np.median(
            np.stack([item[1] for item in accepted_primary_profiles]),
            axis=0,
        )
        if reference_enough else None
    )
    reference_reason = (
        "episode-primary-profile"
        if reference_enough
        else "insufficient-primary-reference-two-scenes-twelve-active-seconds-required"
    )
    target = (
        round(float(np.clip(np.median(primary_loudness), -21, -17)), 2)
        if primary_loudness else -19.0
    )

    result = copy.deepcopy(source_manifest)
    processed_scenes = []

    for scene in scenes:
        scene_id = scene["id"]
        info = inspections[scene_id]
        model = scene.get("model")
        adaptive_windows = []
        reason = "primary-no-spectral-correction"
        processed_samples = info["samples"].copy()

        if model in FALLBACK_MODELS:
            if reference_profile is None:
                reason = reference_reason
            else:
                centers, gains, adaptive_windows = build_adaptive_gain_windows(
                    info["samples"],
                    reference_profile,
                )
                processed_samples = apply_slow_spectral_match(
                    info["samples"],
                    centers,
                    gains,
                )
                reason = f"slow-window-match-{model}-to-current-episode-primary"
        elif model != PRIMARY_MODEL:
            reason = "unknown-model-no-spectral-correction"

        output_path = output_dir / f"{scene_id}.wav"
        raw_path = output_dir / f".{scene_id}.premaster.f32"
        premaster = output_dir / f".{scene_id}.premaster.wav"
        replacement = output_dir / f".{scene_id}.gain.wav"
        try:
            raw_path.write_bytes(processed_samples.astype("<f4").tobytes())
            write_float_premaster(ffmpeg, raw_path, premaster)
            premaster_measurement = measure(ffmpeg, premaster, target)

            requested_gain = target - float(premaster_measurement["input_i"])
            static_gain = float(np.clip(
                requested_gain,
                -MAX_STATIC_GAIN_DB,
                MAX_STATIC_GAIN_DB,
            ))
            predicted_peak = float(premaster_measurement["input_tp"]) + static_gain
            max_gain_for_limiter = (
                TRUE_PEAK_CEILING
                + MAX_LIMITER_REDUCTION_DB
                - float(premaster_measurement["input_tp"])
            )
            if static_gain > max_gain_for_limiter:
                static_gain = max_gain_for_limiter

            limit = 10 ** (-1.2 / 20)
            exact_length = (
                f"aresample=192000,"
                f"volume={static_gain:.5f}dB,"
                f"alimiter=limit={limit:.8f}:attack=5:release=60:level=false:latency=true,"
                f"aresample={SAMPLE_RATE},"
                f"apad=whole_len={len(info['samples'])},"
                f"atrim=end_sample={len(info['samples'])}"
            )
            run(
                ffmpeg,
                [
                    "-y", "-i", str(premaster), "-af", exact_length,
                    "-ar", str(SAMPLE_RATE), "-ac", "1",
                    "-c:a", "pcm_s24le", str(output_path),
                ],
            )

            final_measurement = measure(ffmpeg, output_path, target)
            remediation = []
            # One static correction is allowed when there is enough peak room.
            error = target - float(final_measurement["input_i"])
            headroom = TRUE_PEAK_CEILING - float(final_measurement["input_tp"])
            if abs(error) > LOUDNESS_TOLERANCE and (
                error < 0 or headroom >= min(error, 1.0)
            ):
                correction = float(np.clip(error, -1.0, 1.0))
                correction_chain = (
                    f"aresample=192000,volume={correction:.5f}dB,"
                    f"alimiter=limit={limit:.8f}:attack=5:release=60:level=false:latency=true,"
                    f"aresample={SAMPLE_RATE},"
                    f"apad=whole_len={len(info['samples'])},"
                    f"atrim=end_sample={len(info['samples'])}"
                )
                run(
                    ffmpeg,
                    [
                        "-y", "-i", str(output_path), "-af", correction_chain,
                        "-ar", str(SAMPLE_RATE), "-ac", "1",
                        "-c:a", "pcm_s24le", str(replacement),
                    ],
                )
                replacement.replace(output_path)
                final_measurement = measure(ffmpeg, output_path, target)
                remediation.append({
                    "static_correction_db": round(correction, 4),
                    "output_lufs": float(final_measurement["input_i"]),
                    "true_peak_dbtp": float(final_measurement["input_tp"]),
                })

            output_samples = decode(ffmpeg, output_path)
            output_frames = len(output_samples)
            duration = output_frames / SAMPLE_RATE
            audio_format = probe_audio_format(ffprobe, output_path)
            if (
                audio_format["sample_rate"] != SAMPLE_RATE
                or audio_format["channels"] != 1
                or audio_format["codec_name"] != "pcm_s24le"
            ):
                raise RuntimeError(
                    f"Invalid processed sample format for {scene_id}: {audio_format}"
                )
            if abs(output_frames - len(info["samples"])) > 2:
                raise RuntimeError(
                    f"Processing changed scene sample clock/length for {scene_id}: "
                    f"{len(info['samples'])} -> {output_frames}"
                )
            peak = float(final_measurement["input_tp"])
            if peak > TRUE_PEAK_CEILING:
                raise RuntimeError(
                    f"True peak exceeds ceiling after processing {scene_id}: {peak}dBTP"
                )

            loudness_error = abs(float(final_measurement["input_i"]) - target)
            if loudness_error > 1.5:
                raise RuntimeError(
                    f"Static loudness match outside safe tolerance for {scene_id}: "
                    f"target {target}, measured {final_measurement['input_i']}"
                )

            processed_scene = copy.deepcopy(scene)
            processed_scene["file"] = output_path.name
            processed_scene["duration_seconds"] = round(duration, 6)
            duration_ratio = duration / float(scene["duration_seconds"])
            for timing in processed_scene.get("beat_timings", []):
                if isinstance(timing.get("audio_offset_seconds"), (int, float)):
                    timing["audio_offset_seconds"] = round(
                        min(
                            duration,
                            max(
                                0,
                                timing["audio_offset_seconds"] * duration_ratio,
                            ),
                        ),
                        6,
                    )

            effective_window_gains = [
                window.get("eq_gains_db")
                for window in adaptive_windows
                if window.get("eq_gains_db") is not None
            ]
            processed_scene["postprocess"] = {
                "version": VERSION,
                "reference_scene_ids": reference_scene_ids if reference_enough else [],
                "reason": reason,
                "adaptive_windows": adaptive_windows,
                "adaptive_window_seconds": MATCH_WINDOW_SECONDS,
                "adaptive_hop_seconds": MATCH_HOP_SECONDS,
                "eq_band_ranges_hz": BANDS,
                "spectral_max_gain_db": SPECTRAL_MAX_GAIN_DB,
                "spectral_max_slew_db": SPECTRAL_MAX_SLEW_DB,
                "mean_eq_gains_db": (
                    [
                        round(float(value), 4)
                        for value in np.mean(effective_window_gains, axis=0)
                    ]
                    if effective_window_gains else [0.0] * len(BANDS)
                ),
                "input_profile": info["profile_details"],
                "original_voice_treatment": scene.get("voice_treatment", "none"),
                "input_lufs": float(info["measurement"]["input_i"]),
                "input_true_peak_dbtp": float(info["measurement"]["input_tp"]),
                "premaster_lufs": float(premaster_measurement["input_i"]),
                "premaster_true_peak_dbtp": float(premaster_measurement["input_tp"]),
                "requested_static_gain_db": round(requested_gain, 4),
                "applied_static_gain_db": round(static_gain, 4),
                "predicted_peak_before_limiter_dbtp": round(predicted_peak, 4),
                "normalization_type": "static-gain-with-safety-limiter",
                "output_lufs": float(final_measurement["input_i"]),
                "output_true_peak_dbtp": peak,
                "output_loudness_range_lu": float(final_measurement["input_lra"]),
                "target_lufs": target,
                "loudness_error_lu": round(loudness_error, 4),
                "remediation": remediation,
                "source_file": scene["file"],
                "source_sha256": hashlib.sha256(info["path"].read_bytes()).hexdigest(),
                "source_manifest_duration_seconds": scene["duration_seconds"],
                "source_decoded_samples": len(info["samples"]),
                "beat_offset_duration_ratio": round(duration_ratio, 9),
                "output_samples": output_frames,
                "sample_rate": SAMPLE_RATE,
                "channels": 1,
                "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
            }
            processed_scenes.append(processed_scene)
            print(
                f"{scene_id}: {info['measurement']['input_i']} -> "
                f"{final_measurement['input_i']} LUFS; "
                f"static gain {static_gain:+.2f}dB; peak {peak}dBTP; {reason}",
                flush=True,
            )
        finally:
            raw_path.unlink(missing_ok=True)
            premaster.unlink(missing_ok=True)
            replacement.unlink(missing_ok=True)

    result["scenes"] = processed_scenes
    result["output_format"] = "audio-48khz-24bit-mono-wav"
    result["total_duration_seconds"] = round(
        sum(scene["duration_seconds"] for scene in processed_scenes),
        6,
    )
    result["postprocess"] = {
        "version": VERSION,
        "source_manifest_sha256": hashlib.sha256(
            input_manifest_path.read_bytes()
        ).hexdigest(),
        "source_audio_preserved": True,
        "reference_model": PRIMARY_MODEL,
        "reference_scene_ids": reference_scene_ids if reference_enough else [],
        "reference_profile_db": (
            [round(float(value), 4) for value in reference_profile]
            if reference_profile is not None else None
        ),
        "reference_reason": reference_reason,
        "profile_rejections": profile_rejections,
        "profile_method": (
            "energy-active-frames normalized broadband power; "
            "slow overlapping fallback windows"
        ),
        "spectral_window_seconds": MATCH_WINDOW_SECONDS,
        "spectral_hop_seconds": MATCH_HOP_SECONDS,
        "spectral_max_gain_db": SPECTRAL_MAX_GAIN_DB,
        "spectral_residual_shrinkage": SPECTRAL_SHRINKAGE,
        "spectral_max_slew_db": SPECTRAL_MAX_SLEW_DB,
        "target_lufs": target,
        "target_source": (
            "clamped-primary-scene-median"
            if primary_loudness else "no-primary-default-minus19"
        ),
        "normalization_type": "static-gain-with-safety-limiter",
        "true_peak_ceiling_dbtp": TRUE_PEAK_CEILING,
        "loudness_tolerance_lu": LOUDNESS_TOLERANCE,
        "fallback_models_matched": sorted(FALLBACK_MODELS),
        "limitations": [
            "Energy activity is not phonetic VAD.",
            "Different texts confound spectral identity comparisons.",
            "Slow spectral matching does not normalize prosody or speaking pace.",
            "No pitch, speed, compressor, dynamic loudness normalization or speech crossfade is applied.",
        ],
    }
    temporary_manifest = output_manifest_path.with_suffix(
        output_manifest_path.suffix + ".tmp"
    )
    temporary_manifest.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_manifest.replace(output_manifest_path)
    print(
        f"Processed {len(processed_scenes)} scenes; common target {target} LUFS; "
        f"manifest: {output_manifest_path}",
        flush=True,
    )


if __name__ == "__main__":
    main()
