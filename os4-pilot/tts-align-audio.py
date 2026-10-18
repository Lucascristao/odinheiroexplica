"""Align canonical OS4 narration words to real audio; never rewrite the script.

Dependency: faster-whisper. CPU/int8, Portuguese, word timestamps. The runner may
download the explicitly selected ASR model. This helper never synthesizes audio.
"""

import argparse
from difflib import SequenceMatcher
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import unicodedata
import wave


VERSION = "os4-canonical-word-alignment-v2-vocabulary-prompt"
MINIMUM_COVERAGE = 0.85
MAXIMUM_UNMATCHED_CANONICAL_GROUP = 2
ASR_VOCABULARY_PROMPT = "Roberta Luchsinger, Lulinha, Antônio Camilo, Anvisa."


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized(token):
    plain = unicodedata.normalize("NFKD", token.casefold())
    return "".join(char for char in plain if not unicodedata.combining(char) and char.isalnum())


def canonical_words(narration):
    words = [token for token in re.findall(r"\S+", narration) if normalized(token)]
    if not words:
        raise ValueError("Narração canônica vazia.")
    return words


def split_timed_asr_words(segments):
    """Expand provider word groups without discarding their measured span."""
    words = []
    segment_texts = []
    for segment in segments:
        segment_texts.append(str(segment.text).strip())
        for word in segment.words or []:
            tokens = [token for token in re.findall(r"\S+", word.word) if normalized(token)]
            if not tokens:
                continue
            start = max(0.0, float(word.start))
            end = max(start, float(word.end))
            weights = [max(1, len(normalized(token))) for token in tokens]
            total = sum(weights)
            position = 0
            for token, weight in zip(tokens, weights):
                words.append({
                    "texto": token,
                    "inicio": start + (end - start) * position / total,
                    "fim": start + (end - start) * (position + weight) / total,
                })
                position += weight
    return words, " ".join(segment_texts)


def fold_known_entity_spellings(words):
    """Merge split spellings for matching only; canonical text remains intact."""
    aliases = {("lu", "linha"): "lulinha", ("an", "visa"): "anvisa"}
    folded = []
    index = 0
    while index < len(words):
        pair = tuple(normalized(item["texto"]) for item in words[index:index + 2])
        if len(pair) == 2 and pair in aliases:
            folded.append({
                "texto": aliases[pair],
                "inicio": words[index]["inicio"],
                "fim": words[index + 1]["fim"],
                "asr_original": " ".join(item["texto"] for item in words[index:index + 2]),
            })
            index += 2
        else:
            folded.append(dict(words[index]))
            index += 1
    return folded


def distribute_canonical_span(tokens, start, end, method):
    if end <= start:
        raise ValueError("Não há intervalo de áudio positivo para as palavras canônicas.")
    weights = [max(1, len(normalized(token))) for token in tokens]
    total = sum(weights)
    result = []
    position = 0
    for token, weight in zip(tokens, weights):
        result.append({
            "texto": token,
            "inicio": start + (end - start) * position / total,
            "fim": start + (end - start) * (position + weight) / total,
            "timing_source": method,
        })
        position += weight
    return result


