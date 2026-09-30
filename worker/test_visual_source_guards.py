"""Testes offline para impedir recortes documentais falsos ou vazios."""

import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

sys.modules.setdefault("requests", types.ModuleType("requests"))
rembg_stub = sys.modules.setdefault("rembg", types.ModuleType("rembg"))
rembg_stub.new_session = lambda *_args: None
rembg_stub.remove = lambda image, **_kwargs: image

from worker import auto_capture_sources as capture
from worker import prepare_visual_assets as prepare


VALID_ASSET = {
    "id": "report",
    "type": "source_excerpt",
    "source_page_url": "https://example.org/news/specific-report",
    "expected_text": "Specific verified headline",
}


def image_bytes(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.save(output, "PNG")
    return output.getvalue()


def evidence_image() -> Image.Image:
    image = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(image)
    for y in range(30, 260, 24):
        draw.rectangle((20, y, 340, y + 9), fill="black")
    return image


class FakePage:
    def __init__(self, status=200, content=VALID_ASSET["expected_text"]):
        self.status = status
        self.content = content
        self.keyboard = types.SimpleNamespace(press=lambda *_: None)

    def goto(self, *_args, **_kwargs):
        return types.SimpleNamespace(status=self.status)

    def wait_for_timeout(self, _milliseconds):
        pass

    def evaluate(self, script, *_args):
        if "document.body ?" in script:
            return self.content
        return True

    def title(self):
        return "Specific report"

    def screenshot(self, path, **_kwargs):
        evidence_image().save(path)


class FakeContext:
    def __init__(self, page):
        self.page = page

    def new_page(self):
        return self.page

    def close(self):
        pass


class FakeBrowser:
    def __init__(self, page):
        self.page = page

    def new_context(self, **_kwargs):
        return FakeContext(self.page)


class SourceGuardTests(unittest.TestCase):
    def test_requires_specific_url_and_expected_text(self):
        for bad_url in ("https://example.org/", "https://example.org/news/"):
            with self.subTest(url=bad_url), self.assertRaisesRegex(RuntimeError, "página específica"):
                capture.validate_source_asset({**VALID_ASSET, "source_page_url": bad_url})
        with self.assertRaisesRegex(RuntimeError, "expected_text"):
            capture.validate_source_asset({key: value for key, value in VALID_ASSET.items() if key != "expected_text"})

    def test_unavailable_browser_and_http_error_create_no_source_image(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            with self.assertRaisesRegex(RuntimeError, "Playwright indisponível"):
                capture.capture_asset(dict(VALID_ASSET), destination, None)
            with self.assertRaisesRegex(RuntimeError, "página retornou 404"):
                capture.capture_asset(dict(VALID_ASSET), destination, FakeBrowser(FakePage(status=404)))
            self.assertEqual(list(destination.iterdir()), [])

    def test_expected_text_must_be_on_page_before_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            with patch.object(capture, "sanitize_page_thoroughly"):
                with self.assertRaisesRegex(RuntimeError, "expected_text não encontrado"):
                    capture.capture_asset(dict(VALID_ASSET), destination, FakeBrowser(FakePage(content="Different report")))
            self.assertEqual(list(destination.iterdir()), [])

    def test_valid_page_captures_real_pixels(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            with patch.object(capture, "sanitize_page_thoroughly"):
                self.assertTrue(capture.capture_asset(dict(VALID_ASSET), destination, FakeBrowser(FakePage())))
            captured = destination / "report.png"
            self.assertTrue(captured.is_file())
            with Image.open(captured) as image:
                self.assertEqual(image.size, (400, 300))

    def test_blank_and_old_editorial_placeholder_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            blank = Image.new("RGB", (1351, 917), "white")
            with self.assertRaisesRegex(RuntimeError, "quase branco ou vazio"):
                prepare.prepare_excerpt(image_bytes(blank), destination, {"id": "blank"})
            placeholder = blank.copy()
            draw = ImageDraw.Draw(placeholder)
            draw.rectangle((20, 20, 1331, 897), outline="#E2E8F0", width=2)
            draw.text((60, 60), "FONTE: EXEMPLO", fill="#64748B")
            draw.text((60, 140), "Registro de Documento Oficial", fill="#0F172A")
            with self.assertRaisesRegex(RuntimeError, "quase branco ou vazio"):
                prepare.prepare_excerpt(image_bytes(placeholder), destination, {"id": "placeholder"})
            self.assertEqual(list(destination.iterdir()), [])

    def test_real_excerpt_passes_and_missing_capture_path_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            filename, details = prepare.prepare_excerpt(image_bytes(evidence_image()), destination, {"id": "real"})
            self.assertTrue((destination / filename).is_file())
            self.assertEqual(details["width"], 400)

            project_path = destination / "project.json"
            project_path.write_text(
                json.dumps({"visual_assets": [{"id": "missing", "type": "source_excerpt", "capture_file": "research/captures/no-such-capture.png"}]}),
                encoding="utf-8",
            )
            args = ["prepare_visual_assets.py", "--project", str(project_path), "--output-dir", str(destination), "--manifest", str(destination / "manifest.json")]
            with patch.object(sys, "argv", args), self.assertRaisesRegex(RuntimeError, "capture_file não encontrado"):
                prepare.main()

            project_path.write_text(
                json.dumps({"visual_assets": [{"id": "traversal", "type": "source_excerpt", "capture_file": "research/captures/../../outside.png"}]}),
                encoding="utf-8",
            )
            with patch.object(sys, "argv", args), self.assertRaisesRegex(RuntimeError, "research/captures"):
                prepare.main()


class VisualDownloadTests(unittest.TestCase):
    def test_rate_limit_retries_then_uses_original_file(self):
        throttled = types.SimpleNamespace(status_code=429, headers={"Retry-After": "1"})
        image = types.SimpleNamespace(status_code=200, headers={"content-type": "image/jpeg"}, content=b"photo")
        primary = "https://thumb.wikimedia.org/example.jpg"
        fallback = "https://upload.wikimedia.org/example.jpg"
        with patch.object(prepare.requests, "get", side_effect=[throttled, throttled, image], create=True) as get, patch.object(prepare.time, "sleep") as sleep:
            content, content_type = prepare.download(primary, [fallback])
        self.assertEqual((content, content_type), (b"photo", "image/jpeg"))
        self.assertEqual([call.args[0] for call in get.call_args_list], [primary, primary, fallback])
        sleep.assert_called_once_with(1)

    def test_fallback_urls_must_be_https(self):
        with self.assertRaisesRegex(RuntimeError, "https"):
            prepare.download("https://example.org/image.jpg", ["http://example.org/image.jpg"])


if __name__ == "__main__":
    unittest.main()
