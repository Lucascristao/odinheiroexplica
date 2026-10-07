"""Extract proof frames and regional movement diagnostics from the final encoded MP4.

Pixel difference is diagnostic, not semantic approval or a retention measurement.
"""
import argparse
import hashlib
import json
import subprocess
import zipfile
import shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw


def review(video: Path, timeline: dict, output: Path, regions: dict) -> dict:
    fps = timeline["fps"]
    output.mkdir(parents=True, exist_ok=True)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video)], check=True, capture_output=True, text=True)
    duration = float(json.loads(probe.stdout)["format"]["duration"])
    expected = timeline["duration_in_frames"] / fps
    if abs(duration-expected) > 1/fps+.01:
        raise ValueError("MP4 e timeline divergem; revisar não deve esconder duração errada.")
    sample_width, sample_height, sample_fps = 480, 270, 2
    decode = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={sample_fps},scale={sample_width}:{sample_height}", "-pix_fmt", "gray", "-f", "rawvideo", "pipe:1"], stdout=subprocess.PIPE)
    previous = None
    motion = []
    frame_size = sample_width*sample_height
    while True:
        data = decode.stdout.read(frame_size)
        if not data:
            break
        if len(data) != frame_size:
            raise ValueError("Frame parcial na análise do MP4.")
        image = np.frombuffer(data, dtype=np.uint8).reshape(sample_height, sample_width).astype(np.float32)
        number = len(motion)
        global_frame = round(number*fps/sample_fps)
        entry = min(regions.get("samples", []), key=lambda s: abs(s["frame"]-global_frame), default={})
        regional = []
        delta = np.abs(image-previous) if previous is not None else np.zeros_like(image)
        for region in entry.get("regions", []):
            x = max(0, min(sample_width-1, round(region["x"]*sample_width/1920)))
            y = max(0, min(sample_height-1, round(region["y"]*sample_height/1080)))
            right = min(sample_width, max(x+1, round((region["x"]+region["w"])*sample_width/1920)))
            bottom = min(sample_height, max(y+1, round((region["y"]+region["h"])*sample_height/1080)))
            regional.append({"element_id": region["id"], "kind": region["kind"], "hyperframes": region["hyperframes"], "mean_delta": round(float(delta[y:bottom, x:right].mean()), 4)})
        motion.append({"seconds": number/sample_fps, "scene_id": entry.get("scene_id"), "mean_delta": round(float(delta.mean()), 4), "regions": regional})
        previous = image
    decode.stdout.close()
    if decode.wait() != 0:
        raise RuntimeError("FFmpeg falhou na análise regional.")
    proofs = []
    for scene in timeline["scenes"]:
        frames = {0, scene["duration_frames"]-1}
        for beat in scene.get("visual", {}).get("beats", []):
            at = beat["resolved_frame"]
            frames.update({max(0, at-6), at, min(scene["duration_frames"]-1, at+max(15, round(beat.get("motion_seconds", .5)*fps)))})
        for i, frame in enumerate(sorted(frames)):
            absolute = scene["start_frame"]+frame
            name = f"{scene['id']}-{i:02d}-{absolute:06d}.jpg"
            path = output/name
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(absolute/fps), "-i", str(video), "-frames:v", "1", "-q:v", "3", str(path)], check=True)
            if not path.is_file():
                raise RuntimeError(f"Quadro não extraído: {absolute}")
            proofs.append({"scene_id": scene["id"], "frame": absolute, "seconds": round(absolute/fps, 3), "file": name})
        selected = [q for q in proofs if q["scene_id"] == scene["id"]][::max(1, len(frames)//8)]
        sheet = Image.new("RGB", (1280, 210*((len(selected)+3)//4)), "#090b0d")
        draw = ImageDraw.Draw(sheet)
        for i, proof in enumerate(selected):
            image = Image.open(output/proof["file"]).convert("RGB")
            image.thumbnail((320, 340))
            x, y = (i%4)*320, (i//4)*210
            sheet.paste(image, (x, y))
            draw.text((x+10, y+185), f"{proof['seconds']:.2f}s", fill="#ffbd19")
        sheet.save(output/f"{scene['id']}-contact.jpg", quality=92)
    with video.open("rb") as video_source:
        video_hash = hashlib.file_digest(video_source, "sha256").hexdigest()
    report = {"version": "1.0", "video_sha256": video_hash, "duration_seconds": duration, "method": {"decode": "final MP4", "sample_fps": sample_fps, "sample_resolution": [sample_width, sample_height], "regions": "Stage resolver; visible object envelopes include labels and entrance/camera", "measure": "mean absolute grayscale difference 0..255"}, "scope": "Quadros reais e diagnóstico de movimento; não aprova semântica, prosódia, fatos, legibilidade raster ou retenção.", "semantic_review": "pending-agent-review", "proofs": proofs, "motion": motion}
    (output/"report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    with zipfile.ZipFile(output.parent/"daily-visual-review.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                archive.write(path, arcname=str(path.relative_to(output)))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--video", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for name in ["daily-delivery-qa.json","daily-source-audit.json","daily-pronunciation-audit.json","daily-voice-master-report.json","daily-hyperframes-manifest.json","daily-rhythm-report.json","daily-alignment-report.json","daily-visual-assets.json","daily-layout-final.json"]:
        source=Path("video/generated")/name
        if source.is_file():
            (output/"evidence").mkdir(exist_ok=True)
            shutil.copyfile(source,output/"evidence"/name)
    subprocess.run(["node", "node_modules/tsx/dist/cli.mjs", "scripts/export-review-regions.ts", args.input, str(output/"regions.json")], check=True)
    report = review(Path(args.video), json.loads(Path(args.input).read_text(encoding="utf-8")), output, json.loads((output/"regions.json").read_text(encoding="utf-8")))
    print(f"Revisão do MP4: {len(report['proofs'])} quadros reais; {len(report['motion'])} amostras regionais. Revisão editorial pendente.")
