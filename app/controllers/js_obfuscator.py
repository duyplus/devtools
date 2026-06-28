from flask import Blueprint, g, jsonify, render_template, request

from app.i18n import translate_error
from app.services.js_obfuscator import (
    DEFAULT_OPTIONS,
    JavascriptToolError,
    deobfuscate_javascript,
    obfuscate_javascript,
)

bp = Blueprint("js_obfuscator", __name__, url_prefix="/tools/js-obfuscator")


@bp.route("", methods=("GET", "POST"))
def index():
    error = ""
    result = ""
    form = {
        "text": "",
        "mode": "obfuscate",
        **DEFAULT_OPTIONS,
    }

    if request.method == "POST":
        form.update(_form_options(request.form))
        result, error = _convert(form)

    return render_template("tools/js-obfuscator.html", form=form, result=result, error=error)


@bp.post("/convert")
def convert():
    result, error = _convert(_form_options(request.form))
    return jsonify({"result": result, "error": error})


def _convert(form):
    text = form.get("text", "")
    mode = form.get("mode", "obfuscate")

    try:
        if mode == "deobfuscate":
            return deobfuscate_javascript(text), ""
        if mode == "obfuscate":
            return obfuscate_javascript(text, form), ""
        raise JavascriptToolError("javascript.error.mode")
    except JavascriptToolError as exc:
        return "", translate_error(g.lang, exc)


def _form_options(form_data):
    return {
        "text": form_data.get("text", ""),
        "mode": form_data.get("mode", "obfuscate"),
        "compact": "compact" in form_data,
        "string_array": "string_array" in form_data,
        "debug_protection": "debug_protection" in form_data,
        "numbers_to_expressions": "numbers_to_expressions" in form_data,
        "control_flow_flattening": "control_flow_flattening" in form_data,
        "self_defending": "self_defending" in form_data,
        "simplify": "simplify" in form_data,
        "split_strings": "split_strings" in form_data,
        "string_array_threshold": form_data.get("string_array_threshold", DEFAULT_OPTIONS["string_array_threshold"]),
        "control_flow_threshold": form_data.get("control_flow_threshold", DEFAULT_OPTIONS["control_flow_threshold"]),
        "split_strings_chunk_length": form_data.get(
            "split_strings_chunk_length",
            DEFAULT_OPTIONS["split_strings_chunk_length"],
        ),
        "string_array_encoding": form_data.get(
            "string_array_encoding",
            DEFAULT_OPTIONS["string_array_encoding"],
        ),
    }
