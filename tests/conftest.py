"""Fixtures compartidas para pruebas."""

import pytest
import tempfile
import os
from pathlib import Path

from app import create_app
from app.models import get_db_connection
from scripts.seed import seed_units


@pytest.fixture
def app():
    """Crea una app Flask para testing con BD temporal."""
    # Usar BD temporal en archivo para tests
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    
    test_config = {
        "TESTING": True,
        "DB_PATH": Path(db_path),
        "SECRET_KEY": "test-secret",
        "TIMEZONE": "America/Argentina/Buenos_Aires",
    }
    
    # Pasar config_overrides ANTES de create_app para que init_db use la BD temporal
    app = create_app("default", config_overrides=test_config)
    
    with app.app_context():
        # Ejecutar seed para poblar inventario
        seed_units(Path(db_path))
        yield app
    
    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def client(app):
    """Cliente de prueba Flask."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Runner de comandos CLI."""
    return app.test_cli_runner()


@pytest.fixture
def db_path(app):
    """Obtiene la ruta de la BD temporal del fixture app."""
    return Path(app.config["DB_PATH"])


@pytest.fixture
def db_conn(db_path):
    """Conexión a BD temporal con esquema y seed."""
    conn = get_db_connection(db_path)
    yield conn
    conn.close()