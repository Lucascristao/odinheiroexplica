"""Locate visual anchors in final audio with local, confidence-gated ASR.

No TTS or paid API. Unrecognized anchors retain explicitly estimated timing.
Transcription never replaces the narration or creates editorial facts.
"""

import argparse
import copy
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
import hashlib
import json
import math
import os
from pathlib import Path
import re
import unicodedata
import wave

from editorial_project import normalize_project


VERSION = "audio-word-alignment-v2-activity"


def audio_activity(path):
    """Measure raw WAV only; never rewrite, normalize, trim or resample it."""
    import numpy as np
    with wave.open(str(path), "rb") as wav:
        rate, channels, width = wav.getframerate(), wav.getnchannels(), wav.getsampwidth()
        if channels != 1 or width != 2:
            raise ValueError("Atividade Live exige WAV PCM16 mono bruto.")
        samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(np.float64) / 32768
    if not len(samples):
        raise ValueError("WAV Live vazio.")
    duration = len(samples) / rate
    window = max(1, round(rate * .02))
    padded = np.pad(samples, (0, (-len(samples)) % window))
    rms = np.sqrt(np.mean(padded.reshape(-1, window) ** 2, axis=1))
    active = np.flatnonzero(rms > 10 ** (-45 / 20))
    lead = float(active[0] * .02) if len(active) else duration
    last = min(duration, float((active[-1] + 1) * .02)) if len(active) else duration
    return {"method": "raw-pcm-energy-20ms-gate-minus45dbfs", "sample_rate_hz": rate,
            "duration_seconds": round(duration, 6), "lead_seconds": round(lead, 6),
            "tail_seconds": round(duration-last, 6), "active_seconds": round(len(active) * .02, 6),
            "has_activity": bool(len(active)), "rms_dbfs": round(float(20 * np.log10(max(1e-12, np.sqrt(np.mean(samples**2))))), 3),
            "sample_peak_dbfs": round(float(20 * np.log10(max(1e-12, np.max(np.abs(samples))))), 3),
            "caveat": "activity estimates, not exact phonetic boundaries or a listening assessment"}


def tokens(text, aliases=None):
    for original, replacement in (aliases or {}).items():
        text = re.sub(r"\b" + re.escape(original) + r"\b", replacement, text, flags=re.I)
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    result = []
    for token in re.findall(r"\d+(?:[.,]\d+)*|[^\W\d_]+", text):
        if token[0].isdigit():
            try:
                from num2words import num2words
                # Brazilian notation: a dot groups thousands when followed by
                # three digits; a comma separates the fractional portion.
                numeric = token.replace(".", "") if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", token) else token
                token = num2words(Decimal(numeric.replace(",", ".")), lang="pt_BR")
                token = "".join(c for c in unicodedata.normalize("NFKD", token) if not unicodedata.combining(c))
            except (ImportError, ValueError, OverflowError, InvalidOperation):
                pass
        result.extend(re.findall(r"[^\W_]+", token))
    return result


def locate_anchors(narration, beats, recognized, duration, aliases=None):
    expected = tokens(narration, aliases)
    spoken, offsets = [], []
    for word in recognized:
        start, end, probability = (float(word[k]) for k in ("start", "end", "probability"))
        if not all(math.isfinite(v) for v in (start, end, probability)) or not 0 <= start < end <= duration + .1:
            continue
        for token in tokens(str(word["word"]), aliases):
            spoken.append(token)
            offsets.append((start, end, probability))
    matched = {}
    for block in SequenceMatcher(None, expected, spoken, autojunk=False).get_matching_blocks():
        for i in range(block.size):
            matched[block.a + i] = block.b + i
    coverage = len(matched) / max(1, len(expected))
    accepted, diagnostics = {}, []
    previous_offset = -1.0
    previous_index = -1
    for index, beat in enumerate(beats):
        anchor = tokens(str(beat.get("anchor") or ""), aliases)
        positions = [i for i in range(len(expected) - len(anchor) + 1) if anchor and expected[i:i + len(anchor)] == anchor]
        reason = "anchor-not-unique"
        confidence = 0.0
        if len(positions) == 1:
            position = positions[0]
            indices = [matched[i] for i in range(position, position + len(anchor)) if i in matched]
            anchor_coverage = len(indices) / len(anchor)
            confidence = sum(offsets[i][2] for i in indices) / max(1, len(indices))
            reason = "low-confidence-or-coverage"
            contiguous = bool(indices) and all(b == a + 1 for a, b in zip(indices, indices[1:]))
            if coverage >= .65 and anchor_coverage == 1 and contiguous and confidence >= .65 and position in matched:
                offset = offsets[matched[position]][0]
                span = max((offsets[i][1] for i in indices), default=offset) - offset
                earliest = previous_offset + .4 * (index - previous_index) if previous_index >= 0 else (.1 + .4 * index if index else 0.0)
                room_at_end = .4 * (len(beats) - index - 1)
                if span <= max(3.0, len(anchor) * .9) and offset >= earliest and offset <= duration - room_at_end - .1:
                    accepted[index] = {"beat_index": index, "anchor": beat["anchor"], "mark": f"beat-{index}", "audio_offset_seconds": round(offset, 4), "timing_source": "audio-word-alignment", "alignment_confidence": round(confidence, 4)}
                    previous_offset = offset
                    previous_index = index
                    reason = "accepted"
                else:
                    reason = "timing-collision-or-excessive-span"
        diagnostics.append({"beat_index": index, "reason": reason, "confidence": round(confidence, 4)})
    return accepted, {"transcript_coverage": round(coverage, 4), "aligned_beats": len(accepted), "total_beats": len(beats), "beats": diagnostics}


