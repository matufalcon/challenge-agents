"""Capa de acceso a datos (SQLite directo, sin ORM)."""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from flask import current_app, g


def get_db() -> sqlite3.Connection:
    """Obtiene conexión a BD para el request actual (con FK habilitadas)."""
    if "db" not in g:
        db_path = current_app.config["DB_PATH"]
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        # Obligatorio en SQLite: las FK no se enforcean por defecto
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e: Optional[BaseException] = None) -> None:
    """Cierra la conexión al finalizar el request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Inicializa el esquema de la base de datos (idempotente)."""
    db_path = current_app.config["DB_PATH"]
    schema_path = Path(__file__).resolve().parent.parent / "scripts" / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(schema_sql)
        conn.commit()


# --- Consultas de inventario ---

def get_all_units() -> List[sqlite3.Row]:
    """Retorna todas las unidades ordenadas por code."""
    db = get_db()
    return db.execute(
        "SELECT id, code, name, type, created_at FROM units ORDER BY code"
    ).fetchall()


def get_unit_by_id(unit_id: int) -> Optional[sqlite3.Row]:
    """Retorna una unidad por su ID numérico."""
    db = get_db()
    return db.execute(
        "SELECT id, code, name, type, created_at FROM units WHERE id = ?",
        (unit_id,)
    ).fetchone()


def get_unit_by_code(code: str) -> Optional[sqlite3.Row]:
    """Retorna una unidad por su código único."""
    db = get_db()
    return db.execute(
        "SELECT id, code, name, type, created_at FROM units WHERE code = ?",
        (code,)
    ).fetchone()


def unit_exists(unit_id: int) -> bool:
    """Verifica si existe una unidad con el ID dado."""
    db = get_db()
    row = db.execute(
        "SELECT 1 FROM units WHERE id = ?", (unit_id,)
    ).fetchone()
    return row is not None


# --- Helpers para tests / scripts ---

def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Conexión standalone para scripts/tests (con FK)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def count_units(db_path: Path) -> int:
    """Cuenta unidades en la BD (para tests)."""
    with get_db_connection(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM units").fetchone()[0]


def get_units_list(db_path: Path) -> List[Dict[str, Any]]:
    """Lista de unidades como dicts (para tests)."""
    with get_db_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT code, name, type FROM units ORDER BY code"
        ).fetchall()
        return [dict(row) for row in rows]