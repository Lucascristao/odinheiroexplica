"""Display the authored narration with word times from the already-produced WAV.

ASR locates words; it never supplies screen text. Gaps retain explicit estimated
provenance rather than presenting synthetic timing as measured alignment.
"""

from difflib import SequenceMatcher
import hashlib
import math
import re

from align_narration import tokens

VERSION = "editorial-captions-2026-10-01.1"


def build_caption_timing(scene, audio, fps=30, aliases=None):
    narration = str(scene.get("narration") or "").strip()
    original = re.findall(r"\S+", narration)
    duration = float(audio["duration_seconds"])
    total_frames = max(1, math.floor(duration * fps))
    if len(original) > total_frames:
        raise RuntimeError("O áudio não comporta nem um frame por palavra da narração.")
    expected, owners = [], []
    for index, word in enumerate(original):
        for token in tokens(word, aliases):
            expected.append(token)
            owners.append(index)
    spoken, offsets = [], []
    for word in (audio.get("alignment") or {}).get("recognized_words", []):
        try:
            start, end = float(word["start"]), float(word["end"])
            probability = float(word.get("probability", 0))
        except (TypeError, ValueError, KeyError):
            continue
        if not all(math.isfinite(v) for v in (start, end, probability)) or not 0 <= start < end <= duration + .1 or probability < .45:
            continue
        for token in tokens(str(word.get("word") or ""), aliases):
            spoken.append(token)
            offsets.append((max(0, start), min(duration, end)))
    matches = {}
    for block in SequenceMatcher(None, expected, spoken, autojunk=False).get_matching_blocks():
        for offset in range(block.size):
            source_index = block.a + offset
            matches.setdefault(owners[source_index], []).append(offsets[block.b + offset])
    coverage = len(matches) / max(1, len(original))
    # A low-coverage recognition must not drag unrelated narration words into
    # the wrong phrase. Audio activity provides an honest estimated fallback.
    if coverage < .55:
        matches = {}
    activity = audio.get("audio_activity") or {}
    lead = max(0, min(duration, float(activity.get("lead_seconds", 0))))
    ending = max(lead, min(duration, duration - float(activity.get("tail_seconds", 0))))
    if ending - lead < .1:
        lead, ending = 0, duration
    intervals = [None] * len(original)
    previous_end = 0.0
    for index in sorted(matches):
        start = max(previous_end, min(t[0] for t in matches[index]))
        end = max(start, max(t[1] for t in matches[index]))
        if end - start >= .008:
            intervals[index] = (start, end, "audio-word-alignment")
            previous_end = end
    # Fill each unlocated span only between its own neighbouring audio anchors.
    index = 0
    while index < len(intervals):
        if intervals[index] is not None:
            index += 1
            continue
        first = index
        while index < len(intervals) and intervals[index] is None:
            index += 1
        start = intervals[first - 1][1] if first else lead
        end = intervals[index][0] if index < len(intervals) else ending
        end = max(start, end)
        weights = [max(1, len(re.sub(r"\W", "", w))) for w in original[first:index]]
        scale = (end - start) / max(1, sum(weights))
        source = "estimated-between-audio-anchors" if matches else "estimated-audio-activity"
        cursor = start
        for position, weight in zip(range(first, index), weights):
            following = cursor + weight * scale
            intervals[position] = (cursor, following, source)
            cursor = following
    captions = []
    previous_frame = 0
    for index, (word, interval) in enumerate(zip(original, intervals)):
        start, end, source = interval
        latest_end = total_frames - (len(original) - index - 1)
        first = min(latest_end - 1, max(previous_frame, round(start * fps)))
        last = max(first + 1, min(latest_end, round(end * fps)))
        captions.append({"text": word, "start_frame": first, "end_frame": last, "timing_source": source})
        previous_frame = last
    measured = sum(c["timing_source"] == "audio-word-alignment" for c in captions)
    return captions, {
        "version": VERSION,
        "source": "audio-word-alignment" if measured == len(captions) and measured else "mixed-audio-alignment" if measured else "estimated-audio-activity",
        "matched_words": measured,
        "total_words": len(captions),
        "recognition_coverage": round(coverage, 4),
        "audio_sha256": (audio.get("postprocess") or {}).get("output_sha256"),
        "narration_sha256": hashlib.sha256(narration.encode("utf-8")).hexdigest(),
        "caveat": "Estimated intervals are identified per word; ASR never replaces authored text.",
    }
