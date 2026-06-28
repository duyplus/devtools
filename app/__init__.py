import os
import re
import secrets
from pathlib import Path

from flask import Flask, g, request, url_for
from werkzeug.exceptions import RequestEntityTooLarge

from app.i18n import LANGUAGES, normalize_language, translate


HTML_COMMENT_RE = re.compile(r"<!--(?!\[if).*?-->", re.DOTALL)
INTER_TAG_WHITESPACE_RE = re.compile(r">\s+<")


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        MAX_CONTENT_LENGTH=8 * 1024 * 1024,
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MINIFY_ASSETS=os.environ.get("MINIFY_ASSETS", "0").lower() in {"1", "true", "yes"},
        MINIFY_HTML=os.environ.get("MINIFY_HTML", "0").lower() in {"1", "true", "yes"},
    )

    if test_config:
        app.config.update(test_config)

    from app.controllers.dashboard import bp as dashboard_bp
    from app.controllers.base64_converter import bp as base64_bp
    from app.controllers.comma_delimiter import bp as delimiter_bp
    from app.controllers.icon_converter import bp as icons_bp
    from app.controllers.js_obfuscator import bp as javascript_bp
    from app.controllers.password_generator import bp as password_bp
    from app.controllers.percentage_calculator import bp as percentage_bp
    from app.controllers.qr_generator import bp as qr_bp
    from app.controllers.text_diff import bp as text_diff_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(icons_bp)
    app.register_blueprint(delimiter_bp)
    app.register_blueprint(text_diff_bp)
    app.register_blueprint(percentage_bp)
    app.register_blueprint(base64_bp)
    app.register_blueprint(javascript_bp)
    app.register_blueprint(password_bp)
    app.register_blueprint(qr_bp)

    @app.before_request
    def load_language():
        requested = request.args.get("lang") or request.cookies.get("devtools_lang")
        g.lang = normalize_language(requested)

    @app.after_request
    def remember_language(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        if request.args.get("lang") in LANGUAGES:
            response.set_cookie(
                "devtools_lang",
                g.lang,
                max_age=60 * 60 * 24 * 365,
                httponly=True,
                samesite="Lax",
                secure=request.is_secure,
            )
        if app.config["MINIFY_HTML"] and response.mimetype == "text/html" and not response.direct_passthrough:
            html = HTML_COMMENT_RE.sub("", response.get_data(as_text=True))
            response.set_data(INTER_TAG_WHITESPACE_RE.sub("><", html).strip())
        return response

    @app.context_processor
    def inject_tools():
        from app.tools.registry import TOOLS

        def static_asset(filename):
            if app.config["MINIFY_ASSETS"]:
                path = Path(app.static_folder) / filename
                minified = path.with_name(f"{path.stem}.min{path.suffix}")
                if minified.exists():
                    return str(Path(filename).with_name(minified.name)).replace("\\", "/")
            return filename

        def language_url(language):
            endpoint = request.endpoint or "dashboard.index"
            values = dict(request.view_args or {})
            values["lang"] = language
            return url_for(endpoint, **values)

        return {
            "tools": TOOLS,
            "current_lang": g.lang,
            "language_url": language_url,
            "static_asset": static_asset,
            "t": lambda key: translate(g.lang, key),
        }

    @app.errorhandler(RequestEntityTooLarge)
    def request_too_large(error):
        return "Uploaded file is too large. Maximum size is 8 MB.", 413

    return app
