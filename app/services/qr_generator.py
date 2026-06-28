from dataclasses import dataclass
from html import escape
from io import BytesIO
from pathlib import Path
from urllib.parse import quote
import warnings

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q

FRAME_FONT_FAMILY = "Quicksand, Arial, sans-serif"
FRAME_FONT_PATH = Path(__file__).resolve().parents[1] / "static" / "fonts" / "Quicksand.ttf"
MAX_LOGO_PIXELS = 4_000_000
Image.MAX_IMAGE_PIXELS = MAX_LOGO_PIXELS


class QRError(ValueError):
    def __init__(self, key):
        self.key = key
        super().__init__(key)


@dataclass(frozen=True)
class QROptions:
    size: int = 320
    foreground: str = "#111827ff"
    background: str = "#ffffffff"
    margin: int = 2
    error_correction: str = "M"
    frame_text_enabled: bool = False
    frame_text: str = ""


def build_qr_payload(form):
    qr_type = form.get("type", "url")
    if qr_type == "url":
        url = _required(form.get("url"), "qr.error.url_required")
        if "://" not in url:
            url = f"https://{url}"
        return url
    if qr_type == "text":
        return _required(form.get("text"), "qr.error.text_required")
    if qr_type == "email":
        address = _required(form.get("email_address"), "qr.error.email_required")
        subject = quote((form.get("email_subject") or "").strip())
        body = quote((form.get("email_body") or "").strip())
        query = "&".join(part for part in (f"subject={subject}" if subject else "", f"body={body}" if body else "") if part)
        return f"mailto:{address}{'?' + query if query else ''}"
    if qr_type == "phone":
        return f"tel:{_required(form.get('phone'), 'qr.error.phone_required')}"
    if qr_type == "sms":
        phone = _required(form.get("sms_phone"), "qr.error.phone_required")
        message = quote((form.get("sms_message") or "").strip())
        return f"SMSTO:{phone}:{message}"
    if qr_type == "wifi":
        ssid = _required(form.get("wifi_ssid"), "qr.error.wifi_required")
        password = form.get("wifi_password") or ""
        auth = form.get("wifi_auth") or ("nopass" if not password else "WPA")
        hidden = "true" if form.get("wifi_hidden") else "false"
        return f"WIFI:T:{auth};S:{_wifi_escape(ssid)};P:{_wifi_escape(password)};H:{hidden};;"
    if qr_type == "vcard":
        name = _required(form.get("vcard_name"), "qr.error.name_required")
        return "\n".join(
            line
            for line in (
                "BEGIN:VCARD",
                "VERSION:3.0",
                f"N:{name}",
                f"FN:{name}",
                _optional("ORG", form.get("vcard_org")),
                _optional("TEL", form.get("vcard_phone")),
                _optional("EMAIL", form.get("vcard_email")),
                _optional("URL", form.get("vcard_url")),
                "END:VCARD",
            )
            if line
        )
    if qr_type == "location":
        lat = _required(form.get("latitude"), "qr.error.latitude_required")
        lng = _required(form.get("longitude"), "qr.error.longitude_required")
        return f"geo:{lat},{lng}"
    if qr_type == "event":
        title = _required(form.get("event_title"), "qr.error.event_title_required")
        start = _required(form.get("event_start"), "qr.error.event_start_required")
        return "\n".join(
            line
            for line in (
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "BEGIN:VEVENT",
                f"SUMMARY:{title}",
                f"DTSTART:{_ical_time(start)}",
                _optional("DTEND", _ical_time(form.get("event_end"))),
                _optional("LOCATION", form.get("event_location")),
                _optional("DESCRIPTION", form.get("event_description")),
                "END:VEVENT",
                "END:VCALENDAR",
            )
            if line
        )
    raise QRError("qr.error.unsupported_type")


