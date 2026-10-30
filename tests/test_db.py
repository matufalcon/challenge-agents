"""Pruebas de base de datos: esquema, seed, restricciones e idempotencia."""

import pytest
import sqlite3
from pathlib import Path

from app.models import (
    get_db_connection,
    count_units,
    get_units_list,
    init_db,
)


@pytest.fixture
def db_path(app):
    """Obtiene la ruta de la BD temporal del fixture app (ya inicializada)."""
    return Path(app.config["DB_PATH"])


class TestSchema:
    """Pruebas de estructura de la base de datos."""

    def test_units_table_exists(self, db_path):
        """La tabla units existe con las columnas correctas."""
        with get_db_connection(db_path) as conn:
            cols = conn.execute("PRAGMA table_info(units)").fetchall()
            col_names = {c["name"] for c in cols}
            
            expected = {"id", "code", "name", "type", "created_at"}
            assert expected.issubset(col_names), f"Faltan columnas: {expected - col_names}"
            
            # Verificar NOT NULL en code
            code_col = next(c for c in cols if c["name"] == "code")
            assert code_col["notnull"] == 1, "code debe ser NOT NULL"

    def test_reservations_table_exists(self, db_path):
        """La tabla reservations existe con las columnas correctas."""
        with get_db_connection(db_path) as conn:
            cols = conn.execute("PRAGMA table_info(reservations)").fetchall()
            col_names = {c["name"] for c in cols}
            
            expected = {
                "id", "unit_id", "user", "start_utc", "end_utc",
                "notes", "status", "created_at", "cancelled_at"
            }
            assert expected.issubset(col_names), f"Faltan columnas: {expected - col_names}"
            
            # Verificar FK
            fks = conn.execute("PRAGMA foreign_key_list(reservations)").fetchall()
            unit_fk = next((fk for fk in fks if fk["from"] == "unit_id"), None)
            assert unit_fk is not None, "Falta FK unit_id -> units(id)"
            assert unit_fk["table"] == "units"

    def test_indexes_created(self, db_path):
        """Los índices necesarios existen."""
        with get_db_connection(db_path) as conn:
            indexes = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='reservations'"
            ).fetchall()
            index_names = {idx["name"] for idx in indexes}
            
            assert "idx_reservations_unit_time" in index_names
            assert "idx_reservations_status" in index_names

    def test_foreign_keys_enabled(self, db_path):
        """PRAGMA foreign_keys = ON está efectivo en la conexión."""
        with get_db_connection(db_path) as conn:
            # Intentar insertar reservation con unit_id inexistente → debe fallar
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO reservations (unit_id, user, start_utc, end_utc) "
                    "VALUES (999, 'test', '2025-01-01 10:00:00', '2025-01-01 11:00:00')"
                )
                conn.commit()


class TestSeed:
    """Pruebas de inicialización del inventario (seed)."""

    def test_seed_inserts_five_units(self, db_path):
        """seed.py deja exactamente 5 equipos con codes correctos."""
        from scripts.seed import seed_units
        
        # El fixture app ya ejecutó seed, verificar estado final
        units = get_units_list(db_path)
        assert len(units) == 5
        
        codes = [u["code"] for u in units]
        expected_codes = ["FUE-01", "MIC-01", "MIC-02", "MUL-01", "OSC-01"]
        assert codes == expected_codes, f"Codes: {codes} != {expected_codes}"
        
        # Verificar names y types
        mic_units = [u for u in units if u["code"].startswith("MIC")]
        assert len(mic_units) == 2
        for u in mic_units:
            assert u["name"] == "Microscopio digital"
            assert u["type"] == "Microscopía"
        
        osc = next(u for u in units if u["code"] == "OSC-01")
        assert osc["name"] == "Osciloscopio"
        assert osc["type"] == "Medición"
        
        mul = next(u for u in units if u["code"] == "MUL-01")
        assert mul["name"] == "Multímetro"
        assert mul["type"] == "Medición"
        
        fue = next(u for u in units if u["code"] == "FUE-01")
        assert fue["name"] == "Fuente de alimentación"
        assert fue["type"] == "Potencia"

    def test_seed_idempotent(self, db_path):
        """Ejecutar seed dos veces no duplica equipos."""
        from scripts.seed import seed_units
        
        # El fixture app ya ejecutó seed una vez
        inserted_2 = seed_units(db_path)
        assert inserted_2 == 0, "Segunda ejecución no debería insertar nada"
        
        # Verificar total
        assert count_units(db_path) == 5

    def test_units_have_required_fields(self, db_path):
        """Cada unidad tiene code, name, type no nulos."""
        from scripts.seed import seed_units
        
        seed_units(db_path)
        units = get_units_list(db_path)
        
        for u in units:
            assert u["code"] is not None and u["code"] != ""
            assert u["name"] is not None and u["name"] != ""
            assert u["type"] is not None and u["type"] != ""

    def test_unique_constraint_code(self, db_path):
        """No se pueden insertar dos unidades con mismo code."""
        from scripts.seed import seed_units
        
        seed_units(db_path)
        
        with get_db_connection(db_path) as conn:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO units (code, name, type) VALUES (?, ?, ?)",
                    ("MIC-01", "Duplicado", "Test")
                )
                conn.commit()

    def test_name_not_unique(self, db_path):
        """Dos unidades PUEDEN tener el mismo name (MIC-01 y MIC-02)."""
        from scripts.seed import seed_units
        
        seed_units(db_path)
        
        # Esto NO debe fallar
        with get_db_connection(db_path) as conn:
            conn.execute(
                "INSERT INTO units (code, name, type) VALUES (?, ?, ?)",
                ("NEW-01", "Microscopio digital", "Microscopía")
            )
            conn.commit()
        
        # Verificar que ahora hay 6 unidades
        assert count_units(db_path) == 6
        
        # Verificar que ambas MIC y la nueva tienen el mismo name
        units = get_units_list(db_path)
        mic_names = [u["name"] for u in units if u["name"] == "Microscopio digital"]
        assert len(mic_names) == 3  # MIC-01, MIC-02, NEW-01


class TestInitDb:
    """Pruebas de inicialización del esquema."""

    def test_init_db_creates_tables(self, app):
        """init_db() crea las tablas si no existen (ya llamado por create_app)."""
        # El fixture app ya llamó init_db() en create_app
        db_path = Path(app.config["DB_PATH"])
        
        with get_db_connection(db_path) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {t["name"] for t in tables}
            
            assert "units" in table_names
            assert "reservations" in table_names

    def test_init_db_idempotent(self, app):
        """init_db() se puede llamar múltiples veces sin error."""
        # Ya se llamó una vez en create_app; llamar otra vez en contexto
        with app.app_context():
            init_db()
            init_db()  # No debe lanzar excepción
        
        db_path = Path(app.config["DB_PATH"])
        with get_db_connection(db_path) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            assert len(tables) >= 2


class TestDBIsolation:
    """Pruebas de aislamiento de base de datos en tests."""

    def test_test_app_uses_temp_db(self, app):
        """La app de test usa BD temporal, no data/reservations.db."""
        from pathlib import Path
        
        db_path = Path(app.config["DB_PATH"])
        real_db = Path("data/reservations.db")
        
        # La BD de test debe ser un archivo temporal, no la real
        assert db_path != real_db, f"DB de test ({db_path}) no debe ser la real ({real_db})"
        assert "tmp" in str(db_path).lower() or "temp" in str(db_path).lower(), \
            f"DB de test debe ser temporal: {db_path}"