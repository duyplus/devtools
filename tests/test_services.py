from io import BytesIO
import unittest
import zipfile

from PIL import Image

from app import create_app
from app.services.base64_converter import Base64Error, decode_base64, encode_base64
from app.services.comma_delimiter import DelimiterOptions, convert_text
from app.services.icon_converter import IconError, generate_favicon_pack, generate_ico
from app.services.js_obfuscator import deobfuscate_javascript, obfuscate_javascript
from app.services.password_generator import PasswordError, PasswordOptions, generate_passwords
from app.services.percentage_calculator import PercentageError, calculate_percentage
from app.services.qr_generator import QRError, QROptions, build_qr_payload, generate_qr_outputs, generate_qr_png
from app.services.text_diff import compare_texts
from app.tools.registry import TOOLS


class DelimiterServiceTests(unittest.TestCase):
    def test_convert_dedupes_and_quotes(self):
        result = convert_text(
            "a\n b\n a\n",
            DelimiterOptions(dedupe=True, quote="single", output_delimiter="comma"),
        )
        self.assertEqual(result, "'a','b'")

    def test_custom_delimiter_and_interval(self):
        result = convert_text(
            "a||b||c||d",
            DelimiterOptions(
                input_delimiter="custom",
                input_custom="||",
                output_delimiter="pipe",
                interval=2,
            ),
        )
        self.assertEqual(result, "a|b\nc|d")


class Base64ServiceTests(unittest.TestCase):
    def test_encode_and_decode_utf8_text(self):
        encoded = encode_base64("Xin chào")
        self.assertEqual(encoded, "WGluIGNow6Bv")
        self.assertEqual(decode_base64(encoded), "Xin chào")

    def test_decode_rejects_invalid_base64(self):
        with self.assertRaises(Base64Error):
            decode_base64("not base64!")


class TextDiffServiceTests(unittest.TestCase):
    def test_compare_texts_counts_and_merges(self):
        result = compare_texts("a\nb\nc\n", "a\nB\nc\nd\n")
        self.assertEqual(result.modified, 1)
        self.assertEqual(result.added, 2)
        self.assertEqual(result.deleted, 1)
        self.assertEqual(result.left_lines, 3)
        self.assertEqual(result.right_lines, 4)
        self.assertEqual(result.merged_text, "a\nB\nc\nd\n")

    def test_compare_texts_keeps_left_choice(self):
        result = compare_texts("a\nb\n", "a\nB\n", {1: "left"})
        self.assertEqual(result.merged_text, "a\nb\n")

    def test_compare_texts_does_not_color_equal_lines_inside_replace(self):
        result = compare_texts("A\r\nB\r\nC\r\n", "A\nB")
        lines = [line for hunk in result.hunks for line in hunk.lines]
        self.assertEqual(
            [(line.left_no, line.right_no, line.kind) for line in lines],
            [(1, 1, "equal"), (2, 2, "equal"), (3, None, "deleted")],
        )
        self.assertEqual(result.added, 0)
        self.assertEqual(result.deleted, 1)


class JavascriptToolServiceTests(unittest.TestCase):
    def test_obfuscate_and_deobfuscate_round_trip(self):
        source = "console.log('Xin chào');"
        obfuscated = obfuscate_javascript(source)
        self.assertIn("TextDecoder", obfuscated)
        self.assertEqual(deobfuscate_javascript(obfuscated), source)

    def test_deobfuscate_eval_atob(self):
        self.assertEqual(deobfuscate_javascript('eval(atob("Y29uc29sZS5sb2coMSk7"))'), "console.log(1);")

    def test_deobfuscate_js_escapes(self):
        self.assertEqual(deobfuscate_javascript(r"\x63\x6f\x6e\x73\x6f\x6c\x65.log(1);"), "console.log(1);")

    def test_deobfuscate_option_outputs(self):
        source = "console.log('options');"
        for encoding in ("none", "base64", "rc4"):
            obfuscated = obfuscate_javascript(
                source,
                {
                    "string_array_encoding": encoding,
                    "split_strings": True,
                    "split_strings_chunk_length": "8",
                    "control_flow_flattening": True,
                    "numbers_to_expressions": True,
                },
            )
            self.assertEqual(deobfuscate_javascript(obfuscated), source)


class PercentageServiceTests(unittest.TestCase):
    def test_modes(self):
        self.assertEqual(calculate_percentage({"mode": "of", "percent": "20", "value": "80"}), "16")
        self.assertEqual(
            calculate_percentage({"mode": "ratio", "value": "20", "base": "80"}),
            "25%",
        )
        self.assertEqual(
            calculate_percentage(
                {"mode": "change", "percent": "10", "value": "50", "direction": "increase"}
            ),
            "55",
        )
        self.assertEqual(calculate_percentage({"mode": "total", "percent": "25", "value": "20"}), "80")

    def test_zero_division_is_validation_error(self):
        with self.assertRaises(PercentageError):
            calculate_percentage({"mode": "ratio", "value": "1", "base": "0"})


