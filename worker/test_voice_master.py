"""Offline regression of actual speech energy and level planning across scenes."""
import math
import tempfile
import unittest
import wave
from pathlib import Path
import numpy as np
from align_narration import audio_activity
from voice_master import level_plan,pitch_summary
from build_render_input import validate_preview_mode


class VoiceMasterTests(unittest.TestCase):
    def test_silent_preview_is_explicitly_isolated_from_production(self):
        silent = {"preview_only": True, "engine": "silent-placeholder", "scenes": []}
        real = {"engine": "google-gemini-live", "scenes": []}
        validate_preview_mode(True, False, False, silent)
        validate_preview_mode(False, True, True, real)
        with self.assertRaisesRegex(RuntimeError, "não pode entrar no modo de produção"):
            validate_preview_mode(False, False, False, silent)
        with self.assertRaisesRegex(RuntimeError, "exige manifesto preview_only"):
            validate_preview_mode(True, False, False, real)
        with self.assertRaisesRegex(RuntimeError, "não permite gates de produção"):
            validate_preview_mode(True, True, False, silent)

    def test_pauses_do_not_change_the_level_of_active_speech(self):
        with tempfile.TemporaryDirectory() as folder:
            activities=[]
            for number,padding in enumerate([0,24000*3]):
                tone=np.sin(np.arange(24000*2)*2*np.pi*120/24000)*.1
                samples=np.concatenate([tone,np.zeros(padding)])
                path=Path(folder)/f"scene{number}.wav"
                with wave.open(str(path),"wb") as wav:
                    wav.setparams((1,2,24000,0,"NONE","not compressed"))
                    wav.writeframes((samples*32767).astype("<i2").tobytes())
                activities.append(audio_activity(path))
            self.assertAlmostEqual(activities[0]["active_rms_dbfs"],activities[1]["active_rms_dbfs"],places=2)
            self.assertGreater(abs(activities[0]["rms_dbfs"]-activities[1]["rms_dbfs"]),3)
            plan=level_plan(activities)
            self.assertAlmostEqual(plan["scenes"][0]["gain"],plan["scenes"][1]["gain"],places=3)

    def test_large_volume_difference_is_equalized_without_artificial_gain_clamp(self):
        raw=[{"active_rms_dbfs":-30,"sample_peak_dbfs":-16},{"active_rms_dbfs":-18,"sample_peak_dbfs":-4}]
        plan=level_plan(raw)
        self.assertGreater(plan["scenes"][0]["gain"],1.5)
        actual=[r["active_rms_dbfs"]+20*math.log10(p["gain"]) for r,p in zip(raw,plan["scenes"])]
        self.assertAlmostEqual(actual[0],actual[1],places=6)
        self.assertAlmostEqual(actual[0],-18,places=6)

    def test_peak_constraint_changes_the_shared_target_instead_of_one_scene(self):
        plan=level_plan([{"active_rms_dbfs":-21,"sample_peak_dbfs":0},{"active_rms_dbfs":-28,"sample_peak_dbfs":-12}])
        self.assertLess(plan["target_dbfs"],-21)
        self.assertEqual(plan["scenes"][0]["expected_active_rms_dbfs"],plan["scenes"][1]["expected_active_rms_dbfs"])
        self.assertTrue(all(x["expected_peak_dbfs"]<=20*math.log10(.975)+.001 for x in plan["scenes"]))
        with self.assertRaises(ValueError):
            level_plan([{"active_rms_dbfs":-60,"sample_peak_dbfs":0}])

    def test_pitch_diagnostic_distinguishes_register_and_refuses_silence(self):
        for hz in [120,220]:
            tone=np.sin(np.arange(24000*5)*2*np.pi*hz/24000)*.12
            report=pitch_summary(tone,24000)
            self.assertAlmostEqual(report["median_hz"],hz,delta=3)
            self.assertIn("Estimate",report["scope"])
        self.assertIsNone(pitch_summary(np.zeros(24000*5),24000)["median_hz"])


if __name__=="__main__":
    unittest.main()
