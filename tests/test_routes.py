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
            "/tools/percentage-calculator",
            "/tools/base64-converter",
            "/tools/js-obfuscator",
            "/tools/password-generator",
            "/healthz",
        ):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)

    def test_delimiter_post(self):
        response = self.client.get("/tools/comma-delimiter")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data-delimiter-tool", response.data)
        self.assertIn(b"data-delimiter-error", response.data)

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

        response = self.client.post(
            "/tools/password-generator",
            data={
                "length": "16",
                "count": "2",
                "uppercase": "on",
                "lowercase": "on",
                "digits": "on",
                "symbols": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data-password-tool", response.data)

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

    def test_icon_invalid_upload(self):
        response = self.client.post(
            "/tools/icon-converter",
            data={"mode": "ico", "sizes": ["16"], "image": (BytesIO(b"bad"), "bad.txt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Unsupported or corrupt image file", response.data)

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