class PasswordServiceTests(unittest.TestCase):
    def test_generate_passwords_honors_options(self):
        result = generate_passwords(
            PasswordOptions(length=12, count=3, lowercase=False, uppercase=True, digits=True, symbols=False)
        )
        self.assertEqual(len(result), 3)
        for password in result:
            self.assertEqual(len(password), 12)
            self.assertRegex(password, r"[A-Z]")
            self.assertRegex(password, r"[0-9]")
            self.assertNotRegex(password, r"[a-z!@#$%^&*]")

    def test_rejects_no_character_types(self):
        with self.assertRaises(PasswordError):
            generate_passwords(PasswordOptions(lowercase=False, uppercase=False, digits=False, symbols=False))

class QRServiceTests(unittest.TestCase):
    def test_builds_wifi_payload(self):
        payload = build_qr_payload({"type": "wifi", "wifi_ssid": "Cafe", "wifi_password": "secret"})
        self.assertEqual(payload, "WIFI:T:WPA;S:Cafe;P:secret;H:false;;")

    def test_generate_qr_png(self):
        output = generate_qr_png("https://example.com", QROptions(size=256))
        with Image.open(output) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (256, 256))

    def test_generate_qr_size_limits(self):
        with Image.open(generate_qr_png("https://example.com", QROptions(size=50))) as image:
            self.assertEqual(image.size, (100, 100))
        with Image.open(generate_qr_png("https://example.com", QROptions(size=1200))) as image:
            self.assertEqual(image.size, (550, 550))

    def test_generate_qr_outputs(self):
        output = generate_qr_outputs("https://example.com", QROptions(size=256))
        self.assertEqual(set(output), {"png", "jpg", "svg"})
        self.assertTrue(output["svg"].startswith(b"<svg"))

    def test_generate_qr_with_frame_text_options(self):
        output = generate_qr_outputs(
            "https://example.com",
            QROptions(size=200, foreground="#000000FF", background="#FFFFFFFF", margin=4, error_correction="M", frame_text_enabled=True, frame_text="Scan me"),
        )
        with Image.open(BytesIO(output["png"])) as image:
            self.assertGreater(image.height, image.width)
            pad = (image.width - 200) // 2
            self.assertEqual(image.convert("RGB").getpixel((0, 0)), (255, 255, 255))
            self.assertEqual(image.convert("RGB").getpixel((pad, pad)), (0, 0, 0))
            self.assertEqual(image.convert("RGB").getpixel((0, image.height - 1)), (255, 255, 255))
        self.assertIn(b"Scan me", output["svg"])
        self.assertIn(b"Quicksand", output["svg"])
        self.assertIn(b'font-weight="700"', output["svg"])
        self.assertIn(b'stroke="#000000"', output["svg"])

    def test_transparent_logo_gets_white_background(self):
        logo = BytesIO()
        Image.new("RGBA", (40, 40), (0, 0, 0, 0)).save(logo, format="PNG")
        output = generate_qr_png("https://example.com", QROptions(size=200), logo.getvalue())
        with Image.open(output) as image:
            self.assertEqual(image.convert("RGB").getpixel((100, 100)), (255, 255, 255))

    def test_rejects_logo_decompression_bomb(self):
        from app.services import qr_generator

        old_limit = Image.MAX_IMAGE_PIXELS
        try:
            Image.MAX_IMAGE_PIXELS = 1
            logo = BytesIO()
            Image.new("RGBA", (2, 2), (0, 0, 0, 255)).save(logo, format="PNG")
            with self.assertRaises(QRError):
                generate_qr_png("https://example.com", QROptions(size=200), logo.getvalue())
        finally:
            Image.MAX_IMAGE_PIXELS = old_limit
            qr_generator.Image.MAX_IMAGE_PIXELS = old_limit

class IconServiceTests(unittest.TestCase):
    def _png(self):
        output = BytesIO()
        Image.new("RGBA", (300, 180), (40, 120, 200, 255)).save(output, format="PNG")
        return output.getvalue()

    def test_generate_favicon_pack(self):
        output = generate_favicon_pack(self._png())
        with zipfile.ZipFile(output) as archive:
            names = set(archive.namelist())
        self.assertIn("favicon.ico", names)
        self.assertIn("apple-icon-180x180.png", names)
        self.assertIn("manifest.json", names)
        self.assertIn("browserconfig.xml", names)

    def test_generate_ico(self):
        output = generate_ico(self._png(), [16, 32, 48], "32")
        with Image.open(output) as image:
            self.assertEqual(image.format, "ICO")
            self.assertEqual(image.size, (48, 48))
            self.assertEqual(image.ico.sizes(), {(16, 16), (32, 32), (48, 48)})

    def test_generate_ico_rejects_256_for_8_bit(self):
        with self.assertRaises(IconError):
            generate_ico(self._png(), [256], "8")

    def test_rejects_icon_decompression_bomb(self):
        from app.services import icon_converter

        old_limit = Image.MAX_IMAGE_PIXELS
        try:
            Image.MAX_IMAGE_PIXELS = 1
            with self.assertRaises(IconError):
                generate_ico(self._png(), [16], "32")
        finally:
            Image.MAX_IMAGE_PIXELS = old_limit
            icon_converter.Image.MAX_IMAGE_PIXELS = old_limit


class RegistryTests(unittest.TestCase):
    def test_registry_endpoints_resolve(self):
        app = create_app({"TESTING": True})
        with app.test_request_context():
            for tool in TOOLS:
                self.assertTrue(app.url_for(tool.endpoint).startswith("/"))


if __name__ == "__main__":
    unittest.main()
