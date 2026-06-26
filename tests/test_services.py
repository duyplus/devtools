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
            PasswordOptions(length=12, count=3, uppercase=True, lowercase=False, digits=True, symbols=False)
        )
        self.assertEqual(len(result), 3)
        for password in result:
            self.assertEqual(len(password), 12)
            self.assertRegex(password, r"[A-Z]")
            self.assertRegex(password, r"[0-9]")
            self.assertNotRegex(password, r"[a-z!@#$%^&*]")

    def test_rejects_no_character_types(self):
        with self.assertRaises(PasswordError):
            generate_passwords(PasswordOptions(uppercase=False, lowercase=False, digits=False, symbols=False))

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


class RegistryTests(unittest.TestCase):
    def test_registry_endpoints_resolve(self):
        app = create_app({"TESTING": True})
        with app.test_request_context():
            for tool in TOOLS:
                self.assertTrue(app.url_for(tool.endpoint).startswith("/"))


if __name__ == "__main__":
    unittest.main()
