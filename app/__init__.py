"""Factory de la aplicación Flask."""

from flask import Flask
from app.config import config
from app.models import init_db, close_db


def create_app(config_name: str = None, config_overrides: dict = None) -> Flask:
    """Crea y configura la instancia de Flask
    Args:
        config_name: Nombre de configuración ("development", "production", "default").
        config_overrides: Diccionario opcional para sobreescribir config (ej. DB_PATH para tests).
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")
    
    app = Flask(__name__, 
                template_folder="templates",
                static_folder="static")
    
    app.config.from_object(config[config_name])
    
    # Aplicar overrides ANTES de inicializar BD
    if config_overrides:
        app.config.update(config_overrides)
    # Inicializar BD (idempotente)
    with app.app_context():
        init_db()

    # Registrar blueprints
    from app.routes.web import bp as web_bp
    app.register_blueprint(web_bp)
    
    # Teardown: cerrar conexión BD al finalizar request
    app.teardown_appcontext(close_db)

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