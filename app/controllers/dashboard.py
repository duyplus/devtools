from flask import Blueprint, render_template

from app.tools.registry import TOOLS

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def index():
    return render_template("dashboard.html", tools=TOOLS)


@bp.get("/healthz")
def healthz():
    return "OK"
