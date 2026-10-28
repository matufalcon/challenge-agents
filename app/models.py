"""Capa de acceso a datos (SQLite directo, sin ORM)."""

import sqlite3
from datetime import datetime
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


# --- Reservas ---

def create_reservation(
    conn: sqlite3.Connection,
    unit_id: int,
    user: str,
    start_utc: datetime,
    end_utc: datetime,
    notes: Optional[str] = None
) -> int:
    """Inserta una nueva reserva con estado 'activa'.
    
    Args:
        conn: Conexión SQLite con FK habilitadas.
        unit_id: ID de la unidad (debe existir).
        user: Solicitante.
        start_utc: Inicio en UTC (datetime aware).
        end_utc: Fin en UTC (datetime aware).
        notes: Notas opcionales.
    
    Returns:
        ID de la reserva creada.
    
    Raises:
        sqlite3.IntegrityError: Si unit_id no existe (FK).
    """
    from app.utils.dates import fmt_db
    start_db = fmt_db(start_utc)
    end_db = fmt_db(end_utc)
    
    cursor = conn.execute(
        """INSERT INTO reservations (unit_id, user, start_utc, end_utc, notes, status)
           VALUES (?, ?, ?, ?, ?, 'activa')""",
        (unit_id, user, start_db, end_db, notes)
    )
    conn.commit()
    return cursor.lastrowid


def get_reservation_by_id(conn: sqlite3.Connection, reservation_id: int) -> Optional[sqlite3.Row]:
    """Retorna una reserva por su ID (sin JOIN)."""
    return conn.execute(
        """SELECT id, unit_id, user, start_utc, end_utc, notes, status, created_at, cancelled_at
           FROM reservations WHERE id = ?""",
        (reservation_id,)
    ).fetchone()


def get_reservation_with_unit(conn: sqlite3.Connection, reservation_id: int) -> Optional[sqlite3.Row]:
    """Retorna una reserva con JOIN a units (incluye unit_code, unit_name)."""
    return conn.execute(
        """SELECT r.id, r.unit_id, r.user, r.start_utc, r.end_utc, r.notes, r.status,
                  r.created_at, r.cancelled_at,
                  u.code as unit_code, u.name as unit_name
           FROM reservations r
           JOIN units u ON r.unit_id = u.id
           WHERE r.id = ?""",
        (reservation_id,)
    ).fetchone()


def get_active_reservations_for_unit(
    conn: sqlite3.Connection,
    unit_id: int,
    start_utc: Optional[datetime] = None,
    end_utc: Optional[datetime] = None
) -> List[sqlite3.Row]:
    """Lista reservas activas de una unidad.
    
    Args:
        conn: Conexión SQLite.
        unit_id: ID de la unidad.
        start_utc: Si se provee, filtra reservas con end_utc > start_utc (inicio del rango).
        end_utc: Si se provee, filtra reservas con start_utc < end_utc (fin del rango).
    
    Semántica de filtros temporales:
    - Sin filtros: todas las reservas activas de la unidad.
    - Con start_utc: reservas que terminan DESPUÉS del inicio del rango (end_utc > start_utc).
    - Con end_utc: reservas que empiezan ANTES del fin del rango (start_utc < end_utc).
    - Con ambos: reservas que se solapan con el rango [start_utc, end_utc).
    - No incluye lógica de solapamiento compleja; solo filtra por límites.
    
    Returns:
        Lista de filas (sqlite3.Row) con columnas de reservations.
    """
    from app.utils.dates import fmt_db
    query = """SELECT id, unit_id, user, start_utc, end_utc, notes, status, created_at, cancelled_at
               FROM reservations
               WHERE unit_id = ? AND status = 'activa'"""
    params = [unit_id]
    
    if start_utc is not None:
        query += " AND end_utc > ?"
        params.append(fmt_db(start_utc))
    if end_utc is not None:
        query += " AND start_utc < ?"
        params.append(fmt_db(end_utc))
    
    query += " ORDER BY start_utc"
    
    return conn.execute(query, params).fetchall()


def cancel_reservation(conn: sqlite3.Connection, reservation_id: int) -> bool:
    """Cancela una reserva activa.
    
    Args:
        conn: Conexión SQLite.
        reservation_id: ID de la reserva a cancelar.
    
    Returns:
        True si la reserva existía, estaba activa y se canceló.
        False si no existe o ya estaba cancelada (no modifica nada).
    
    Efecto:
        - status -> 'cancelada'
        - cancelled_at -> ahora (UTC)
        - Conserva todos los demás datos originales.
    """
    from app.utils.dates import now_utc, fmt_db
    # Verificar que existe y está activa
    row = conn.execute(
        "SELECT id FROM reservations WHERE id = ? AND status = 'activa'",
        (reservation_id,)
    ).fetchone()
    
    if not row:
        return False
    
    cancelled_at_db = fmt_db(now_utc())
    conn.execute(
        "UPDATE reservations SET status = 'cancelada', cancelled_at = ? WHERE id = ?",
        (cancelled_at_db, reservation_id)
    )
    conn.commit()
    return True


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