"""Configuración centralizada de la aplicación."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

class Config:
    """Configuración base."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    JSON_SORT_KEYS = False
    
    # Base de datos (preparada para siguiente sprint)
    DB_PATH = DATA_DIR / "reservations.db"
    
    # Zona horaria: Argentina (ART, UTC-3, sin DST desde 2009)
    TIMEZONE = "America/Argentina/Buenos_Aires"
    
    # Horarios de laboratorio (pendiente de definición)
    # LAB_OPEN_HOUR = 8
    # LAB_CLOSE_HOUR = 20
    # LAB_DAYS = [0, 1, 2, 3, 4]  # Lunes a viernes


class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = "development"


class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = "production"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}