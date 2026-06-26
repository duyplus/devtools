from flask import Blueprint, render_template, request

from app.services.comma_delimiter import DelimiterOptions, convert_text

bp = Blueprint("comma_delimiter", __name__, url_prefix="/tools/comma-delimiter")


@bp.route("", methods=("GET", "POST"))
def index():
    result = ""
    error = ""
    form = {
        "text": "",
        "input_delimiter": "newline",
        "input_custom": "",
        "output_delimiter": "comma",
        "output_custom": "",
        "quote": "none",
        "prefix": "",
        "suffix": "",
        "interval": "",
        "trim": "on",
        "remove_blank": "on",
        "dedupe": "",
        "direction": "forward",
    }

    if request.method == "POST":
        form.update(request.form.to_dict())
        source_text = request.form.get("text", "")
        direction = request.form.get("direction", "forward")
        input_delimiter = request.form.get("input_delimiter", "newline")
        output_delimiter = request.form.get("output_delimiter", "comma")
        input_custom = request.form.get("input_custom", "")
        output_custom = request.form.get("output_custom", "")

        if direction == "reverse":
            input_delimiter, output_delimiter = output_delimiter, input_delimiter
            input_custom, output_custom = output_custom, input_custom

        try:
            interval_raw = request.form.get("interval", "").strip()
            options = DelimiterOptions(
                input_delimiter=input_delimiter,
                input_custom=input_custom,
                output_delimiter=output_delimiter,
                output_custom=output_custom,
                trim=bool(request.form.get("trim")),
                remove_blank=bool(request.form.get("remove_blank")),
                dedupe=bool(request.form.get("dedupe")),
                quote=request.form.get("quote", "none"),
                prefix=request.form.get("prefix", ""),
                suffix=request.form.get("suffix", ""),
                interval=int(interval_raw) if interval_raw else 0,
            )
            result = convert_text(source_text, options)
        except ValueError as exc:
            error = str(exc)

    return render_template("tools/comma-delimiter.html", form=form, result=result, error=error)
