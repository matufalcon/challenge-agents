"""Factory de la aplicación Flask."""

from flask import Flask
from app.config import config


def create_app(config_name: str = None) -> Flask:
    """Crea y configura la instancia de Flask."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")
    
    app = Flask(__name__, 
                template_folder="templates",
                static_folder="static")
    
    app.config.from_object(config[config_name])
    
    # Registrar blueprints
    from app.routes.web import bp as web_bp
    app.register_blueprint(web_bp)
    
    # Health check simple
    @app.route("/health")
    def health():
        from app.config import Config
        return {
            "status": "ok",
            "tz": Config.TIMEZONE
        }, 200
    
    return app


import os  # noqa: E402 (import después de create_app para evitar circular)