def merge_timings(originals, accepted, duration):
    """Keep located words fixed; interpolate uncertain beats between them."""
    if not accepted:
        return [originals[i] for i in sorted(originals)]
    keys = sorted(originals)
    boundaries = [-1, *sorted(accepted), len(keys)]
    result = {}
    for left, right in zip(boundaries, boundaries[1:]):
        lo = accepted[left]["audio_offset_seconds"] if left in accepted else 0.0
        hi = accepted[right]["audio_offset_seconds"] if right in accepted else duration
        old_lo = originals[left]["audio_offset_seconds"] if left in originals else 0.0
        old_hi = originals[right]["audio_offset_seconds"] if right in originals else duration
        for index in keys:
            if not left < index < right:
                continue
            ratio = (originals[index]["audio_offset_seconds"] - old_lo) / (old_hi - old_lo) if old_hi > old_lo else (index - left) / (right - left)
            lower = lo + .4 * (index - left) if left >= 0 else .1 + .4 * index
            upper = hi - .4 * (right - index) if right < len(keys) else duration - .1 - .4 * (len(keys) - index - 1)
            offset = min(upper, max(lower, lo + max(0.0, min(1.0, ratio)) * (hi - lo)))
            result[index] = {**originals[index], "audio_offset_seconds": round(offset, 4), "timing_source": "estimated-between-audio-anchors"}
    result.update(accepted)
    return [result[i] for i in keys]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--input-manifest", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output-manifest", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--model", default="base")
    args = parser.parse_args()
    source_dir = Path(args.source_dir).resolve()
    project = normalize_project(json.loads(Path(args.project).read_text(encoding="utf-8")))
    result = copy.deepcopy(json.loads(Path(args.input_manifest).read_text(encoding="utf-8")))
    aliases = (project.get("speech") or {}).get("pronunciations") or {}
    scenes = project.get("scenes") or project.get("script", {}).get("scenes", [])
    by_id = {str(s.get("id") or f"scene-{int(s.get('scene_index', s.get('index', i))):02d}"): s for i, s in enumerate(scenes)}
    report = {"version": VERSION, "model": args.model, "engine": "faster-whisper-cpu-int8", "scenes": []}
    model, model_failure = None, None
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=min(4, os.cpu_count() or 2), num_workers=1)
    except Exception as exc:
        model_failure = type(exc).__name__
        print(f"[Alignment] Local recognizer unavailable ({model_failure}); timing remains explicitly estimated.", flush=True)
    for audio in result["scenes"]:
        scene = by_id[audio["id"]]
        path = (source_dir / audio["file"]).resolve()
        if not path.is_relative_to(source_dir) or not path.is_file():
            raise RuntimeError("Missing or unsafe processed audio for alignment.")
        audio_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if audio_hash != (audio.get("postprocess") or {}).get("output_sha256"):
            raise RuntimeError(f"Processed audio hash differs for {audio['id']}.")
        narration_hash = hashlib.sha256(scene["narration"].strip().encode()).hexdigest()
        if narration_hash != audio.get("narration_sha256"):
            raise RuntimeError(f"Narration hash differs for {audio['id']}.")
        audio["audio_activity"] = audio_activity(path)
        scene_aliases = {**aliases, **((scene.get("tts") or {}).get("pronunciations") or {})}
        words = []
        accepted, details = {}, {"aligned_beats": 0, "total_beats": len((scene.get("visual") or {}).get("beats") or []), "reason": model_failure or "no-beats"}
        if model is not None and details["total_beats"]:
            try:
                segments, _ = model.transcribe(str(path), language="pt", beam_size=1, word_timestamps=True, vad_filter=True, condition_on_previous_text=False, temperature=0)
                words = [{"word": w.word, "start": w.start, "end": w.end, "probability": w.probability} for segment in segments for w in (segment.words or [])]
                accepted, details = locate_anchors(scene["narration"], scene["visual"]["beats"], words, float(audio["duration_seconds"]), scene_aliases)
            except Exception as exc:
                details["reason"] = "recognition-failed-" + type(exc).__name__
        originals = {int(item["beat_index"]): item for item in audio.get("beat_timings", [])}
        audio["beat_timings"] = merge_timings(originals, accepted, float(audio["duration_seconds"]))
        audio["alignment"] = {"version": VERSION, "source_audio_sha256": audio_hash, "narration_sha256": narration_hash, "model": args.model, "recognized_words": words, **details}
        report["scenes"].append({"id": audio["id"], **audio["alignment"]})
        print(f"[Alignment] {audio['id']}: {len(accepted)}/{details['total_beats']} anchors located; remaining timings are estimates.", flush=True)
    result["alignment"] = {"version": VERSION, "engine": report["engine"], "model": args.model, "aligned_beats": sum(s["aligned_beats"] for s in report["scenes"]), "total_beats": sum(s["total_beats"] for s in report["scenes"])}
    for path, data in ((args.output_manifest, result), (args.report, report)):
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