def generate_qr_outputs(payload, options=None, logo_bytes=None):
    options = options or QROptions()
    payload = _required(payload, "qr.error.content_required")
    size = _clamp_int(options.size, 100, 550)
    margin = _clamp_int(options.margin, 0, 12)
    foreground = _hex_color(options.foreground)
    background = _hex_color(options.background)
    qr = qrcode.QRCode(
        error_correction=_error_correction(options.error_correction),
        border=margin,
        box_size=10,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color=_pil_color(foreground), back_color=_pil_color(background)).convert("RGBA")
    image = image.resize((size, size), Image.Resampling.NEAREST)
    if logo_bytes:
        image = _add_logo(image, logo_bytes)
    if options.frame_text_enabled and options.frame_text.strip():
        image = _add_frame_text(image, options.frame_text.strip(), foreground, background)
    return {
        "png": _save_image(image, "PNG"),
        "jpg": _save_image(image.convert("RGB"), "JPEG"),
        "svg": _qr_svg(qr, size, foreground, background, logo_bytes, options.frame_text if options.frame_text_enabled else ""),
    }

def generate_qr_png(payload, options=None, logo_bytes=None):
    return BytesIO(generate_qr_outputs(payload, options, logo_bytes)["png"])

def _save_image(image, image_format):
    output = BytesIO()
    image.save(output, format=image_format)
    return output.getvalue()

def _qr_svg(qr, size, foreground, background, logo_bytes=None, frame_text=""):
    matrix = qr.get_matrix()
    dimension = len(matrix)
    frame_text = frame_text.strip()
    padding = max(1, dimension / 24) if frame_text else 0
    frame_height = max(2, dimension / 12) if frame_text else 0
    view_width = dimension + padding * 2
    view_height = dimension + padding * 2 + frame_height
    output_width = int(round(size * view_width / dimension))
    output_height = int(round(size * view_height / dimension))
    rects = [
        f'<rect x="{x}" y="{y}" width="1" height="1"/>'
        for y, row in enumerate(matrix)
        for x, value in enumerate(row)
        if value
    ]
    logo = ""
    if logo_bytes:
        logo_size = dimension / 4
        logo_pos = padding + (dimension - logo_size) / 2
        logo_data = _logo_png_data(logo_bytes)
        logo = (
            f'<image href="data:image/png;base64,{logo_data}" x="{logo_pos}" y="{logo_pos}" '
            f'width="{logo_size}" height="{logo_size}" preserveAspectRatio="xMidYMid meet"/>'
        )
    frame = ""
    if frame_text:
        frame = (
            f'<text x="{view_width / 2}" y="{padding + dimension + frame_height / 2}" text-anchor="middle" '
            f'dominant-baseline="middle" font-family="{FRAME_FONT_FAMILY}" font-size="{dimension / 24}" font-weight="700" '
            f'{_svg_fill(foreground)}>{escape(frame_text)}</text>'
            f'<rect x="{padding}" y="{padding}" width="{dimension}" height="{dimension}" '
            f'fill="none" {_svg_stroke(foreground)} stroke-width="{max(0.2, dimension / 160)}"/>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{output_width}" height="{output_height}" viewBox="0 0 {view_width} {view_height}">'
        f'<rect width="{view_width}" height="{view_height}" {_svg_fill(background)}/>'
        f'<rect x="{padding}" y="{padding}" width="{dimension}" height="{dimension}" {_svg_fill(background)}/>'
        f'<g transform="translate({padding} {padding})" {_svg_fill(foreground)}>{"".join(rects)}</g>{logo}{frame}</svg>'
    ).encode("utf-8")


def _add_logo(image, logo_bytes):
    logo = _open_logo(logo_bytes)
    max_size = image.size[0] // 4
    logo.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    logo = _white_backed_if_transparent(logo)
    x = (image.size[0] - logo.size[0]) // 2
    y = (image.size[1] - logo.size[1]) // 2
    image.alpha_composite(logo, (x, y))
    return image

