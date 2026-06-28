from flask import Blueprint, render_template, request

from app.services.text_diff import compare_texts

bp = Blueprint("text_diff", __name__, url_prefix="/tools/text-diff")


@bp.route("", methods=("GET", "POST"))
def index():
    form = {"left_text": "", "right_text": ""}
    result = None

    if request.method == "POST":
        form.update(
            {
                "left_text": request.form.get("left_text", ""),
                "right_text": request.form.get("right_text", ""),
            }
        )
        result = compare_texts(form["left_text"], form["right_text"], _merge_choices(request.form))

    return render_template("tools/text-diff.html", form=form, result=result)


def _merge_choices(form_data):
    choices = {}
    for key, value in form_data.items():
        if key.startswith("merge_") and value in {"left", "right"}:
            try:
                choices[int(key.removeprefix("merge_"))] = value
            except ValueError:
                pass
    return choices
