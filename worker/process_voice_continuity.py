"""Master existing scene audio without changing the TTS cache or calling a provider.

Spectral matching is a bounded correction of a descriptive speech profile. It
does not reproduce identity, pitch, emotion, pacing, or a model's pronunciation.
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


VERSION = "adaptive-voice-continuity-v1"
PRIMARY_MODEL = "gemini-3.8-flash-tts"
SECONDARY_MODEL = "gemini-3.8-flash-lite-tts"
FALLBACK_MODEL = "gemini-3.1-flash-tts-preview"
FALLBACK_MODELS = {SECONDARY_MODEL, FALLBACK_MODEL}
SAMPLE_RATE = 48000
LOUDNESS_TOLERANCE = 0.5
TRUE_PEAK_CEILING = -1.0
BANDS = [(80, 300), (300, 900), (900, 2500), (2500, 6000), (6000, 10000)]
COMPRESSOR = "acompressor=threshold=0.125:ratio=1.18:attack=15:release=180:knee=2.5:makeup=1"


def run(ffmpeg, arguments):
    result = subprocess.run([ffmpeg, "-hide_banner", "-nostats", *arguments], capture_output=True)
    if result.returncode:
        raise RuntimeError("ffmpeg failed: " + result.stderr.decode("utf-8", errors="replace")[-3000:])
    return result


def decode(ffmpeg, path):
    raw = run(ffmpeg, ["-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le", "-"]).stdout
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


def measure(ffmpeg, path, target):
    result = run(ffmpeg, ["-i", str(path), "-af", f"loudnorm=I={target}:TP={TRUE_PEAK_CEILING}:LRA=11:print_format=json", "-f", "null", "-"])
    matches = re.findall(r'\{\s*"input_i".*?\}', result.stderr.decode("utf-8", errors="replace"), flags=re.S)
    if not matches:
        raise RuntimeError(f"Loudness analysis did not return measurements: {path}")
    data = json.loads(matches[-1])
    if not all(math.isfinite(float(data[k])) for k in ["input_i", "input_tp", "input_lra", "input_thresh", "target_offset"]):
        raise RuntimeError(f"Cannot normalize silent or invalid audio: {path}")
    return data


def speech_profile(samples):
    size, hop = 4096, 2048
    if len(samples) < size:
        return None, {"reason": "too-short"}
    frames = np.lib.stride_tricks.sliding_window_view(samples, size)[::hop]
    rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
    rms_db = 20 * np.log10(np.maximum(rms, 1e-12))
    # Energy activity gate, explicitly not a speech recognizer/phonetic VAD.
    gate_db = max(-45.0, float(np.percentile(rms_db, 75)) - 25.0)
    selected = frames[rms_db >= gate_db]
    active_seconds = len(selected) * hop / SAMPLE_RATE
    details = {"activity_gate_dbfs": round(gate_db, 3), "active_frames": len(selected), "active_seconds": round(active_seconds, 3)}
    if active_seconds < 5.0 or len(selected) < 60:
        return None, {**details, "reason": "insufficient-active-audio"}
    power = np.abs(np.fft.rfft(selected * np.hanning(size), axis=1)) ** 2
    frequencies = np.fft.rfftfreq(size, 1 / SAMPLE_RATE)
    bands = np.stack([power[:, (frequencies >= lo) & (frequencies < hi)].sum(axis=1) for lo, hi in BANDS], axis=1)
    # Normalize every active frame before taking medians, so loud scenes and
    # unusually loud words cannot dominate the episode's spectral reference.
    normalized = bands / np.maximum(bands.sum(axis=1, keepdims=True), 1e-20)
    profile = np.median(10 * np.log10(np.maximum(normalized, 1e-12)), axis=0)
    return profile, {**details, "reason": "accepted", "profile_db": [round(float(x), 4) for x in profile]}


def eq_filter(gains):
    return ",".join([
        f"lowshelf=f=200:g={gains[0]:.4f}",
        f"equalizer=f=550:t=q:w=0.65:g={gains[1]:.4f}",
        f"equalizer=f=1500:t=q:w=0.65:g={gains[2]:.4f}",
        f"equalizer=f=4000:t=q:w=0.65:g={gains[3]:.4f}",
        f"highshelf=f=7000:g={gains[4]:.4f}",
    ])


def safe_source(directory, filename):
    resolved = (directory / filename).resolve()
    if not resolved.is_relative_to(directory.resolve()) or not resolved.is_file():
        raise RuntimeError(f"Missing scene audio or unsafe filename: {filename}")
    return resolved


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
        measurement = measure(ffmpeg, source_path, -19)
        inspections[scene_id] = {"path": source_path, "samples": samples, "profile": profile, "profile_details": details, "measurement": measurement}
        if profile is None:
            profile_rejections.append({"scene_id": scene_id, **details})
        if scene.get("model") == PRIMARY_MODEL:
            primary_loudness.append(float(measurement["input_i"]))
            if profile is not None:
                accepted_primary_profiles.append((scene_id, profile, details["active_seconds"]))
    reference_scene_ids = [item[0] for item in accepted_primary_profiles]
    reference_enough = len(accepted_primary_profiles) >= 2 and sum(item[2] for item in accepted_primary_profiles) >= 12
    reference_profile = np.median(np.stack([item[1] for item in accepted_primary_profiles]), axis=0) if reference_enough else None
    reference_reason = "episode-primary-profile" if reference_enough else "insufficient-primary-reference-two-scenes-twelve-active-seconds-required"
    target = round(float(np.clip(np.median(primary_loudness), -21, -17)), 2) if primary_loudness else -19.0
    result = copy.deepcopy(source_manifest)
    processed_scenes = []
    for scene in scenes:
        scene_id = scene["id"]
        info = inspections[scene_id]
        gains = np.zeros(len(BANDS))
        reason = "primary-no-spectral-correction"
        if scene.get("model") in FALLBACK_MODELS:
            if reference_profile is None:
                reason = reference_reason
            elif info["profile"] is None:
                reason = "fallback-profile-insufficient"
            else:
                residual = reference_profile - info["profile"]
                residual -= np.median(residual)
                # Charon 3.1 may already carry the fixed pre-EQ. This pass is
                # intentionally residual and also handles 3.8 Flash-Lite.
                gains = np.clip(residual * 0.6, -3, 3)
                reason = f"residual-match-{scene.get('model')}-to-current-episode-primary"
        elif scene.get("model") != PRIMARY_MODEL:
            reason = "unknown-model-no-spectral-correction"
        output_path = output_dir / f"{scene_id}.wav"
        intermediate = output_dir / f".{scene_id}.premaster.wav"
        replacement = output_dir / f".{scene_id}.gain.wav"
        filters = ([eq_filter(gains)] if np.any(np.abs(gains) > .0001) else []) + [COMPRESSOR]
        normalization_type = None
        remediation = []
        try:
            run(ffmpeg, ["-y", "-i", str(info["path"]), "-af", ",".join(filters), "-ar", str(SAMPLE_RATE), "-ac", "1", "-c:a", "pcm_f32le", str(intermediate)])
            measured = measure(ffmpeg, intermediate, target)
            norm = (
                f"loudnorm=I={target}:TP={TRUE_PEAK_CEILING}:LRA=11:"
                f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
                f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
                f"offset={measured['target_offset']}:linear=true:print_format=json"
            )
            # loudnorm may internally run at 192 kHz. Resample back to the
            # delivery clock before using sample-based padding/trimming.
            exact_length = (
                f"aresample={SAMPLE_RATE},apad=whole_len={len(info['samples'])},"
                f"atrim=end_sample={len(info['samples'])}"
            )
            normalized = run(
                ffmpeg,
                [
                    "-y", "-i", str(intermediate), "-af", f"{norm},{exact_length}",
                    "-ar", str(SAMPLE_RATE), "-ac", "1", "-c:a", "pcm_s24le", str(output_path),
                ],
            )
            normalization_data = re.findall(r'\{\s*"input_i".*?\}', normalized.stderr.decode("utf-8", errors="replace"), flags=re.S)
            if normalization_data:
                normalization_type = json.loads(normalization_data[-1]).get("normalization_type")
            final_measurement = measure(ffmpeg, output_path, target)
            for attempt in range(2):
                error = target - float(final_measurement["input_i"])
                peak = float(final_measurement["input_tp"])
                if abs(error) <= LOUDNESS_TOLERANCE and peak <= TRUE_PEAK_CEILING:
                    break
                gain = float(np.clip(error, -3, 3))
                # Oversampled limiter with 0.2dB guard for downsampling peaks.
                limit = 10 ** (-1.2 / 20)
                filter_chain = (
                    f"volume={gain:.4f}dB,aresample=192000,"
                    f"alimiter=limit={limit:.8f}:attack=5:release=60:level=false:latency=true,"
                    f"aresample={SAMPLE_RATE},apad=whole_len={len(info['samples'])},"
                    f"atrim=end_sample={len(info['samples'])}"
                )
                run(ffmpeg, ["-y", "-i", str(output_path), "-af", filter_chain, "-ar", str(SAMPLE_RATE), "-ac", "1", "-c:a", "pcm_s24le", str(replacement)])
                replacement.replace(output_path)
                final_measurement = measure(ffmpeg, output_path, target)
                remediation.append({"attempt": attempt + 1, "gain_db": round(gain, 4), "output_lufs": float(final_measurement["input_i"]), "true_peak_dbtp": float(final_measurement["input_tp"])})
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
                raise RuntimeError(f"Processing changed scene sample clock/length for {scene_id}: {len(info['samples'])} -> {output_frames}")
            peak = float(final_measurement["input_tp"])
            if peak > TRUE_PEAK_CEILING:
                raise RuntimeError(f"True peak exceeds ceiling after processing {scene_id}: {peak}dBTP")
            loudness_error = abs(float(final_measurement["input_i"]) - target)
            ceiling_prevents_equalization = loudness_error > LOUDNESS_TOLERANCE
            if ceiling_prevents_equalization:
                raise RuntimeError(f"Cannot reach loudness tolerance without further processing for {scene_id}: target {target}, measured {final_measurement['input_i']}, peak {peak}; no success manifest written")
            processed_scene = copy.deepcopy(scene)
            processed_scene["file"] = output_path.name
            processed_scene["duration_seconds"] = round(duration, 6)
            duration_ratio = duration / float(scene["duration_seconds"])
            for timing in processed_scene.get("beat_timings", []):
                if isinstance(timing.get("audio_offset_seconds"), (int, float)):
                    timing["audio_offset_seconds"] = round(min(duration, max(0, timing["audio_offset_seconds"] * duration_ratio)), 6)
            processed_scene["postprocess"] = {
                "version": VERSION, "reference_scene_ids": reference_scene_ids if reference_enough else [],
                "eq_gains_db": [round(float(value), 4) for value in gains], "eq_band_ranges_hz": BANDS,
                "reason": reason, "input_profile": info["profile_details"], "original_voice_treatment": scene.get("voice_treatment", "none"),
                "input_lufs": float(info["measurement"]["input_i"]), "input_true_peak_dbtp": float(info["measurement"]["input_tp"]),
                "output_lufs": float(final_measurement["input_i"]), "output_true_peak_dbtp": peak,
                "output_loudness_range_lu": float(final_measurement["input_lra"]), "target_lufs": target,
                "loudness_error_lu": round(loudness_error, 4), "normalization_type": normalization_type,
                "compressor": {"ratio": 1.18, "threshold_dbfs": round(20 * math.log10(.125), 3), "attack_ms": 15, "release_ms": 180},
                "remediation": remediation, "ceiling_prevented_equalization": ceiling_prevents_equalization,
                "source_file": scene["file"], "source_sha256": hashlib.sha256(info["path"].read_bytes()).hexdigest(),
                "source_manifest_duration_seconds": scene["duration_seconds"], "source_decoded_samples": len(info["samples"]),
                "beat_offset_duration_ratio": round(duration_ratio, 9),
                "output_samples": output_frames, "sample_rate": SAMPLE_RATE, "channels": 1,
                "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
            }
            processed_scenes.append(processed_scene)
            print(f"{scene_id}: {info['measurement']['input_i']} -> {final_measurement['input_i']} LUFS; peak {peak} dBTP; {reason}", flush=True)
        finally:
            intermediate.unlink(missing_ok=True)
            replacement.unlink(missing_ok=True)
    result["scenes"] = processed_scenes
    result["output_format"] = "audio-48khz-24bit-mono-wav"
    result["total_duration_seconds"] = round(sum(s["duration_seconds"] for s in processed_scenes), 6)
    result["postprocess"] = {
        "version": VERSION, "source_manifest_sha256": hashlib.sha256(input_manifest_path.read_bytes()).hexdigest(),
        "source_audio_preserved": True, "reference_model": PRIMARY_MODEL, "reference_scene_ids": reference_scene_ids if reference_enough else [],
        "reference_profile_db": [round(float(x), 4) for x in reference_profile] if reference_profile is not None else None,
        "reference_reason": reference_reason, "profile_rejections": profile_rejections,
        "profile_method": "energy-active-frames-normalized-broadband-power-median-frames-then-median-primary-scenes",
        "spectral_max_gain_db": 3, "spectral_residual_shrinkage": .6,
        "target_lufs": target, "target_source": "clamped-primary-scene-median" if primary_loudness else "no-primary-default-minus19",
        "true_peak_ceiling_dbtp": TRUE_PEAK_CEILING, "loudness_tolerance_lu": LOUDNESS_TOLERANCE,
        "fallback_models_matched": sorted(FALLBACK_MODELS),
        "limitations": ["Energy activity is not phonetic VAD.", "Different texts confound spectral identity comparisons.", "EQ and compression do not normalize timbre identity, prosody or speaking pace.", "No pitch, speed or speech crossfade is applied."],
    }
    temporary_manifest = output_manifest_path.with_suffix(output_manifest_path.suffix + ".tmp")
    temporary_manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_manifest.replace(output_manifest_path)
    print(f"Processed {len(processed_scenes)} scenes; common target {target} LUFS; manifest: {output_manifest_path}", flush=True)


if __name__ == "__main__":
    main()
