from flask import Blueprint, g, render_template, request

from app.i18n import translate_error
from app.services.password_generator import PasswordError, PasswordOptions, generate_passwords


bp = Blueprint("password_generator", __name__, url_prefix="/tools/password-generator")


@bp.route("", methods=("GET", "POST"))
def index():
    error = ""
    result = []
    form = {
        "length": "16",
        "count": "1",
        "lowercase": True,
        "uppercase": True,
        "digits": True,
        "symbols": True,
    }

    if request.method == "POST":
        form.update(_form_options(request.form))
        try:
            result = generate_passwords(PasswordOptions(**form))
        except PasswordError as exc:
            error = translate_error(g.lang, exc)

    return render_template("tools/password-generator.html", form=form, result=result, error=error)


def _form_options(form_data):
    return {
        "length": form_data.get("length", "16"),
        "count": form_data.get("count", "1"),
        "lowercase": "lowercase" in form_data,
        "uppercase": "uppercase" in form_data,
        "digits": "digits" in form_data,
        "symbols": "symbols" in form_data,
    }