def align_scene(narration, asr_words, duration):
    expected = canonical_words(narration)
    observed = fold_known_entity_spellings(asr_words)
    matcher = SequenceMatcher(
        None, [normalized(word) for word in expected],
        [normalized(word["texto"]) for word in observed], autojunk=False,
    )
    opcodes = matcher.get_opcodes()
    matched_count = sum(i2 - i1 for tag, i1, i2, _, _ in opcodes if tag == "equal")
    coverage = matched_count / len(expected)
    diagnostics = {
        "canonical_word_count": len(expected),
        "asr_word_count": len(asr_words),
        "matching_asr_word_count": len(observed),
        "direct_matched_word_count": matched_count,
        "direct_coverage": round(coverage, 6),
        "minimum_required_coverage": MINIMUM_COVERAGE,
        "maximum_unmatched_canonical_group": MAXIMUM_UNMATCHED_CANONICAL_GROUP,
        "corrections": [],
        "asr_insertions": [],
        "failures": [],
    }
    if coverage < MINIMUM_COVERAGE:
        diagnostics["failures"].append(f"Cobertura direta {coverage:.3f} abaixo de {MINIMUM_COVERAGE:.2f}.")

    aligned = [None] * len(expected)
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            for canonical_index, asr_index in zip(range(i1, i2), range(j1, j2)):
                word = observed[asr_index]
                aligned[canonical_index] = {
                    "texto": expected[canonical_index],
                    "inicio": word["inicio"],
                    "fim": word["fim"],
                    "timing_source": "asr-exact-normalized",
                }
        elif tag == "insert":
            diagnostics["asr_insertions"].append({
                "after_canonical_index": i1 - 1,
                "asr_text": " ".join(word["texto"] for word in observed[j1:j2]),
                "inicio": observed[j1]["inicio"],
                "fim": observed[j2 - 1]["fim"],
            })

    for tag, i1, i2, j1, j2 in opcodes:
        if tag not in {"replace", "delete"}:
            continue
        tokens = expected[i1:i2]
        correction = {
            "canonical_start_index": i1,
            "canonical_text": " ".join(tokens),
            "asr_text": " ".join(word["texto"] for word in observed[j1:j2]),
            "canonical_count": len(tokens),
            "kind": tag,
        }
        if len(tokens) > MAXIMUM_UNMATCHED_CANONICAL_GROUP:
            diagnostics["failures"].append(f"Grupo canônico ausente/divergente de {len(tokens)} palavras no índice {i1}.")
            correction["accepted"] = False
        elif tag == "replace" and j1 < j2:
            aligned[i1:i2] = distribute_canonical_span(
                tokens, observed[j1]["inicio"], observed[j2 - 1]["fim"], "asr-span-canonical-correction",
            )
            correction["accepted"] = True
        elif 0 < i1 and i2 < len(expected) and aligned[i1 - 1] is not None and aligned[i2] is not None:
            start = aligned[i1 - 1]["fim"]
            end = aligned[i2]["inicio"]
            if end > start and end - start <= max(1.2, len(tokens) * 0.7):
                aligned[i1:i2] = distribute_canonical_span(tokens, start, end, "interpolated-between-asr-anchors")
                correction["accepted"] = True
            else:
                diagnostics["failures"].append(f"Intervalo inadequado entre âncoras no índice {i1}.")
                correction["accepted"] = False
        else:
            diagnostics["failures"].append(f"Grupo ausente sem duas âncoras no índice {i1}.")
            correction["accepted"] = False
        diagnostics["corrections"].append(correction)

    # An ASR insertion is diagnostic only; it can never replace editorial text.
    # Long unexplained ASR runs warrant manual review even with high match rate.
    for insertion in diagnostics["asr_insertions"]:
        if len(insertion["asr_text"].split()) > 2:
            diagnostics["failures"].append("Grupo ASR adicional com mais de duas palavras; revisar áudio.")

    if any(word is None for word in aligned):
        diagnostics["failures"].append("Existem palavras canônicas sem tempo confiável.")
    if not diagnostics["failures"]:
        previous_start = -1.0
        for index, word in enumerate(aligned):
            start = float(word["inicio"])
            end = float(word["fim"])
            if start < previous_start - 0.03 or end <= start or end > duration + 0.12:
                diagnostics["failures"].append(f"Tempo inválido/não monotônico na palavra {index}.")
                break
            previous_start = start
    diagnostics["passed"] = not diagnostics["failures"]
    diagnostics["final_canonical_coverage"] = round(sum(word is not None for word in aligned) / len(expected), 6)
    if diagnostics["passed"] and [word["texto"] for word in aligned] != expected:
        raise AssertionError("Alinhamento tentou alterar texto canônico.")
    words = [{"texto": word["texto"], "inicio": round(word["inicio"], 4), "fim": round(min(duration, word["fim"]), 4)} for word in aligned if word is not None]
    sources = [word["timing_source"] if word else "unresolved" for word in aligned]
    diagnostics["timing_sources"] = sources
    return words, diagnostics


def audio_duration(path):
    with wave.open(str(path), "rb") as source:
        return source.getnframes() / source.getframerate()


