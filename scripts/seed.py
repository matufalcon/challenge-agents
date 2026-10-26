#!/usr/bin/env python
"""Inicialización idempotente del inventario fijo (5 equipos del challenge)."""

import sqlite3
import sys
from pathlib import Path

# Unidades exactas del enunciado
UNITS = [
    {"code": "MIC-01", "name": "Microscopio digital", "type": "Microscopía"},
    {"code": "MIC-02", "name": "Microscopio digital", "type": "Microscopía"},
    {"code": "OSC-01", "name": "Osciloscopio", "type": "Medición"},
    {"code": "MUL-01", "name": "Multímetro", "type": "Medición"},
    {"code": "FUE-01", "name": "Fuente de alimentación", "type": "Potencia"},
]


def get_db_path() -> Path:
    """Ruta de la base de datos (data/reservations.db)."""
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir / "reservations.db"


def init_schema(db_path: Path) -> None:
    """Crea las tablas si no existen (idempotente)."""
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(schema_sql)
        conn.commit()


def seed_units(db_path: Path) -> int:
    """Inserta los 5 equipos si no existen (idempotente por code UNIQUE).
    
    Returns:
        Número de filas insertadas (0 si ya existían).
    
    Raises:
        sqlite3.IntegrityError: Si hay violación de integridad distinta a
            UNIQUE constraint en units.code (ej. NOT NULL, FK, etc.).
    """
    inserted = 0
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        for unit in UNITS:
            try:
                cursor.execute(
                    "INSERT INTO units (code, name, type) VALUES (?, ?, ?)",
                    (unit["code"], unit["name"], unit["type"])
                )
                inserted += 1
            except sqlite3.IntegrityError as e:
                # Solo ignorar violación de UNIQUE en units.code
                if "UNIQUE constraint failed: units.code" in str(e):
                    pass  # code ya existe → ignorar (idempotente)
                else:
                    raise  # propagar otros errores de integridad
        conn.commit()
    return inserted


def main() -> int:
    """Ejecuta inicialización completa: esquema + seed."""
    db_path = get_db_path()
    
    print(f"Base de datos: {db_path}")
    
    # 1. Crear esquema (idempotente)
    init_schema(db_path)
    print("Esquema verificado/creado.")
    
    # 2. Seed idempotente
    inserted = seed_units(db_path)
    if inserted:
        print(f"Seed: {inserted} equipos insertados.")
    else:
        print("Seed: equipos ya existentes (ningún cambio).")
    
    # 3. Verificar resultado
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute(
            "SELECT code, name, type FROM units ORDER BY code"
        ).fetchall()
        print(f"\nInventario actual ({len(rows)} equipos):")
        for row in rows:
            print(f"  {row['code']} — {row['name']} [{row['type']}]")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())