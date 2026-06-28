from flask import Blueprint, g, render_template, request

from app.i18n import translate_error
from app.services.base64_converter import Base64Error, decode_base64, encode_base64

bp = Blueprint("base64_converter", __name__, url_prefix="/tools/base64-converter")


@bp.route("", methods=("GET", "POST"))
def index():
    error = ""
    result = ""
    form = {
        "text": "",
        "mode": "encode",
    }

    if request.method == "POST":
        form.update(request.form.to_dict())
        text = request.form.get("text", "")
        mode = request.form.get("mode", "encode")

        try:
            if mode == "decode":
                result = decode_base64(text)
            elif mode == "encode":
                result = encode_base64(text)
            else:
                raise Base64Error("base64.error.mode")
        except Base64Error as exc:
            error = translate_error(g.lang, exc)

    return render_template("tools/base64-converter.html", form=form, result=result, error=error)
