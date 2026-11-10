"""Exercise the real voice/render/QA engine on a reviewed evaluation artifact.

Never upload, change privacy, schedule, or write a canonical news episode.
"""
import json
from pathlib import Path
import subprocess
import sys

from news_single_project import validate


def run(*args):
    print("EVALUATION_STAGE", args[0], flush=True)
    subprocess.run(list(args), check=True)


def main():
    episode = validate(json.loads(Path("render-output/news-editorial-evaluation.json").read_text(encoding="utf-8")))
    project = json.loads(Path("video/generated/daily-project.json").read_text(encoding="utf-8"))
    if (project["project_id"] != episode["episode_id"] or project["title"] != episode["title"]
            or project["sources"] != episode["sources"]):
        raise ValueError("Evaluation artifact identity mismatch")
    project_path = "video/generated/daily-project.json"
    def worker(name, *args):
        run(sys.executable, "worker/" + name + ".py", *args)
    worker("validate_voice_policy")
    worker("prepare_visual_assets", "--project", project_path, "--output-dir", "public/generated-assets", "--manifest", "video/generated/daily-visual-assets.json")
    worker("generate_sound_design", "--output-dir", "public/generated-sfx")
    worker("synthesize_scenes", "--input", project_path, "--output-dir", "public/generated-audio/daily", "--manifest", "video/generated/daily-tts-manifest.json", "--diagnostics", "video/generated/daily-live-diagnostics.json")
    worker("process_voice_continuity", "--input-manifest", "video/generated/daily-tts-manifest.json", "--source-dir", "public/generated-audio/daily", "--output-dir", "public/processed-audio/daily", "--output-manifest", "video/generated/daily-processed-tts-manifest.json")
    worker("align_narration", "--project", project_path, "--input-manifest", "video/generated/daily-processed-tts-manifest.json", "--source-dir", "public/processed-audio/daily", "--output-manifest", "video/generated/daily-aligned-tts-manifest.json", "--report", "video/generated/daily-alignment-report.json")
    worker("build_render_input", "--project", project_path, "--tts-manifest", "video/generated/daily-aligned-tts-manifest.json", "--require-gemini", "--require-voice-continuity", "--audio-public-prefix", "processed-audio/daily", "--audio-dir", "public/processed-audio/daily", "--visual-assets-manifest", "video/generated/daily-visual-assets.json", "--output", "video/generated/daily-render-input.json")
    worker("generate_music", "--project", project_path, "--render-input", "video/generated/daily-render-input.json", "--output-dir", "public/generated-music")
    worker("build_youtube_package", "--project", project_path, "--render-input", "video/generated/daily-render-input.json", "--output", "render-output/daily-youtube.json")
    run("npm", "run", "render:daily")
    worker("qa_delivery", "--project", project_path, "--render-input", "video/generated/daily-render-input.json", "--tts-manifest", "video/generated/daily-aligned-tts-manifest.json", "--audio-dir", "public/processed-audio/daily", "--video", "render-output/daily-video.mp4", "--output", "video/generated/daily-delivery-qa.json")
    worker("review_rendered_video", "--input", "video/generated/daily-render-input.json", "--video", "render-output/daily-video.mp4", "--output-dir", "render-output/visual-review")
    print("REAL_VOICE_RENDER_EVALUATION_COMPLETE_NO_UPLOAD", flush=True)


if __name__ == "__main__":
    main()
