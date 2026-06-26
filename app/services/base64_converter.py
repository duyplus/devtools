import base64
import binascii


class Base64Error(ValueError):
    pass


def encode_base64(text):
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def decode_base64(text):
    try:
        decoded = base64.b64decode(text.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise Base64Error("Input is not valid Base64.") from exc

    try:
        return decoded.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Base64Error("Decoded data is not valid UTF-8 text.") from exc
