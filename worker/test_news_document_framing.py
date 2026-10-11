"""A real narrow paragraph must remain in its article and visible in motion."""
import copy
import unittest
from news_document_framing import apply_news_document_views, contextual_proof_views


class DocumentaryCameraTests(unittest.TestCase):
    def test_thin_aneel_passage_and_edge_proofs_stay_inside_each_view(self):
        proofs = [
            {"x": 7.647, "y": 26.667, "width": 84.706, "height": 6.222},
            {"x": 75, "y": 92, "width": 25, "height": 8},
            {"x": 0, "y": 0, "width": 100, "height": 100},
        ]
        for proof in proofs:
            wide, close = contextual_proof_views(proof)
            for view in (wide, close):
                self.assertLessEqual(view["x"], proof["x"])
                self.assertLessEqual(view["y"], proof["y"])
                self.assertGreaterEqual(view["x"] + view["width"], proof["x"] + proof["width"])
                self.assertGreaterEqual(view["y"] + view["height"], proof["y"] + proof["height"])
                self.assertGreaterEqual(view["height"], 40)
                self.assertLessEqual(view["x"] + view["width"], 100)
                self.assertLessEqual(view["y"] + view["height"], 100)
            # Linear interpolation between these rectangles also contains proof.
            for progress in (.1, .5, .9):
                view = {key: wide[key] + (close[key]-wide[key])*progress for key in wide}
                self.assertLessEqual(view["y"], proof["y"])
                self.assertGreaterEqual(view["y"] + view["height"], proof["y"] + proof["height"])

    def test_contextual_cues_reframe_but_authored_and_historical_views_are_preserved(self):
        prepared = {"proof_region": {"x": 10, "y": 25, "width": 80, "height": 8}}
        beats = [{"anchor": "first"}, {"anchor": "second"}, {"anchor": "third"}]
        apply_news_document_views({"document_context_seconds": 1.6}, prepared, beats)
        self.assertNotEqual(beats[0]["view"], beats[1]["view"])
        self.assertEqual(beats[0]["view"], beats[2]["view"])
        authored = [{"view": {"x": 0, "y": 0, "width": 100, "height": 100}}, {}]
        original = copy.deepcopy(authored)
        apply_news_document_views({"document_context_seconds": 1.6}, prepared, authored)
        self.assertEqual(authored, original)
        historical = [{}, {}]
        apply_news_document_views({}, prepared, historical)
        self.assertEqual(historical, [{"view": prepared["proof_region"]}, {}])


if __name__ == "__main__":
    unittest.main()
