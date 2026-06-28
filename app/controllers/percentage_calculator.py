from flask import Blueprint, g, render_template, request

from app.i18n import translate_error
from app.services.percentage_calculator import PercentageError, calculate_percentage

bp = Blueprint("percentage_calculator", __name__, url_prefix="/tools/percentage-calculator")


@bp.route("", methods=("GET", "POST"))
def index():
    result = ""
    error = ""
    form = {
        "mode": "of",
        "percent": "",
        "value": "",
        "base": "",
        "direction": "increase",
    }

    if request.method == "POST":
        form.update(request.form.to_dict())
        try:
            result = calculate_percentage(form)
        except PercentageError as exc:
            error = translate_error(g.lang, exc)

    return render_template("tools/percentage-calculator.html", form=form, result=result, error=error)