def cache_valid(cache, manifest, audio_dir, model):
    if not cache or cache.get("version") != VERSION or cache.get("status") != "success" or cache.get("asr_model") != model:
        return False
    cached_scenes = {scene["id"]: scene for scene in cache.get("scenes", [])}
    if set(cached_scenes) != {scene["id"] for scene in manifest.get("scenes", [])}:
        return False
    for scene in manifest["scenes"]:
        cached = cached_scenes[scene["id"]]
        audio_file = audio_dir / scene["file"]
        expected_tokens = canonical_words(scene["narration"])
        if cached.get("audio_sha256") != sha256_file(audio_file) or cached.get("narration_sha256") != hashlib.sha256(scene["narration"].encode("utf-8")).hexdigest():
            return False
        if not cached.get("diagnostics", {}).get("passed") or cached.get("coverage", 0) < MINIMUM_COVERAGE:
            return False
        if [word["texto"] for word in cached.get("palavras", [])] != expected_tokens:
            return False
        duration = audio_duration(audio_file)
        previous_start = -1.0
        for word in cached["palavras"]:
            if not (0 <= word["inicio"] < word["fim"] <= duration + 0.01) or word["inicio"] < previous_start - 0.03:
                return False
            previous_start = word["inicio"]
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-dir", default="audio")
    parser.add_argument("--model", default="base")
    args = parser.parse_args()
    audio_dir = Path(args.audio_dir).resolve()
    manifest = json.loads((audio_dir / "narration-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "success":
        raise RuntimeError("Narração ainda não concluída; alinhamento não executado.")
    output_file = audio_dir / "aligned-words.json"
    try:
        cached = json.loads(output_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cached = None
    if cache_valid(cached, manifest, audio_dir, args.model):
        print(json.dumps({"status": "cache-valid", "scenes": len(cached["scenes"])}))
        return

    from faster_whisper import WhisperModel
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    result = {
        "version": VERSION,
        "status": "running",
        "asr_engine": "faster-whisper",
        "asr_package_version": importlib.metadata.version("faster-whisper"),
        "asr_model": args.model,
        "device": "cpu",
        "compute_type": "int8",
        "language": "pt",
        "word_timestamps": True,
        "initial_prompt": ASR_VOCABULARY_PROMPT,
        "canonical_text_preserved": True,
        "minimum_required_coverage": MINIMUM_COVERAGE,
        "scenes": [],
    }
    for scene in manifest["scenes"]:
        audio_file = audio_dir / scene["file"]
        actual_hash = sha256_file(audio_file)
        if actual_hash != scene["audio_sha256"]:
            raise RuntimeError(f"Hash do WAV divergiu do manifesto: {scene['id']}")
        duration = audio_duration(audio_file)
        segments, info = model.transcribe(
            str(audio_file), language="pt", word_timestamps=True,
            initial_prompt=ASR_VOCABULARY_PROMPT, beam_size=5,
            condition_on_previous_text=False, vad_filter=False,
        )
        asr_words, asr_text = split_timed_asr_words(segments)
        words, diagnostics = align_scene(scene["narration"], asr_words, duration)
        aligned_scene = {
            "id": scene["id"],
            "file": scene["file"],
            "audio_sha256": actual_hash,
            "narration_sha256": hashlib.sha256(scene["narration"].encode("utf-8")).hexdigest(),
            "duration_seconds": round(duration, 6),
            "narration": scene["narration"],
            "asr_text": asr_text,
            "asr_language": info.language,
            "coverage": diagnostics["direct_coverage"],
            "palavras": words,
            "diagnostics": diagnostics,
        }
        result["scenes"].append(aligned_scene)
        output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"id": scene["id"], "coverage": aligned_scene["coverage"], "passed": diagnostics["passed"], "words": len(words)}, ensure_ascii=False), flush=True)
    result["status"] = "success" if all(scene["diagnostics"]["passed"] for scene in result["scenes"]) else "failed-alignment"
    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if result["status"] != "success":
        raise RuntimeError("Alinhamento reprovado; consultar diagnósticos sem substituir roteiro por ASR.")


if __name__ == "__main__":
    main()
