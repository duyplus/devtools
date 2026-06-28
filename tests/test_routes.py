from io import BytesIO
import unittest

from PIL import Image

from app import create_app
from app.i18n import translate


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True})
        self.client = self.app.test_client()

    def test_pages_load(self):
        for path in (
            "/",
            "/tools/icon-converter",
            "/tools/comma-delimiter",
            "/tools/text-diff",
            "/tools/percentage-calculator",
            "/tools/base64-converter",
            "/tools/js-obfuscator",
            "/tools/password-generator",
            "/tools/qr-generator",
            "/healthz",
        ):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)

    def test_delimiter_post(self):
        response = self.client.get("/tools/comma-delimiter")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data-delimiter-tool", response.data)
        self.assertIn(b"data-delimiter-error", response.data)
        self.assertIn(b"data-line-numbers-for=\"delimiter-source\"", response.data)
        self.assertIn(b"data-line-numbers-for=\"delimiter-result\"", response.data)

        response = self.client.post(
            "/tools/comma-delimiter",
            data={
                "text": "a\nb",
                "input_delimiter": "newline",
                "output_delimiter": "comma",
                "trim": "on",
                "remove_blank": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"a,b", response.data)

    def test_base64_post(self):
        response = self.client.get("/tools/base64-converter")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data-base64-tool", response.data)
        self.assertIn(b"data-line-numbers-for=\"base64-source\"", response.data)
        self.assertIn(b"data-line-numbers-for=\"base64-result\"", response.data)

        response = self.client.post(
            "/tools/base64-converter",
            data={
                "text": "Xin chào",
                "mode": "encode",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"WGluIGNow6Bv", response.data)

        response = self.client.post(
            "/tools/base64-converter",
            data={
                "text": "WGluIGNow6Bv",
                "mode": "decode",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Xin chào".encode("utf-8"), response.data)

    def test_javascript_tool_post(self):
        response = self.client.get("/tools/js-obfuscator")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data-javascript-tool", response.data)
        self.assertIn(b"/tools/js-obfuscator/convert", response.data)
        self.assertIn(b"data-line-numbers-for=\"javascript-source\"", response.data)
        self.assertIn(b"data-line-numbers-for=\"javascript-result\"", response.data)

        response = self.client.post(
            "/tools/js-obfuscator",
            data={
                "text": "console.log(1);",
                "mode": "obfuscate",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"TextDecoder", response.data)

        response = self.client.post(
            "/tools/js-obfuscator",
            data={
                "text": 'eval(atob("Y29uc29sZS5sb2coMSk7"))',
                "mode": "deobfuscate",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"console.log(1);", response.data)

        response = self.client.post(
            "/tools/js-obfuscator/convert",
            data={
                "text": "console.log(1);",
                "mode": "obfuscate",
                "compact": "on",
                "string_array": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["error"], "")
        self.assertIn("devtools-js-obfuscator:v2", response.json["result"])

    def test_password_post(self):
        response = self.client.get("/tools/password-generator")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data-password-error", response.data)
        self.assertIn(b"data-password-no-types", response.data)
        self.assertIn(b"data-line-numbers-for=\"password-result\"", response.data)

        response = self.client.post(
            "/tools/password-generator",
            data={
                "length": "16",
                "count": "2",
                "lowercase": "on",
                "uppercase": "on",
                "digits": "on",
                "symbols": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data-password-tool", response.data)

    def test_text_diff_post(self):
        response = self.client.post(
            "/tools/text-diff",
            data={
                "left_text": "a\nb\nc\n",
                "right_text": "a\nB\nc\nd\n",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data-text-diff-tool", response.data)
        self.assertIn(b"data-line-numbers-for=\"text-diff-left\"", response.data)
        self.assertIn(b"data-line-numbers-for=\"text-diff-right\"", response.data)
        self.assertIn(b"diff-line-modified", response.data)
        self.assertIn(b"diff-line-added", response.data)
        self.assertIn('class="textdiff-total-lines">3 dòng</span>'.encode(), response.data)
        self.assertIn('class="textdiff-total-lines">4 dòng</span>'.encode(), response.data)

    def test_qr_post(self):
        response = self.client.get("/tools/qr-generator")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data-qr-tool", response.data)
        self.assertNotIn(b'name="frame_text_enabled" checked', response.data)
        self.assertNotIn(b'type="submit"', response.data)
        self.assertIn(b'name="size" type="range" min="100" max="550" step="50"', response.data)

        response = self.client.post(
            "/tools/qr-generator",
            data={
                "type": "url",
                "url": "example.com",
                "size": "350",
                "foreground": "#000000",
                "background": "#ffffff",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data:image/png;base64,", response.data)
        self.assertIn(b"data:image/jpeg;base64,", response.data)
        self.assertIn(b"data:image/svg+xml;base64,", response.data)
        self.assertIn(b"data-copy-image-button", response.data)
        self.assertIn(b"--qr-preview-size: 350px", response.data)

    def test_qr_error_can_show_toast(self):
        response = self.client.post("/tools/qr-generator", data={"type": "url", "url": ""})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data-toast-error", response.data)
        self.assertIn("URL là bắt buộc.".encode(), response.data)

    def test_percentage_page_has_live_calculators(self):
        response = self.client.get("/tools/percentage-calculator")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-percentage-row="of"', response.data)
        self.assertIn(b'data-percentage-row="ratio"', response.data)
        self.assertIn(b'data-percentage-row="change"', response.data)
        self.assertIn(b'data-percentage-row="total"', response.data)
        self.assertEqual(response.data.count(b"<input"), 12)
        self.assertEqual(response.data.count(b"<select"), 1)

    def test_vietnamese_language_switch(self):
        response = self.client.get("/?lang=vi")
        self.assertEqual(response.status_code, 200)
        self.assertIn(translate("vi", "app.subtitle").encode("utf-8"), response.data)
        self.assertIn("devtools_lang=vi", response.headers.get("Set-Cookie", ""))

    def test_topbar_breadcrumb(self):
        response = self.client.get("/tools/comma-delimiter")
        self.assertEqual(response.status_code, 200)
        self.assertIn(translate("vi", "breadcrumb.home").encode("utf-8"), response.data)
        self.assertIn(translate("vi", "tool.delimiter.name").encode("utf-8"), response.data)
        self.assertIn(b'data-lucide="home"', response.data)
        self.assertIn(b'data-lucide="list-filter"', response.data)

    def test_icon_invalid_upload(self):
        response = self.client.post(
            "/tools/icon-converter",
            data={"mode": "ico", "sizes": ["16"], "image": (BytesIO(b"bad"), "bad.txt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(translate("vi", "icons.error.invalid").encode("utf-8"), response.data)

    def test_icon_valid_upload(self):
        image = BytesIO()
        Image.new("RGBA", (128, 128), (255, 0, 0, 255)).save(image, format="PNG")
        image.seek(0)
        response = self.client.post(
            "/tools/icon-converter",
            data={
                "mode": "ico",
                "bit_depth": "32",
                "sizes": ["16", "32", "48"],
                "image": (image, "icon.png"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "image/x-icon")
        with Image.open(BytesIO(response.data)) as icon:
            self.assertEqual(icon.size, (48, 48))
            self.assertEqual(icon.ico.sizes(), {(16, 16), (32, 32), (48, 48)})

    def test_ajax_post_contracts(self):
        headers = {"X-Requested-With": "fetch"}
        image = BytesIO()
        Image.new("RGBA", (64, 64), (0, 128, 255, 255)).save(image, format="PNG")
        image.seek(0)
        response = self.client.post(
            "/tools/icon-converter",
            data={
                "mode": "ico",
                "bit_depth": "32",
                "sizes": ["16"],
                "image": (image, "icon.png"),
            },
            content_type="multipart/form-data",
            headers=headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response.headers.get("Content-Disposition", ""))


if __name__ == "__main__":
    unittest.main()
