from __future__ import annotations

from flask import Flask

from .blueprints.api.routes import api_bp
from .blueprints.web.routes import web_bp
from .config import AppConfig
from .extensions import init_extensions


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    config = AppConfig.from_env()
    missing_keys = config.validate()
    if missing_keys:
        joined_keys = ", ".join(missing_keys)
        raise RuntimeError(f"Missing required environment variables: {joined_keys}")

    app.config.update(config.to_flask_dict())
    init_extensions(app)

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
