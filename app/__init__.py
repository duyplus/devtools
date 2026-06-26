from flask import Flask, g, request, url_for
from werkzeug.exceptions import RequestEntityTooLarge

from app.i18n import LANGUAGES, normalize_language, translate


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        MAX_CONTENT_LENGTH=8 * 1024 * 1024,
        SECRET_KEY="devtools-local",
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

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(icons_bp)
    app.register_blueprint(delimiter_bp)
    app.register_blueprint(percentage_bp)
    app.register_blueprint(base64_bp)
    app.register_blueprint(javascript_bp)
    app.register_blueprint(password_bp)

    @app.before_request
    def load_language():
        requested = request.args.get("lang") or request.cookies.get("devtools_lang")
        g.lang = normalize_language(requested)

    @app.after_request
    def remember_language(response):
        if request.args.get("lang") in LANGUAGES:
            response.set_cookie("devtools_lang", g.lang, max_age=60 * 60 * 24 * 365, samesite="Lax")
        return response

    @app.context_processor
    def inject_tools():
        from app.tools.registry import TOOLS

        def language_url(language):
            endpoint = request.endpoint or "dashboard.index"
            values = dict(request.view_args or {})
            values["lang"] = language
            return url_for(endpoint, **values)

        return {
            "tools": TOOLS,
            "current_lang": g.lang,
            "language_url": language_url,
            "t": lambda key: translate(g.lang, key),
        }

    @app.errorhandler(RequestEntityTooLarge)
    def request_too_large(error):
        return "Uploaded file is too large. Maximum size is 8 MB.", 413

    return app
