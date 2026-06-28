from flask import Blueprint, g, render_template, request, send_file

from app.i18n import translate_error
from app.services.icon_converter import IconError, generate_favicon_pack, generate_ico

bp = Blueprint("icon_converter", __name__, url_prefix="/tools/icon-converter")

DEFAULT_SIZES = [16, 32, 48]
ALL_SIZES = [16, 32, 48, 64, 128, 256]


@bp.route("", methods=("GET", "POST"))
def index():
    error = ""
    form = {
        "mode": "pack",
        "bit_depth": "32",
        "sizes": DEFAULT_SIZES,
        "keep_ratio": False,
    }

    if request.method == "POST":
        form["mode"] = request.form.get("mode", "pack")
        form["bit_depth"] = request.form.get("bit_depth", "32")
        form["sizes"] = [int(size) for size in request.form.getlist("sizes") if size.isdigit()]
        form["keep_ratio"] = request.form.get("keep_ratio") == "1"

        try:
            upload = request.files.get("image")
            if upload is None or upload.filename == "":
                raise IconError("icons.error.file_required")

            image_bytes = upload.read()
            if form["mode"] == "ico":
                output = generate_ico(image_bytes, form["sizes"], form["bit_depth"])
                return send_file(
                    output,
                    mimetype="image/x-icon",
                    as_attachment=True,
                    download_name="icon.ico",
                )

            output = generate_favicon_pack(image_bytes, keep_ratio=form["keep_ratio"])
            return send_file(
                output,
                mimetype="application/zip",
                as_attachment=True,
                download_name="favicon-pack.zip",
            )
        except (IconError, ValueError) as exc:
            error = translate_error(g.lang, exc)

    return render_template(
        "tools/icon-converter.html",
        error=error,
        form=form,
        all_sizes=ALL_SIZES,
    )
