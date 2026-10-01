"""Voice continuity v3.

Rules:
- Same model + same voice for the whole episode: copy source audio byte-for-byte.
- Mixed models: leave the reference-model scenes untouched and process only
  fallback scenes.
- Model boundaries are recorded in metadata only; no audible marker is inserted.
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
from tts_config import TTS_MODEL_CASCADE

VERSION = "adaptive-voice-continuity-v3"
PRIMARY_MODEL, SECONDARY_MODEL, FALLBACK_MODEL = TTS_MODEL_CASCADE
SAMPLE_RATE = 48000
TRUE_PEAK_CEILING = -1.2
LOUDNESS_TOLERANCE = 0.8
LOUDNESS_FAILURE_TOLERANCE = 1.5
BANDS = [(80, 300), (300, 900), (900, 2500), (2500, 6000), (6000, 10000)]
MATCH_WINDOW_SECONDS = 5.0
MATCH_HOP_SECONDS = 2.5
SPECTRAL_MAX_GAIN_DB = 2.5
SPECTRAL_SHRINKAGE = 0.50
SPECTRAL_MAX_SLEW_DB = 0.65
MAX_STATIC_GAIN_DB = 3.0
STFT_SIZE = 4096
STFT_HOP = 2048


REFERENCE_SCHEMA = "gemini-voice-reference-v1"
REFERENCE_PROFILE_METHOD = "normalized-broadband-power-median-energy-active-frames-v1"
DEFAULT_REFERENCE_PATH = Path(__file__).parent / "voice-references" / "roberto-charon-3.8.json"


def profile_sha256(profile):
    payload = {"method": REFERENCE_PROFILE_METHOD, "bands_hz": BANDS,
               "profile_db": [round(float(value), 6) for value in profile]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def load_reusable_reference(path, voice):
    """Load a provenance-bound primary profile; never substitute another voice."""
    path = Path(path)
    if not path.is_file():
        return None, {"reason": "reusable-primary-reference-missing"}
    raw = path.read_bytes()
    asset = json.loads(raw.decode("utf-8"))
    if asset.get("voice") != voice:
        return None, {"reason": "reusable-primary-reference-voice-mismatch"}
    if asset.get("schema_version") != REFERENCE_SCHEMA or asset.get("model") != PRIMARY_MODEL:
        raise RuntimeError("Reusable voice reference has an invalid schema/model.")
    profile = np.asarray(asset.get("profile_db"), dtype=np.float64)
    sources = asset.get("sources") or []
    bands = [list(band) for band in BANDS]
    if (profile.shape != (len(BANDS),) or not np.isfinite(profile).all()
            or asset.get("bands_hz") != bands or asset.get("profile_method") != REFERENCE_PROFILE_METHOD
            or asset.get("profile_sha256") != profile_sha256(profile)
            or not sources or asset.get("provenance_kind") not in {"user-selected-primary-voice-sample", "reviewed-primary-episode-samples"}):
        raise RuntimeError("Reusable voice reference profile/provenance/hash is invalid.")
    active_total = 0.0
    for source in sources:
        if (not isinstance(source.get("filename"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", str(source.get("sha256", "")))
                or not math.isfinite(float(source.get("active_seconds", 0)))
                or not math.isfinite(float(source.get("duration_seconds", 0)))
                or float(source.get("active_seconds", 0)) <= 0
                or float(source.get("active_seconds", 0)) > float(source.get("duration_seconds", 0)) + .1):
            raise RuntimeError("Reusable voice reference source metadata is invalid.")
        active_total += float(source["active_seconds"])
    if active_total < 5:
        raise RuntimeError("Reusable voice reference has insufficient active audio.")
    confidence = float(asset.get("correction_confidence", .75))
    if not math.isfinite(confidence) or not 0 < confidence <= 1:
        raise RuntimeError("Reusable voice reference confidence is invalid.")
    return profile, {
        "reason": "reusable-primary-reference", "reference_id": asset["reference_id"],
        "voice": voice, "model": PRIMARY_MODEL, "schema_version": REFERENCE_SCHEMA,
        "profile_sha256": asset["profile_sha256"], "asset_sha256": hashlib.sha256(raw).hexdigest(),
        "provenance_kind": asset["provenance_kind"], "sources": sources,
        "correction_confidence": confidence,
    }


def loudness_assessment(error):
    if error > LOUDNESS_FAILURE_TOLERANCE + 1e-9:
        raise RuntimeError(f"Static loudness match exceeds failure tolerance {LOUDNESS_FAILURE_TOLERANCE} LU: {error:.3f} LU")
    warning = error > LOUDNESS_TOLERANCE + 1e-9
    return {"loudness_warning": warning, "loudness_status": "outside-target-peak-protection-preserved" if warning else "within-target",
            "loudness_target_tolerance_lu": LOUDNESS_TOLERANCE,
            "loudness_failure_tolerance_lu": LOUDNESS_FAILURE_TOLERANCE}


def select_reference(primary_profiles, voice, reference_path, episode_sources=None):
    enough = len(primary_profiles) >= 2 and sum(item[2] for item in primary_profiles) >= 12
    if enough:
        profile = np.median(np.stack([item[1] for item in primary_profiles]), axis=0)
        digest = profile_sha256(profile)
        return profile, {
            "reason": "episode-primary-profile", "reference_id": f"episode-primary-{digest[:12]}",
            "schema_version": REFERENCE_SCHEMA, "voice": voice, "model": PRIMARY_MODEL,
            "profile_sha256": digest, "asset_sha256": None, "correction_confidence": 1.0,
            "provenance_kind": "current-episode-primary-scenes", "sources": episode_sources or [],
            "scene_ids": [item[0] for item in primary_profiles],
        }
    profile, metadata = load_reusable_reference(reference_path, voice)
    metadata["scene_ids"] = []
    if profile is None:
        metadata["reason"] = "insufficient-episode-primary;" + metadata["reason"]
        metadata["correction_confidence"] = 0.0
    return profile, metadata



def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def static_gain_with_peak_guard(requested_gain, input_true_peak):
    gain = float(np.clip(requested_gain, -MAX_STATIC_GAIN_DB, MAX_STATIC_GAIN_DB))
    gain = min(gain, TRUE_PEAK_CEILING - .02 - input_true_peak)
    return gain, input_true_peak + gain


def run(ffmpeg: str, args: list[str]):
    result = subprocess.run([ffmpeg, "-hide_banner", "-nostats", *args], capture_output=True)
    if result.returncode:
        raise RuntimeError(
            "ffmpeg failed: " + result.stderr.decode("utf-8", errors="replace")[-3000:]
        )
    return result


def duration_seconds(ffprobe: str, path: Path) -> float:
    result = subprocess.run(
        [
            ffprobe, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(f"ffprobe duration failed: {path}")
    duration = float(result.stdout.strip())
    if not math.isfinite(duration) or duration <= 0:
        raise RuntimeError(f"Invalid audio duration: {path}")
    return duration


def decode(ffmpeg: str, path: Path) -> np.ndarray:
    raw = run(
        ffmpeg,
        [
            "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SAMPLE_RATE),
            "-f", "f32le", "-",
        ],
    ).stdout
    samples = np.frombuffer(raw, dtype="<f4").copy()
    if len(samples) < SAMPLE_RATE or not np.isfinite(samples).all():
        raise RuntimeError(f"Invalid scene audio: {path}")
    return samples


def measure(ffmpeg: str, path: Path, target: float = -19.0) -> dict:
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
    return json.loads(matches[-1])


def speech_profile(samples: np.ndarray, minimum_active_seconds: float = 5.0):
    if len(samples) < STFT_SIZE:
        return None, {"reason": "too-short"}
    frames = np.lib.stride_tricks.sliding_window_view(samples, STFT_SIZE)[::STFT_HOP]
    rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
    rms_db = 20 * np.log10(np.maximum(rms, 1e-12))
    gate_db = max(-45.0, float(np.percentile(rms_db, 75)) - 25.0)
    selected = frames[rms_db >= gate_db]
    active_seconds = len(selected) * STFT_HOP / SAMPLE_RATE
    details = {
        "active_seconds": round(active_seconds, 3),
        "activity_gate_dbfs": round(gate_db, 3),
        "activity_fraction": round(len(selected) / max(1, len(frames)), 4),
    }
    if active_seconds < minimum_active_seconds or len(selected) < 16:
        return None, {**details, "reason": "insufficient-active-audio"}

    power = np.abs(np.fft.rfft(selected * np.hanning(STFT_SIZE), axis=1)) ** 2
    frequencies = np.fft.rfftfreq(STFT_SIZE, 1 / SAMPLE_RATE)
    band_power = np.stack([
        power[:, (frequencies >= lo) & (frequencies < hi)].sum(axis=1)
        for lo, hi in BANDS
    ], axis=1)
    normalized = band_power / np.maximum(band_power.sum(axis=1, keepdims=True), 1e-20)
    profile = np.median(10 * np.log10(np.maximum(normalized, 1e-12)), axis=0)
    return profile, {**details, "reason": "accepted"}


def residual_gain(reference_profile: np.ndarray, profile: np.ndarray) -> np.ndarray:
    residual = reference_profile - profile
    residual -= np.median(residual)
    return np.clip(
        residual * SPECTRAL_SHRINKAGE,
        -SPECTRAL_MAX_GAIN_DB,
        SPECTRAL_MAX_GAIN_DB,
    )


def _window_confidence(reference, profile, scene_profile, details, reference_confidence):
    residual = reference - profile
    residual -= np.median(residual)
    difference = profile - scene_profile
    difference -= np.median(difference)
    shape_distance = float(np.sqrt(np.mean(residual ** 2)))
    scene_distance = float(np.sqrt(np.mean(difference ** 2)))
    coverage = float(np.clip(details.get("activity_fraction", 0), 0, 1))
    activity_quality = min(1.0, details.get("active_seconds", 0) / 3.0) * float(np.clip((coverage - .2) / .6, 0, 1))
    similarity = 1.0 / (1.0 + (shape_distance / 5.0) ** 2)
    temporal_agreement = 1.0 / (1.0 + (scene_distance / 3.0) ** 2)
    confidence = float(np.clip(reference_confidence * activity_quality * similarity * temporal_agreement, 0, 1))
    return confidence, {"shape_distance_db": round(shape_distance, 4),
                        "scene_profile_distance_db": round(scene_distance, 4),
                        "activity_quality": round(activity_quality, 4),
                        "similarity": round(similarity, 4),
                        "temporal_agreement": round(temporal_agreement, 4)}



def build_adaptive_gain_windows(samples: np.ndarray, reference_profile: np.ndarray, *, reference_confidence=1.0):
    duration = len(samples) / SAMPLE_RATE
    centers = np.unique(
        np.clip(
            np.arange(0.0, duration + MATCH_HOP_SECONDS, MATCH_HOP_SECONDS),
            0.0,
            duration,
        )
    )
    raw = []
    details = []
    scene_profile, scene_details = speech_profile(samples, 1.25)
    base_gain = residual_gain(reference_profile, scene_profile) if scene_profile is not None else np.zeros(len(BANDS))
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
        profile, profile_details = speech_profile(segment, 1.25)
        confidence = 0.0
        confidence_metrics = {}
        if profile is None or scene_profile is None:
            gain = np.zeros(len(BANDS))
            confidence_reason = "insufficient-active-audio"
        else:
            confidence, confidence_metrics = _window_confidence(reference_profile, profile, scene_profile, profile_details, reference_confidence)
            confidence_reason = "accepted" if confidence >= .1 else "weak-activity-or-unrepresentative-profile"
            gain = (.8 * base_gain + .2 * residual_gain(reference_profile, profile)) * confidence if confidence >= .1 else np.zeros(len(BANDS))
        raw.append(gain)
        details.append({
            "center_seconds": round(float(center), 3),
            "profile": profile_details,
            "correction_confidence": round(confidence, 4),
            "confidence_reason": confidence_reason,
            "confidence_metrics": confidence_metrics,
            "reference_confidence": reference_confidence,
            "scene_profile": scene_details,
        })

    # Weak windows fade toward zero instead of inheriting another phoneme's EQ.
    filled = np.asarray(raw, dtype=np.float64)

    smoothed = filled.copy()
    if len(filled) > 2:
        smoothed[1:-1] = (
            0.25 * filled[:-2] + 0.50 * filled[1:-1] + 0.25 * filled[2:]
        )
    stable = smoothed.copy()
    for i in range(1, len(stable)):
        stable[i] = stable[i - 1] + np.clip(
            stable[i] - stable[i - 1],
            -SPECTRAL_MAX_SLEW_DB,
            SPECTRAL_MAX_SLEW_DB,
        )
    stable = np.clip(stable, -SPECTRAL_MAX_GAIN_DB, SPECTRAL_MAX_GAIN_DB)
    for index, window_details in enumerate(details):
        window_details["eq_gains_db"] = [round(float(value), 4) for value in stable[index]]
    return centers, stable, details


def apply_spectral_match(
    samples: np.ndarray, centers: np.ndarray, gains: np.ndarray
) -> np.ndarray:
    if not np.any(np.abs(gains) > 1e-6):
        return samples.copy()

    pad = STFT_SIZE // 2
    padded = np.pad(samples.astype(np.float64), (pad, pad), mode="reflect")
    window = np.hanning(STFT_SIZE)
    frequencies = np.fft.rfftfreq(STFT_SIZE, 1 / SAMPLE_RATE)
    band_centers = np.array([math.sqrt(lo * hi) for lo, hi in BANDS])
    control_freqs = np.concatenate(([0.0], band_centers, [SAMPLE_RATE / 2]))
    output = np.zeros_like(padded)
    weight = np.zeros_like(padded)
    last_start = len(padded) - STFT_SIZE
    starts = list(range(0, max(1, last_start + 1), STFT_HOP))
    if starts[-1] != last_start:
        starts.append(last_start)

    for start in starts:
        frame = padded[start:start + STFT_SIZE]
        time_seconds = float(np.clip(
            (start + STFT_SIZE / 2 - pad) / SAMPLE_RATE,
            0.0,
            len(samples) / SAMPLE_RATE,
        ))
        temporal = np.array([
            np.interp(time_seconds, centers, gains[:, band])
            for band in range(len(BANDS))
        ])
        curve = np.interp(
            frequencies,
            control_freqs,
            np.concatenate(([0.0], temporal, [0.0])),
        )
        spectrum = np.fft.rfft(frame * window)
        spectrum *= np.power(10.0, curve / 20.0)
        reconstructed = np.fft.irfft(spectrum, n=STFT_SIZE)
        output[start:start + STFT_SIZE] += reconstructed * window
        weight[start:start + STFT_SIZE] += window ** 2

    valid = weight > 1e-10
    output[valid] /= weight[valid]
    return output[pad:pad + len(samples)].astype(np.float32)


def safe_source(directory: Path, filename: str) -> Path:
    resolved = (directory / filename).resolve()
    if not resolved.is_relative_to(directory.resolve()) or not resolved.is_file():
        raise RuntimeError(f"Missing scene audio or unsafe filename: {filename}")
    return resolved


def copy_passthrough(source: Path, output_dir: Path) -> Path:
    destination = output_dir / source.name
    shutil.copy2(source, destination)
    if file_sha256(source) != file_sha256(destination):
        raise RuntimeError(f"Passthrough copy changed audio: {source.name}")
    return destination


def write_float_wav(
    ffmpeg: str, samples: np.ndarray, raw_path: Path, wav_path: Path
) -> None:
    raw_path.write_bytes(samples.astype("<f4").tobytes())
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
    parser.add_argument("--reference-profile", default=str(DEFAULT_REFERENCE_PATH))
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
        raise RuntimeError("ffmpeg and ffprobe are required.")

    source_manifest = json.loads(input_manifest_path.read_text(encoding="utf-8"))
    scenes = source_manifest.get("scenes") or []
    if not scenes:
        raise RuntimeError("Source TTS manifest has no scenes.")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)

    models = [str(scene.get("model") or "") for scene in scenes]
    voices = {str(scene.get("voice") or "") for scene in scenes}
    if len(voices) != 1 or "" in voices or any(model not in TTS_MODEL_CASCADE for model in models):
        raise RuntimeError("Voice continuity requires one voice and only canonical Gemini models.")
    homogeneous = len(set(models)) == 1 and len(voices) == 1
    result = copy.deepcopy(source_manifest)
    processed_scenes = []

    if homogeneous:
        for scene in scenes:
            source = safe_source(source_dir, scene["file"])
            destination = copy_passthrough(source, output_dir)
            processed = copy.deepcopy(scene)
            processed["file"] = destination.name
            processed["postprocess"] = {
                "version": VERSION,
                "mode": "passthrough-byte-identical",
                "reason": "single-model-single-voice-no-processing-needed",
                "source_sha256": file_sha256(source),
                "output_sha256": file_sha256(destination),
                "byte_identical": True,
                "eq_applied": False,
                "gain_applied": False,
                "limiter_applied": False,
                "resampled": False,
                "reencoded": False,
            }
            processed_scenes.append(processed)
            print(
                f"{scene['id']}: byte-identical passthrough; nenhum efeito aplicado.",
                flush=True,
            )

        result["scenes"] = processed_scenes
        result["postprocess"] = {
            "version": VERSION,
            "mode": "homogeneous-passthrough",
            "models_used": sorted(set(models)),
            "voice": next(iter(voices)),
            "effects_applied": False,
            "source_audio_preserved": True,
            "model_transition_count": 0,
        }
    else:
        reference_model = PRIMARY_MODEL
        inspections = {}
        reference_profiles = []
        reference_loudness = []

        for scene in scenes:
            source = safe_source(source_dir, scene["file"])
            samples = decode(ffmpeg, source)
            loudness = measure(ffmpeg, source)
            profile, details = speech_profile(samples)
            inspections[scene["id"]] = {
                "path": source,
                "samples": samples,
                "loudness": loudness,
            }
            if scene.get("model") == reference_model:
                reference_loudness.append(float(loudness["input_i"]))
                if profile is not None:
                    reference_profiles.append(
                        (scene["id"], profile, details.get("active_seconds", 0.0))
                    )

        episode_sources = [
            {"scene_id": scene_id, "filename": inspections[scene_id]["path"].name,
             "sha256": file_sha256(inspections[scene_id]["path"]),
             "duration_seconds": len(inspections[scene_id]["samples"]) / SAMPLE_RATE,
             "active_seconds": active_seconds}
            for scene_id, _, active_seconds in reference_profiles
        ]
        reference_profile, reference_metadata = select_reference(reference_profiles, next(iter(voices)), args.reference_profile, episode_sources)
        target_lufs = (
            float(np.median(reference_loudness))
            if reference_loudness else -19.0
        )

        for scene in scenes:
            scene_id = scene["id"]
            model = scene.get("model")
            info = inspections[scene_id]
            transition = scene.get("model_transition") or {}
            marker_shift = 0.0
            adaptive_windows = []
            fallback_metrics = {}

            if model == reference_model:
                base_output = copy_passthrough(info["path"], output_dir)
                reason = "reference-model-byte-identical"
                static_gain = 0.0
                eq_applied = False
                gain_applied = False
            else:
                matched = info["samples"].copy()
                gains = np.zeros((1, len(BANDS)))
                reason = "fallback-no-reference-profile"
                if reference_profile is not None:
                    centers, gains, adaptive_windows = build_adaptive_gain_windows(
                        info["samples"], reference_profile,
                        reference_confidence=reference_metadata.get("correction_confidence", 1.0),
                    )
                    matched = apply_spectral_match(
                        info["samples"], centers, gains
                    )
                    reason = f"slow-window-match-{model}-to-{reference_model}"

                raw_path = output_dir / f".{scene_id}.f32"
                premaster = output_dir / f".{scene_id}.premaster.wav"
                base_output = output_dir / f"{scene_id}.wav"
                try:
                    write_float_wav(ffmpeg, matched, raw_path, premaster)
                    pre = measure(ffmpeg, premaster, target_lufs)
                    static_gain, predicted_peak = static_gain_with_peak_guard(target_lufs - float(pre["input_i"]), float(pre["input_tp"]))
                    run(
                        ffmpeg,
                        [
                            "-y", "-i", str(premaster),
                            "-af", f"volume={static_gain:.5f}dB,aresample={SAMPLE_RATE}",
                            "-ar", str(SAMPLE_RATE), "-ac", "1",
                            "-c:a", "pcm_s24le", str(base_output),
                        ],
                    )
                    final_measurement = measure(ffmpeg, base_output, target_lufs)
                    if float(final_measurement["input_tp"]) > TRUE_PEAK_CEILING:
                        raise RuntimeError(f"Fallback true peak exceeds safe static-gain ceiling: {scene_id}")
                    loudness_error = abs(float(final_measurement["input_i"]) - target_lufs)
                    loudness_quality = loudness_assessment(loudness_error)
                    if loudness_quality["loudness_warning"]:
                        print(f"[Voice continuity warning] {scene_id}: {loudness_error:.2f} LU outside target {LOUDNESS_TOLERANCE} LU; within failure limit {LOUDNESS_FAILURE_TOLERANCE} LU, no limiter/compressor applied.", flush=True)
                    if abs(len(decode(ffmpeg, base_output)) - len(info["samples"])) > 2:
                        raise RuntimeError(f"Fallback processing changed sample length: {scene_id}")
                    fallback_metrics = {"input_lufs": float(info["loudness"]["input_i"]),
                                        "output_lufs": float(final_measurement["input_i"]),
                                        "output_true_peak_dbtp": float(final_measurement["input_tp"]),
                                        "target_lufs": target_lufs, "loudness_error_lu": round(loudness_error, 4),
                                        "predicted_peak_before_output_dbtp": round(predicted_peak, 4), **loudness_quality}
                finally:
                    raw_path.unlink(missing_ok=True)
                    premaster.unlink(missing_ok=True)

                eq_applied = bool(np.any(np.abs(gains) > 1e-6))
                gain_applied = abs(static_gain) > 1e-6

            final_output = base_output
            processed = copy.deepcopy(scene)
            processed["file"] = final_output.name
            processed["duration_seconds"] = round(
                duration_seconds(ffprobe, final_output), 6
            )
            if model != reference_model:
                duration_ratio = processed["duration_seconds"] / float(scene["duration_seconds"])
                for timing in processed.get("beat_timings", []):
                    if isinstance(timing.get("audio_offset_seconds"), (int, float)):
                        timing["audio_offset_seconds"] = round(min(processed["duration_seconds"], max(0, timing["audio_offset_seconds"] * duration_ratio)), 6)
            processed["postprocess"] = {
                "version": VERSION,
                "mode": "mixed-model-fallback-only",
                "reason": reason,
                "reference_model": reference_model,
                "reference": reference_metadata,
                **fallback_metrics,
                "adaptive_windows": adaptive_windows,
                "eq_applied": eq_applied,
                "gain_applied": gain_applied,
                "limiter_applied": False,
                "static_gain_db": round(float(static_gain), 4),
                "model_transition_recorded": bool(transition),
                "audible_transition_marker": False,
                "source_sha256": file_sha256(info["path"]),
                "output_sha256": file_sha256(final_output),
                "byte_identical": (
                    model == reference_model
                    and not marker_shift
                    and file_sha256(info["path"]) == file_sha256(final_output)
                ),
            }
            processed_scenes.append(processed)
            print(
                f"{scene_id}: model={model}; eq={eq_applied}; "
                f"gain={static_gain:+.2f}dB; marker={bool(marker_shift)}",
                flush=True,
            )

        result["scenes"] = processed_scenes
        result["output_format"] = "mixed-original-audio-and-48khz-24bit-mono-wav"
        result["total_duration_seconds"] = round(
            sum(float(scene["duration_seconds"]) for scene in processed_scenes),
            6,
        )
        result["postprocess"] = {
            "version": VERSION,
            "mode": "mixed-model-fallback-only",
            "models_used": sorted(set(models)),
            "voice": next(iter(voices)) if len(voices) == 1 else None,
            "reference_model": reference_model,
            "reference": reference_metadata,
            "reference_profile_db": [round(float(value), 6) for value in reference_profile] if reference_profile is not None else None,
            "loudness_target_tolerance_lu": LOUDNESS_TOLERANCE,
            "loudness_failure_tolerance_lu": LOUDNESS_FAILURE_TOLERANCE,
            "loudness_tolerance_scope": "processed-fallback-only; primary and homogeneous episodes stay byte-identical",
            "loudness_warning_scene_ids": [item["id"] for item in processed_scenes if item["postprocess"].get("loudness_warning")],
            "effects_applied": True,
            "primary_or_reference_audio_untouched": True,
            "fallback_only_spectral_match": True,
            "dynamic_loudness_normalization": False,
            "compressor": False,
            "limiter": False,
            "audible_transition_marker": False,
            "model_transition_count": int(
                source_manifest.get("model_transition_count", 0)
            ),
        }

    temporary = output_manifest_path.with_suffix(
        output_manifest_path.suffix + ".tmp"
    )
    temporary.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output_manifest_path)
    print(
        f"Voice continuity v3 complete: {result['postprocess']['mode']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
