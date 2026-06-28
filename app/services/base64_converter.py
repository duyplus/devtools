import base64
import binascii


class Base64Error(ValueError):
    def __init__(self, key):
        self.key = key
        self.params = {}
        super().__init__(key)


def encode_base64(text):
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def decode_base64(text):
    try:
        decoded = base64.b64decode(text.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise Base64Error("base64.error.invalid") from exc

    try:
        return decoded.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Base64Error("base64.error.invalid_utf8") from exc