def _logo_png_data(logo_bytes):
    logo = _white_backed_if_transparent(_open_logo(logo_bytes))
    output = BytesIO()
    logo.save(output, format="PNG")
    return __import__("base64").b64encode(output.getvalue()).decode("ascii")

def _open_logo(logo_bytes):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            logo = Image.open(BytesIO(logo_bytes))
            logo.load()
        return logo.convert("RGBA")
    except (
        OSError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise QRError("qr.error.logo_invalid") from exc

def _white_backed_if_transparent(logo):
    if logo.getchannel("A").getextrema()[0] == 255:
        return logo
    background = Image.new("RGBA", logo.size, (255, 255, 255, 255))
    background.alpha_composite(logo)
    return background

def _add_frame_text(image, text, foreground, background):
    padding = max(12, image.size[0] // 24)
    frame_height = max(32, image.size[1] // 12)
    framed = Image.new("RGBA", (image.size[0] + padding * 2, image.size[1] + padding * 2 + frame_height), _pil_color(background))
    framed.alpha_composite(image, (padding, padding))
    draw = ImageDraw.Draw(framed)
    font = _frame_font(max(10, image.size[0] // 24))
    box = draw.textbbox((0, 0), text, font=font)
    x = (framed.size[0] - (box[2] - box[0])) // 2
    y = padding + image.size[1] + (frame_height - (box[3] - box[1])) // 2
    draw.text((x, y), text, fill=_pil_color(foreground), font=font)
    border = max(2, image.size[0] // 160)
    draw.rectangle((padding, padding, padding + image.size[0] - 1, padding + image.size[1] - 1), outline=_pil_color(foreground), width=border)
    return framed

def _frame_font(size):
    try:
        return ImageFont.truetype(str(FRAME_FONT_PATH), size)
    except OSError:
        return ImageFont.load_default()


def _required(value, key):
    value = (value or "").strip()
    if not value:
        raise QRError(key)
    return value


def _optional(name, value):
    value = (value or "").strip()
    return f"{name}:{value}" if value else ""


def _wifi_escape(value):
    return str(value).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace(":", "\\:")


def _ical_time(value):
    value = (value or "").strip()
    value = value.replace("-", "").replace(":", "").replace("T", "T")
    return f"{value}00" if "T" in value and len(value.rsplit("T", 1)[1]) == 4 else value


def _hex_color(value):
    value = (value or "").strip()
    if len(value) == 4 and value.startswith("#"):
        value = "#" + "".join(char * 2 for char in value[1:]) + "ff"
    if len(value) == 7 and value.startswith("#"):
        value = f"{value}ff"
    if len(value) == 9 and value.startswith("#") and all(char in "0123456789abcdefABCDEF" for char in value[1:]):
        return value.upper()
    raise QRError("qr.error.color_invalid")

def _pil_color(value):
    value = _hex_color(value)
    return tuple(int(value[index:index + 2], 16) for index in (1, 3, 5, 7))

def _svg_fill(value):
    value = _hex_color(value)
    opacity = int(value[7:9], 16) / 255
    opacity_attr = f' fill-opacity="{opacity:.3f}"' if opacity < 1 else ""
    return f'fill="{escape(value[:7])}"{opacity_attr}'

def _svg_stroke(value):
    value = _hex_color(value)
    opacity = int(value[7:9], 16) / 255
    opacity_attr = f' stroke-opacity="{opacity:.3f}"' if opacity < 1 else ""
    return f'stroke="{escape(value[:7])}"{opacity_attr}'

def _error_correction(value):
    levels = {
        "L": ERROR_CORRECT_L,
        "M": ERROR_CORRECT_M,
        "Q": ERROR_CORRECT_Q,
        "H": ERROR_CORRECT_H,
    }
    try:
        return levels[(value or "M").upper()]
    except KeyError as exc:
        raise QRError("qr.error.correction_invalid") from exc


def _clamp_int(value, minimum, maximum):
    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise QRError("qr.error.size_invalid") from exc
    return min(maximum, max(minimum, value))
