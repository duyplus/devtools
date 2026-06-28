import base64

from flask import Blueprint, g, render_template, request

from app.i18n import translate, translate_error
from app.services.qr_generator import QRError, QROptions, build_qr_payload, generate_qr_outputs


bp = Blueprint("qr_generator", __name__, url_prefix="/tools/qr-generator")

QR_TYPES = ("url", "text", "email", "phone", "sms", "wifi", "vcard", "location", "event")


@bp.route("", methods=("GET", "POST"))
def index():
    error = ""
    result = {}
    form = _default_form()
    if request.method == "POST":
        form.update(request.form.to_dict())
        form["wifi_hidden"] = "wifi_hidden" in request.form
        try:
            payload = build_qr_payload(form)
            logo = request.files.get("logo")
            logo_bytes = logo.read() if logo and logo.filename else None
            outputs = generate_qr_outputs(
                payload,
                QROptions(
                    size=form.get("size", 320),
                    foreground=form.get("foreground", "#111827ff"),
                    background=form.get("background", "#ffffffff"),
                    margin=form.get("margin", 2),
                    error_correction=form.get("error_correction", "M"),
                    frame_text_enabled="frame_text_enabled" in request.form,
                    frame_text=form.get("frame_text", ""),
                ),
                logo_bytes,
            )
            result = {name: base64.b64encode(content).decode("ascii") for name, content in outputs.items()}
        except QRError as exc:
            error = translate_error(g.lang, exc)
    return render_template("tools/qr-generator.html", error=error, result=result, form=form, qr_types=QR_TYPES)


def _default_form():
    return {
        "type": "url",
        "url": "",
        "text": "",
        "email_address": "",
        "email_subject": "",
        "email_body": "",
        "phone": "",
        "sms_phone": "",
        "sms_message": "",
        "wifi_ssid": "",
        "wifi_password": "",
        "wifi_auth": "WPA",
        "wifi_hidden": False,
        "vcard_name": "",
        "vcard_org": "",
        "vcard_phone": "",
        "vcard_email": "",
        "vcard_url": "",
        "latitude": "",
        "longitude": "",
        "event_title": "",
        "event_start": "",
        "event_end": "",
        "event_location": "",
        "event_description": "",
        "size": "300",
        "foreground": "#000000FF",
        "background": "#FFFFFFFF",
        "margin": "2",
        "error_correction": "M",
        "frame_text_enabled": False,
        "frame_text": translate(g.lang, "qr.placeholder.frame_text"),
    }
