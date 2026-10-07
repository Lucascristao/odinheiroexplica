"""Measured delivery gate before Drive. No synthesis, DSP or subjective listening."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import wave

from align_narration import audio_activity
from voice_master import active_rms
from editorial_project import normalize_project
from gemini_live_fidelity import canonical_tokens, evaluate_transcription
from tts_config import (DEFAULT_PRESENTER, MINIMUM_TRANSCRIPTION_SIMILARITY, PRESENTER_VOICES,
                        PRIMARY_TTS_MODEL, VOICE_POLICY_VERSION, project_pronunciations,
                        project_speech_fingerprint, scene_direction_fingerprint, scene_voice_direction,
                        voice_policy_fingerprint)

VERSION = "gemini-live-delivery-qa-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe_video(path):
    command = ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]
    return json.loads(subprocess.run(command, check=True, capture_output=True, text=True).stdout)


def meter_video(path):
    # Input statistics of the ACTUAL channels. Never use a power-preserving
    # mono downmix to classify clipping: it raises duplicated stereo peaks.
    command = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af",
               "loudnorm=I=-19:TP=-1:LRA=11:print_format=json", "-f", "null", "-"]
    stderr = subprocess.run(command, check=True, capture_output=True, text=True).stderr
    found = re.search(r'\{\s*"input_i".*?\}', stderr, re.S)
    if not found:
        raise ValueError("ffmpeg não retornou métricas de áudio final.")
    measured = json.loads(found.group())
    result = {}
    for source, target in (("input_i", "integrated_lufs"), ("input_tp", "true_peak_dbtp"), ("input_lra", "loudness_range_lu")):
        value = float(measured[source])
        result[target] = value if math.isfinite(value) else None
    result["channel_handling"] = "actual encoded channel layout; no downmix"
    return result


def finite_positive(value):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("Valor precisa ser finito e positivo.")
    return value


def analyze_delivery(project, render_input, manifest, video, audio_dir):
    report = {"version": VERSION, "status": "pass", "failures": [], "warnings": [],
              "scenes": [], "boundaries": [], "video": {}, "subjective_listening_performed": False,
              "limitations": ["No subjective listening: metrics do not certify naturalness, pronunciation or timbre.",
                              "Live output transcript is checked literally; local ASR remains confidence-gated and may misrecognize.",
                              "Activity uses an energy gate, not exact phonetic boundaries.",
                              "WPM and energy differences are diagnostics, never universal speed controls.",
                              "No DSP is applied and no new provider request is made by this gate."]}
    def issue(kind, code, message, scene_id=None, **details):
        report[kind].append({"code": code, "message": message, **({"scene_id": scene_id} if scene_id else {}), **details})

    try:
        project = normalize_project(project)
        fps = finite_positive(render_input["fps"])
        expected_duration = finite_positive(render_input["duration_in_frames"]) / fps
        audio_dir = Path(audio_dir).resolve()
        render_scenes = render_input.get("scenes") or []
        audio_scenes = manifest.get("scenes") or []
        expected_ids = [s["id"] for s in project["scenes"]]
        if [s.get("id") for s in render_scenes] != expected_ids or [s.get("id") for s in audio_scenes] != expected_ids:
            raise ValueError("Cenas do projeto, manifesto e render não correspondem em ordem e quantidade.")
        presenter = (project.get("presenter") or {}).get("gender") or DEFAULT_PRESENTER
        voice = PRESENTER_VOICES[presenter]
        if (manifest.get("engine") != "google-gemini-live" or manifest.get("model") != PRIMARY_TTS_MODEL
                or manifest.get("voice") != voice or manifest.get("fallback_models")
                or manifest.get("fallback_model") or manifest.get("model_transition_count", 0)
                or manifest.get("voice_policy_version") != VOICE_POLICY_VERSION):
            raise ValueError("Manifesto não segue a política Live única e raw atual.")
        public_root = next((p for p in [audio_dir, *audio_dir.parents] if p.name.casefold() == "public"), None)
        previous_end = 0.0
        for scene, rendered, audio in zip(project["scenes"], render_scenes, audio_scenes):
            scene_id = scene["id"]
            try:
                if audio.get("engine") != "google-gemini-live" or audio.get("model") != PRIMARY_TTS_MODEL or audio.get("voice") != voice or audio.get("voice_treatment") != "none" or audio.get("fallback_reason"):
                    raise ValueError("Modelo/voz/tratamento divergente da política raw.")
                if audio.get("voice_policy_version") != VOICE_POLICY_VERSION or audio.get("voice_policy_fingerprint") != voice_policy_fingerprint(PRIMARY_TTS_MODEL, voice):
                    raise ValueError("Fingerprint vocal divergente.")
                if audio.get("speech_profile_fingerprint") != project_speech_fingerprint(project) or audio.get("scene_direction_fingerprint") != scene_direction_fingerprint(scene):
                    raise ValueError("Pronúncia/direção da cena não corresponde ao áudio.")
                if audio.get("narration_sha256") != hashlib.sha256(scene["narration"].strip().encode()).hexdigest():
                    raise ValueError("Narração atual não corresponde ao áudio.")
                path = (audio_dir / audio["file"]).resolve()
                if not path.is_relative_to(audio_dir) or not path.is_file() or path.suffix.lower() != ".wav":
                    raise ValueError("WAV ausente ou caminho inseguro.")
                if public_root is not None:
                    rendered_path = (public_root / rendered["audio_file"]).resolve()
                    if rendered_path != path:
                        raise ValueError("Render aponta para outro arquivo de áudio.")
                elif Path(rendered["audio_file"]).name != path.name:
                    raise ValueError("Arquivo do render difere do manifesto.")
                digest = sha(path)
                post = audio.get("postprocess") or {}
                if (digest != audio.get("audio_sha256") or digest != post.get("source_sha256")
                        or digest != post.get("output_sha256") or post.get("byte_identical") is not True
                        or any(post.get(flag, False) for flag in ("effects_applied", "eq_applied", "gain_applied", "limiter_applied", "compressor_applied", "resampled", "reencoded"))):
                    raise ValueError("Hash/passthrough raw diverge; o WAV deve permanecer byte-idêntico.")
                with wave.open(str(path), "rb") as wav:
                    if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth(), wav.getcomptype()) != (24000, 1, 2, "NONE"):
                        raise ValueError("Formato raw deve ser PCM16 mono de 24 kHz.")
                    duration = finite_positive(wav.getnframes() / wav.getframerate())
                if abs(duration-finite_positive(audio["duration_seconds"])) > .01:
                    raise ValueError("Duração registrada diverge do WAV.")
                aliases = {**project_pronunciations(project), **scene_voice_direction(scene).get("pronunciations", {})}
                fidelity = evaluate_transcription(scene["narration"], audio.get("output_transcription") or "", aliases, MINIMUM_TRANSCRIPTION_SIMILARITY)
                if not fidelity["passed"]:
                    issue("failures", "literal-transcript-mismatch", "Live alterou/omitiu/acrescentou tokens; similaridade global não basta.", scene_id, fidelity=fidelity)
                activity = audio_activity(path)
                if abs(activity["duration_seconds"]-duration) > .0001:
                    raise ValueError("WAV truncado: cabeçalho e amostras decodificadas divergem.")
                if activity["sample_peak_dbfs"] < -80:
                    raise ValueError("WAV vazio de sinal vocal utilizável.")
                start = float(rendered["start_frame"]) / fps
                frame_duration = finite_positive(rendered["duration_frames"]) / fps
                if not math.isfinite(start) or start < 0 or start < previous_end-1e-6:
                    raise ValueError("Linha do tempo contém início inválido ou sobreposição de cenas.")
                if frame_duration + .001 < duration:
                    issue("failures", "timeline-cuts-raw-audio", "Cena termina antes do WAV raw; não cortar nenhuma amostra.", scene_id, audio_seconds=duration, timeline_seconds=frame_duration)
                previous_end = start+frame_duration
                word_count = len(canonical_tokens(scene["narration"], aliases))
                measured = {"id": scene_id, "model": audio["model"], "voice": voice, "audio_sha256": digest,
                            "raw_bytes_verified": True, "start_seconds": start, "end_seconds": previous_end,
                            "audio_seconds": duration, "activity": activity, "spoken_token_count": word_count,
                            "words_per_minute": round(word_count / duration * 60, 2), "fidelity": fidelity}
                report["scenes"].append(measured)
                alignment = audio.get("alignment") or {}
                if alignment.get("source_audio_sha256") and alignment["source_audio_sha256"] != digest:
                    issue("failures", "stale-word-alignment", "Tempos de palavras pertencem a outro áudio.", scene_id)
                beats = audio.get("beat_timings") or []
                for beat in beats:
                    offset = float(beat["audio_offset_seconds"])
                    if not math.isfinite(offset) or not 0 <= offset < duration:
                        issue("failures", "invalid-beat-timing", "Âncora visual fora do áudio.", scene_id)
                estimated = sum(b.get("timing_source") != "audio-word-alignment" for b in beats)
                if estimated:
                    issue("warnings", "estimated-visual-anchors", "Algumas âncoras visuais continuam estimadas; revisar sincronização.", scene_id, count=estimated)
                if alignment.get("transcript_coverage", 1) < .9:
                    issue("warnings", "asr-low-coverage", "ASR local não confirmou toda a fala; não regenerar automaticamente.", scene_id, coverage=alignment.get("transcript_coverage"))
            except (ValueError, KeyError, TypeError, OSError, wave.Error) as exc:
                issue("failures", "scene-integrity", str(exc), scene_id)
        if abs(previous_end-expected_duration) > .001:
            issue("failures", "render-total-duration", "Duração total não corresponde ao fim da última cena.")
        master=render_input.get("voice_master")
        if master:
            import numpy as np
            path=audio_dir/Path(render_input.get("narration_master_audio") or "missing").name
            if not path.is_file() or sha(path)!=master.get("master_sha256"):
                raise ValueError("Trilha contínua ausente ou hash divergente.")
            with wave.open(str(path),"rb") as wav:
                rate=wav.getframerate()
                if (rate,wav.getnchannels(),wav.getsampwidth())!=(24000,1,2):
                    raise ValueError("Trilha contínua deve ser PCM16 mono 24kHz.")
                samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype="<i2").astype(float)/32768
            measured_levels=[]
            target=master["levels"]["target_dbfs"]
            for rendered,audio in zip(render_scenes,audio_scenes):
                start=round(rendered["start_frame"]/fps*rate)
                end=start+round(float(audio["duration_seconds"])*rate)
                level=active_rms(samples[start:end],rate)
                measured_levels.append({"id":rendered["id"],"actual_master_active_rms_dbfs":round(level,3) if level is not None else None})
                if level is None or abs(level-target)>1.5:
                    issue("warnings","master-level-variation","Energia real da fala na trilha contínua exige revisão.",rendered["id"],actual_dbfs=level,target_dbfs=target)
            report["voice_master"]={"sha256_verified":True,"target_dbfs":target,"actual_levels":measured_levels,"pitch_diagnostics":master.get("pitch"),"pitch_correction_applied":False}
            for warning in master.get("warnings",[]):
                issue("warnings","estimated-register-variation","Estimativa de registro variou; conferir por escuta antes de decidir nova síntese.",**warning)
        for current, following in zip(report["scenes"], report["scenes"][1:]):
            gap = following["start_seconds"] + following["activity"]["lead_seconds"] - (current["start_seconds"] + current["audio_seconds"] - current["activity"]["tail_seconds"])
            delta_wpm = following["words_per_minute"]-current["words_per_minute"]
            delta_rms = following["activity"]["rms_dbfs"]-current["activity"]["rms_dbfs"]
            boundary = {"from": current["id"], "to": following["id"], "at_seconds": following["start_seconds"],
                        "activity_gap_seconds": round(gap, 4), "delta_wpm": round(delta_wpm, 2), "delta_rms_db": round(delta_rms, 3)}
            report["boundaries"].append(boundary)
            if gap > 1.2:
                issue("warnings", "long-boundary-pause", "Pausa entre cenas merece revisão narrativa; não é prova de defeito.", following["id"], **boundary)
            if abs(delta_wpm) > current["words_per_minute"]*.25 or abs(delta_rms) > 3:
                issue("warnings", "delivery-variation", "Ritmo/energia variam; considerar texto, números e intenção, sem corrigir velocidade ou volume automaticamente.", following["id"], **boundary)
        video = Path(video)
        if not video.is_file():
            raise ValueError("MP4 final ausente.")
        info = probe_video(video)
        video_streams = [s for s in info["streams"] if s.get("codec_type") == "video"]
        audio_streams = [s for s in info["streams"] if s.get("codec_type") == "audio"]
        if len(video_streams) != 1 or len(audio_streams) != 1:
            raise ValueError("MP4 precisa conter um stream de vídeo e um de áudio.")
        encoded_video_duration = finite_positive(video_streams[0].get("duration") or info["format"]["duration"])
        encoded_audio_duration = finite_positive(audio_streams[0].get("duration") or info["format"]["duration"])
        if abs(encoded_video_duration-expected_duration) > .1 or encoded_audio_duration+.06 < expected_duration:
            issue("failures", "mp4-timeline-coverage", "MP4 não corresponde/cobre a duração planejada.", expected_seconds=expected_duration, video_seconds=encoded_video_duration, audio_seconds=encoded_audio_duration)
        meter = meter_video(video)
        if meter["integrated_lufs"] is None:
            issue("failures", "mp4-silent-audio", "MP4 não contém atividade sonora mensurável.")
        if meter["true_peak_dbtp"] is not None and meter["true_peak_dbtp"] > 0:
            issue("warnings", "mp4-positive-true-peak", "Pico entre amostras acima de 0 dBTP nos canais reais; revisar. Não é sozinho prova de clipping audível.")
        report["video"] = {"file": str(video), "sha256": sha(video), "expected_seconds": expected_duration,
                           "video_seconds": encoded_video_duration, "audio_seconds": encoded_audio_duration,
                           "channels": audio_streams[0].get("channels"), "sample_rate_hz": audio_streams[0].get("sample_rate"), **meter}
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        issue("failures", "delivery-unavailable-or-invalid", str(exc))
    report["status"] = "fail" if report["failures"] else "warn" if report["warnings"] else "pass"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("project", "render-input", "tts-manifest", "video", "output", "audio-dir"):
        parser.add_argument("--"+argument, required=True)
    args = parser.parse_args()
    load = lambda path: json.loads(Path(path).read_text(encoding="utf-8-sig"))
    try:
        report = analyze_delivery(load(args.project), load(args.render_input), load(args.tts_manifest), args.video, args.audio_dir)
    except (OSError, ValueError, TypeError) as exc:
        report = {"version": VERSION, "status": "fail", "failures": [{"code": "input-unavailable", "message": str(exc)}], "warnings": [], "subjective_listening_performed": False}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(f"[Delivery QA] {report['status']}: {len(report['failures'])} falhas, {len(report['warnings'])} avisos; nenhuma escuta subjetiva/API/DSP.", flush=True)
    if report["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
