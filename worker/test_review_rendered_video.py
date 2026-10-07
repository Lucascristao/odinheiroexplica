"""Offline integration: movement diagnostics must observe encoded pixels, not labels."""
import subprocess
import tempfile
import unittest
import wave
import json
from pathlib import Path
from review_rendered_video import review, plan_review_samples


class EncodedReviewTests(unittest.TestCase):
    def test_complete_events_and_intervals_survive_sampling(self):
        scene={"duration_frames":300,"visual":{"beats":[{"resolved_frame":0,"motion_seconds":.5,"anchor":"opening","timing_source":"text-fallback"},{"resolved_frame":90,"motion_seconds":2},{"resolved_frame":100}]}}
        groups=plan_review_samples(scene,30)
        self.assertEqual([s["role"] for s in groups[0]["samples"]],["before","during","after","interval"])
        self.assertGreater(groups[0]["samples"][3]["local_frame"],15)
        self.assertEqual(groups[0]["timing_source"],"text-fallback")
        self.assertFalse(groups[1]["completed_before_next_event"])
        self.assertLessEqual(max(s["local_frame"] for s in groups[1]["samples"]),99)
        self.assertEqual(groups[-1]["samples"][-1]["local_frame"],299)
        self.assertTrue(all(0<=s["local_frame"]<300 for g in groups for s in g["samples"]))
        with self.assertRaisesRegex(ValueError,"fora"):
            plan_review_samples({"duration_frames":30,"visual":{"beats":[{"resolved_frame":30}]}},30)

    def test_actual_change_and_pending_semantic_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            video=root/"proof.mp4"
            # Remotion's lean FFmpeg omits lavfi color/drawbox. Feed real RGB frames.
            raw=root/"frames.rgb"
            with raw.open("wb") as file:
                file.write(bytes(320*180*3)*45)
                file.write(bytes([255])*(320*180*3)*45)
            subprocess.run(["ffmpeg","-v","error","-f","rawvideo","-pixel_format","rgb24","-video_size","320x180","-framerate","30","-i",str(raw),"-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p",str(video)],check=True)
            timeline={"fps":30,"duration_in_frames":90,"scenes":[{"id":"s","start_frame":0,"duration_frames":90,"visual":{"beats":[{"resolved_frame":45}]}}]}
            regions={"samples":[{"frame":0,"scene_id":"s","regions":[{"id":"hero","kind":"object","hyperframes":True,"x":0,"y":0,"w":1920,"h":1080}]}]}
            report=review(video,timeline,root/"review",regions)
            self.assertEqual(report["semantic_review"],"pending-agent-review")
            self.assertGreater(max(x["mean_delta"] for x in report["motion"]),200)
            self.assertEqual(report["motion"][1]["mean_delta"],0)
            self.assertTrue(all((root/"review"/p["file"]).is_file() for p in report["proofs"]))
            # The old strided sheet could hide the settled white result.
            after=next(s for s in report["sample_groups"][0]["samples"] if s["role"]=="after")
            self.assertGreater(after["frame"],45)
            from PIL import Image
            with Image.open(root/"review"/after["file"]) as image:
                self.assertGreater(image.getpixel((160,90))[0],240)
            self.assertTrue((root/"daily-visual-review.zip").is_file())
            self.assertEqual(len(report["video_sha256"]),64)
            # Audio/AAC tail affects MP4 container duration, not the video clock.
            audio=root/"tail.wav"
            with wave.open(str(audio),"wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(24000)
                wav.writeframes(bytes(round(3.2*24000)*2))
            muxed=root/"proof-aac.mp4"
            subprocess.run(["ffmpeg","-v","error","-i",str(video),"-i",str(audio),"-c:v","copy","-c:a","aac",str(muxed)],check=True)
            probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(muxed)],text=True))
            self.assertGreater(float(probe["format"]["duration"]),3.1)
            padded=review(muxed,timeline,root/"padded",regions)
            self.assertAlmostEqual(padded["duration_seconds"],3.0)
            self.assertGreater(padded["container_duration_seconds"],3.1)
            with self.assertRaisesRegex(ValueError,"divergem"):
                review(video,{**timeline,"duration_in_frames":120},root/"bad",regions)


if __name__=="__main__":
    unittest.main()
