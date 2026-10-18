"""Synthesize the approved OS4 sketch with ODE's unchanged Gemini Live worker.

Requires GEMINI_API_KEY in the process environment. Never reads credential files.
Only the narrator's channel name is adapted; voice/model/fidelity/cache stay ODE.
"""

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import sys


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ode-root", required=True)
    parser.add_argument("--script", default=str(Path(__file__).parents[1] / "esboco-SVQcs6JUmOc.md"))
    parser.add_argument("--output-dir", default=str(Path(__file__).parent / "audio"))
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()

    source = Path(args.script).resolve()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    source_bytes = source.read_bytes()
    source_text = source_bytes.decode("utf-8-sig")
    narrations = [re.sub(r"\n>\s?", " ", match).strip() for match in re.findall(r"\*\*Locução:\*\*\s*\n\s*> ([\s\S]*?)(?=\n\s*\n)", source_text)]
    if len(narrations) != 3:
        raise RuntimeError(f"Esperadas 3 locuções literais no roteiro; encontradas {len(narrations)}.")

    worker_path = Path(args.ode_root).resolve() / "worker"
    if not (worker_path / "synthesize_scenes.py").is_file():
        raise RuntimeError("Worker de síntese ODE não encontrado.")
    sys.path.insert(0, str(worker_path))
    import tts_config as policy

    original_system_instruction = policy.live_system_instruction

    def os4_system_instruction(pronunciations=None):
        return original_system_instruction(pronunciations).replace(
            "Você é o narrador do canal O Dinheiro Explica.",
            "Você é o narrador do canal OS4 Cortes.",
        )

    policy.live_system_instruction = os4_system_instruction
    import synthesize_scenes as worker

    if worker.PRIMARY_TTS_MODEL != "gemini-3.8-live" or worker.DEFAULT_TTS_VOICE != "Charon":
        raise RuntimeError("A política ODE divergiu do modelo/voz aprovados; síntese interrompida.")

    pronunciation_profile = {"speech": {"pronunciations": {}}}
    speech_fingerprint = worker.project_speech_fingerprint(pronunciation_profile)
    ids = ["abertura", "comentario", "fechamento"]
    jobs = []
    for index, (scene_id, narration) in enumerate(zip(ids, narrations)):
        scene = {"id": scene_id, "narration": narration, "tts": {"delivery": "explain"}}
        direction = worker.scene_voice_direction(scene)
        worker.canonical_tokens(narration, direction.get("pronunciations", {}))
        jobs.append({
            "scene": scene,
            "scene_index": index,
            "scene_id": scene_id,
            "narration": narration,
            "narration_hash": sha256_bytes(narration.encode("utf-8")),
            "output_file": output / f"{scene_id}.wav",
            "direction": direction,
            "direction_fingerprint": worker.scene_direction_fingerprint(scene),
        })

    manifest = {
        "version": "os4-sketch-tts-v1",
        "source_script": source.name,
        "source_script_sha256": sha256_bytes(source_bytes),
        "source_text_unchanged": True,
        "engine": worker.ENGINE,
        "model": worker.PRIMARY_TTS_MODEL,
        "voice": "Charon",
        "presenter_name": "Roberto",
        "channel_identity": "OS4 Cortes",
        "identity_adaptation_only": True,
        "ode_worker_sha256": sha256_bytes((worker_path / "synthesize_scenes.py").read_bytes()),
        "voice_policy_version": worker.VOICE_POLICY_VERSION,
        "voice_policy_fingerprint": worker.voice_policy_fingerprint(worker.PRIMARY_TTS_MODEL, "Charon"),
        "voice_policy_sha256": sha256_bytes((worker_path / "voice-policy.json").read_bytes()),
        "speech_profile_fingerprint": speech_fingerprint,
        "output_format": "pcm-s16le-24000-mono-wav",
        "effects_applied": False,
        "fallback_models": [],
        "sdk_required": worker.GOOGLE_GENAI_REQUIRED_VERSION,
        "sdk_installed": worker.installed_google_genai_version(),
        "credential_present": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
        "scenes": [],
    }
    for job in jobs:
        manifest["scenes"].append({
            "id": job["scene_id"],
            "file": job["output_file"].name,
            "narration": job["narration"],
            "narration_sha256": job["narration_hash"],
            "scene_direction": job["direction"],
            "scene_direction_fingerprint": job["direction_fingerprint"],
        })

    manifest_path = output / "narration-manifest.json"

    def save_manifest():
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.preflight_only:
        manifest["status"] = "ready" if manifest["credential_present"] and manifest["sdk_installed"] == manifest["sdk_required"] else "blocked-local-prerequisites"
        save_manifest()
        print(json.dumps({key: manifest[key] for key in ["status", "model", "voice", "credential_present", "sdk_required", "sdk_installed"]}))
        return

    if not manifest["credential_present"]:
        manifest["status"] = "blocked-credential-unavailable"
        save_manifest()
        raise RuntimeError("GEMINI_API_KEY ausente; executar com o segredo interno do GitHub Actions. Não extrair o segredo.")

    missing = []
    for job in jobs:
        cached = worker.cached_duration(
            job["output_file"], job["narration_hash"], worker.PRIMARY_TTS_MODEL,
            "Charon", worker.NO_VOICE_TREATMENT, speech_fingerprint,
            narration=job["narration"], pronunciations=job["direction"].get("pronunciations", {}),
            direction_fingerprint=job["direction_fingerprint"],
        )
        if cached is None:
            missing.append(job)
    manifest["status"] = "synthesizing"
    save_manifest()
    try:
        asyncio.run(worker.synthesize_missing_jobs(
            missing, gemini_key=os.environ["GEMINI_API_KEY"].strip(), voice="Charon",
            pronunciations={}, speech_fingerprint=speech_fingerprint,
            diagnostics_path=output / "live-diagnostics.json",
        ))
    except Exception:
        manifest["status"] = "failed"
        save_manifest()
        raise

    for scene, job in zip(manifest["scenes"], jobs):
        sidecar = json.loads(job["output_file"].with_suffix(".tts.json").read_text(encoding="utf-8"))
        fidelity = worker.evaluate_transcription(
            job["narration"], sidecar["output_transcription"], job["direction"].get("pronunciations", {}),
            worker.MINIMUM_TRANSCRIPTION_SIMILARITY,
        )
        if not fidelity["passed"]:
            raise RuntimeError(f"Fidelidade rejeitada após síntese: {job['scene_id']}")
        scene.update({
            "duration_seconds": worker.duration_seconds(job["output_file"]),
            "audio_sha256": worker.audio_sha256(job["output_file"]),
            "output_transcription": sidecar["output_transcription"],
            "output_fidelity": fidelity,
            "cache_validated": True,
        })
    manifest["status"] = "success"
    manifest["total_duration_seconds"] = round(sum(scene["duration_seconds"] for scene in manifest["scenes"]), 3)
    save_manifest()
    print(json.dumps({"status": "success", "model": manifest["model"], "voice": manifest["voice"], "scenes": [{"id": scene["id"], "duration_seconds": scene["duration_seconds"], "fidelity_passed": scene["output_fidelity"]["passed"]} for scene in manifest["scenes"]]}))


if __name__ == "__main__":
    main()
