"""Offline integration: movement diagnostics must observe encoded pixels, not labels."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from review_rendered_video import review


class EncodedReviewTests(unittest.TestCase):
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
            self.assertTrue((root/"daily-visual-review.zip").is_file())
            self.assertEqual(len(report["video_sha256"]),64)
            with self.assertRaisesRegex(ValueError,"divergem"):
                review(video,{**timeline,"duration_in_frames":120},root/"bad",regions)


if __name__=="__main__":
    unittest.main()
