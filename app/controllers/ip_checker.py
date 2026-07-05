from flask import Blueprint, current_app, g, render_template, request

from app.i18n import translate_error
from app.services.ip_checker import IpCheckError, check_ip_target, get_client_ip, lookup_public_ips

bp = Blueprint("ip_checker", __name__, url_prefix="/tools/ip-checker")


@bp.route("", methods=("GET", "POST"))
def index():
    error = ""
    public_ips = lookup_public_ips() if not current_app.config["TESTING"] else {"ipv4": "", "ipv6": ""}
    client_ip = public_ips["ipv6"] or public_ips["ipv4"] or get_client_ip(request)
    submitted = request.method == "POST" and bool(request.form.get("target", "").strip())
    target = request.form.get("target", "").strip() if submitted else client_ip
    result = None

    try:
        lookup_target = public_ips["ipv4"] if not submitted and public_ips["ipv4"] else target or client_ip
        result = check_ip_target(lookup_target, include_geo=not current_app.config["TESTING"])
        display_public_ips = public_ips if not submitted or result["ip"] in public_ips.values() else {}
        _add_display_ips(result, display_public_ips)
    except IpCheckError as exc:
        error = translate_error(g.lang, exc)

    return render_template(
        "tools/ip-checker.html",
        client_ip=client_ip,
        error=error,
        result=result,
        user_agent=request.headers.get("User-Agent", ""),
    )


def _add_display_ips(result, public_ips):
    result["display_ipv4"] = (
        result.get("ipv4")
        or public_ips.get("ipv4")
        or (result["ip"] if result["version"] == "IPv4" else "")
    )
    result["display_ipv6"] = (
        public_ips.get("ipv6")
        or result.get("ipv6")
        or (result["ip"] if result["version"] == "IPv6" else "")
    )
