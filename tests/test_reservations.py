"""Tests para Tarea 2.1: Utils de fechas y validación básica."""

import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from app.utils.dates import (
    ART,
    UTC,
    now_utc,
    now_art,
    to_utc,
    to_art,
    parse_iso_with_tz,
    parse_html_datetime_local,
    fmt_db,
    fmt_iso_with_offset,
    fmt_ui,
    parse_db_utc,
    validate_interval,
    validate_user,
    DB_FMT,
    HTML_DATETIME_LOCAL_FMT,
)
from app.services.reservations import (
    validate_reservation_input,
    ValidationError,
    reservation_to_dict,
)


class TestDatesUtils:
    """Tests para app.utils.dates."""

    def test_art_zoneinfo(self):
        """ART es ZoneInfo correcta."""
        assert str(ART) == "America/Argentina/Buenos_Aires"

    def test_now_utc_returns_aware_utc(self):
        """now_utc retorna datetime aware en UTC."""
        dt = now_utc()
        assert dt.tzinfo is not None
        assert dt.tzinfo == UTC

    def test_now_art_returns_aware_art(self):
        """now_art retorna datetime aware en ART."""
        dt = now_art()
        assert dt.tzinfo is not None
        assert dt.tzinfo == ART

    def test_to_utc_from_naive_assumes_art(self):
        """to_utc con naive asume ART y convierte a UTC."""
        # 10:00 ART = 13:00 UTC
        dt_naive = datetime(2025, 1, 15, 10, 0, 0)
        dt_utc = to_utc(dt_naive)
        assert dt_utc.tzinfo == UTC
        assert dt_utc.hour == 13
        assert dt_utc.minute == 0

    def test_to_utc_from_aware_converts(self):
        """to_utc con aware convierte correctamente."""
        dt_art = datetime(2025, 1, 15, 10, 0, 0, tzinfo=ART)
        dt_utc = to_utc(dt_art)
        assert dt_utc.tzinfo == UTC
        assert dt_utc.hour == 13

    def test_to_art_from_naive_assumes_art(self):
        """to_art con naive asume ART (no cambia hora)."""
        dt_naive = datetime(2025, 1, 15, 10, 0, 0)
        dt_art = to_art(dt_naive)
        assert dt_art.tzinfo == ART
        assert dt_art.hour == 10

    def test_to_art_from_utc_converts(self):
        """to_art desde UTC convierte correctamente."""
        dt_utc = datetime(2025, 1, 15, 13, 0, 0, tzinfo=UTC)
        dt_art = to_art(dt_utc)
        assert dt_art.tzinfo == ART
        assert dt_art.hour == 10

    def test_parse_iso_with_tz_offset_colon(self):
        """Parsea ISO 8601 con offset -03:00 (dos puntos)."""
        dt = parse_iso_with_tz("2025-01-15T10:00:00-03:00")
        assert dt.tzinfo == UTC
        assert dt.hour == 13  # 10:00 ART = 13:00 UTC
        assert dt.minute == 0

    def test_parse_iso_with_tz_offset_no_colon(self):
        """Parsea ISO 8601 con offset -0300 (sin dos puntos)."""
        dt = parse_iso_with_tz("2025-01-15T10:00:00-0300")
        assert dt.tzinfo == UTC
        assert dt.hour == 13

    def test_parse_iso_with_tz_zulu(self):
        """Parsea ISO 8601 con Z (UTC)."""
        dt = parse_iso_with_tz("2025-01-15T13:00:00Z")
        assert dt.tzinfo == UTC
        assert dt.hour == 13

    def test_parse_iso_with_tz_positive_offset(self):
        """Parsea ISO 8601 con offset positivo."""
        dt = parse_iso_with_tz("2025-01-15T10:00:00+02:00")
        assert dt.tzinfo == UTC
        assert dt.hour == 8  # 10:00 +02:00 = 08:00 UTC

    def test_parse_iso_with_tz_without_seconds(self):
        """Parsea ISO 8601 sin segundos."""
        dt = parse_iso_with_tz("2025-01-15T10:00-03:00")
        assert dt.tzinfo == UTC
        assert dt.hour == 13
        assert dt.minute == 0
        assert dt.second == 0

    def test_parse_iso_with_tz_positive_offset_no_colon(self):
        """Parsea ISO 8601 con offset positivo sin dos puntos."""
        dt = parse_iso_with_tz("2025-01-15T10:00:00+0200")
        assert dt.tzinfo == UTC
        assert dt.hour == 8

    def test_parse_iso_with_tz_invalid_raises(self):
        """Formato inválido lanza ValueError."""
        with pytest.raises(ValueError):
            parse_iso_with_tz("2025-01-15T10:00:00")  # sin zona
        with pytest.raises(ValueError):
            parse_iso_with_tz("")  # vacío
        with pytest.raises(ValueError):
            parse_iso_with_tz("no-es-fecha")
        with pytest.raises(ValueError):
            parse_iso_with_tz(None)  # tipo inválido
        with pytest.raises(ValueError):
            parse_iso_with_tz(123)  # tipo inválido

    def test_parse_html_datetime_local(self):
        """Parsea datetime-local naive asumiendo ART → UTC."""
        dt = parse_html_datetime_local("2025-01-15T10:00")
        assert dt.tzinfo == UTC
        assert dt.hour == 13  # 10:00 ART = 13:00 UTC

    def test_parse_html_datetime_local_invalid_raises(self):
        """Formato datetime-local inválido lanza ValueError."""
        with pytest.raises(ValueError):
            parse_html_datetime_local("2025-01-15")  # sin hora
        with pytest.raises(ValueError):
            parse_html_datetime_local("")
        with pytest.raises(ValueError):
            parse_html_datetime_local(None)

    def test_fmt_db_formats_utc_correctly(self):
        """fmt_db formatea UTC a 'YYYY-MM-DD HH:MM:SS'."""
        dt = datetime(2025, 1, 15, 13, 0, 0, tzinfo=UTC)
        assert fmt_db(dt) == "2025-01-15 13:00:00"

    def test_fmt_db_naive_assumes_utc(self):
        """fmt_db con naive asume UTC."""
        dt = datetime(2025, 1, 15, 13, 0, 0)
        assert fmt_db(dt) == "2025-01-15 13:00:00"

    def test_fmt_db_converts_from_art(self):
        """fmt_db convierte ART a UTC antes de formatear."""
        dt = datetime(2025, 1, 15, 10, 0, 0, tzinfo=ART)
        assert fmt_db(dt) == "2025-01-15 13:00:00"

    def test_fmt_iso_with_offset_returns_art_offset(self):
        """fmt_iso_with_offset retorna ISO con offset -03:00."""
        dt = datetime(2025, 1, 15, 13, 0, 0, tzinfo=UTC)
        result = fmt_iso_with_offset(dt)
        assert result == "2025-01-15T10:00:00-03:00"

    def test_fmt_ui_returns_local_format(self):
        """fmt_ui retorna formato local DD/MM/YYYY HH:MM."""
        dt = datetime(2025, 1, 15, 13, 0, 0, tzinfo=UTC)
        assert fmt_ui(dt) == "15/01/2025 10:00"

    def test_parse_db_utc(self):
        """parse_db_utc parsea formato BD a UTC aware."""
        dt = parse_db_utc("2025-01-15 13:00:00")
        assert dt.tzinfo == UTC
        assert dt.hour == 13

    def test_validate_interval_ok(self):
        """Intervalo válido retorna None."""
        start = datetime(2025, 1, 15, 13, 0, 0, tzinfo=UTC)
        end = datetime(2025, 1, 15, 14, 0, 0, tzinfo=UTC)
        assert validate_interval(start, end) is None

    def test_validate_interval_start_equals_end_error(self):
        """start == end retorna error."""
        dt = datetime(2025, 1, 15, 13, 0, 0, tzinfo=UTC)
        err = validate_interval(dt, dt)
        assert err is not None
        assert "anterior" in err

    def test_validate_interval_start_after_end_error(self):
        """start > end retorna error."""
        start = datetime(2025, 1, 15, 14, 0, 0, tzinfo=UTC)
        end = datetime(2025, 1, 15, 13, 0, 0, tzinfo=UTC)
        err = validate_interval(start, end)
        assert err is not None

    def test_validate_user_ok(self):
        """User válido retorna None."""
        assert validate_user("Juan") is None
        assert validate_user("  Juan  ") is None

    def test_validate_user_empty_error(self):
        """User vacío retorna error."""
        err = validate_user("")
        assert err is not None
        assert "obligatorio" in err
        err = validate_user("   ")
        assert err is not None

    def test_validate_user_none_error(self):
        """User None retorna error."""
        err = validate_user(None)
        assert err is not None


class TestValidationService:
    """Tests para app.services.reservations.validate_reservation_input."""

    def test_valid_input_returns_normalized(self):
        """Entrada válida retorna dict normalizado con UTC."""
        result = validate_reservation_input(
            unit_id=1,
            user="Juan Pérez",
            start="2025-01-15T10:00:00-03:00",
            end="2025-01-15T11:00:00-03:00",
            notes="  Prueba  "
        )
        assert result["unit_id"] == 1
        assert result["user"] == "Juan Pérez"
        assert result["start_utc"].tzinfo == UTC
        assert result["start_utc"].hour == 13  # 10:00 ART = 13:00 UTC
        assert result["end_utc"].hour == 14
        assert result["notes"] == "Prueba"

    def test_valid_input_with_zulu(self):
        """Entrada con Z (UTC) funciona."""
        result = validate_reservation_input(
            unit_id=1,
            user="Test",
            start="2025-01-15T13:00:00Z",
            end="2025-01-15T14:00:00Z",
        )
        assert result["start_utc"].hour == 13
        assert result["end_utc"].hour == 14

    def test_valid_input_with_positive_offset(self):
        """Entrada con offset positivo funciona."""
        result = validate_reservation_input(
            unit_id=1,
            user="Test",
            start="2025-01-15T10:00:00+02:00",
            end="2025-01-15T11:00:00+02:00",
        )
        assert result["start_utc"].hour == 8  # 10:00 +02:00 = 08:00 UTC

    def test_empty_user_raises(self):
        """User vacío lanza ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_reservation_input(1, "", "2025-01-15T10:00:00-03:00", "2025-01-15T11:00:00-03:00")
        assert exc.value.code == "INVALID_USER"

    def test_whitespace_user_raises(self):
        """User solo espacios lanza ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_reservation_input(1, "   ", "2025-01-15T10:00:00-03:00", "2025-01-15T11:00:00-03:00")
        assert exc.value.code == "INVALID_USER"

    def test_start_equals_end_raises(self):
        """start == end lanza ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_reservation_input(1, "Juan", "2025-01-15T10:00:00-03:00", "2025-01-15T10:00:00-03:00")
        assert exc.value.code == "INVALID_INTERVAL"

    def test_start_after_end_raises(self):
        """start > end lanza ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_reservation_input(1, "Juan", "2025-01-15T11:00:00-03:00", "2025-01-15T10:00:00-03:00")
        assert exc.value.code == "INVALID_INTERVAL"

    def test_invalid_datetime_format_raises(self):
        """Formato datetime inválido lanza ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_reservation_input(1, "Juan", "2025-01-15T10:00:00", "2025-01-15T11:00:00-03:00")
        assert exc.value.code == "INVALID_DATETIME_FORMAT"

    def test_invalid_datetime_format_end_raises(self):
        """Formato datetime inválido en end lanza ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_reservation_input(1, "Juan", "2025-01-15T10:00:00-03:00", "2025-01-15T11:00:00")
        assert exc.value.code == "INVALID_DATETIME_FORMAT"

    def test_notes_optional_stripped(self):
        """Notes opcional, se trimea y None si vacío."""
        result = validate_reservation_input(1, "Juan", "2025-01-15T10:00:00-03:00", "2025-01-15T11:00:00-03:00", notes=None)
        assert result["notes"] is None
        result = validate_reservation_input(1, "Juan", "2025-01-15T10:00:00-03:00", "2025-01-15T11:00:00-03:00", notes="  ")
        assert result["notes"] is None
        result = validate_reservation_input(1, "Juan", "2025-01-15T10:00:00-03:00", "2025-01-15T11:00:00-03:00", notes="  nota  ")
        assert result["notes"] == "nota"

    def test_user_stripped(self):
        """User se trimea."""
        result = validate_reservation_input(1, "  Juan  ", "2025-01-15T10:00:00-03:00", "2025-01-15T11:00:00-03:00")
        assert result["user"] == "Juan"

    # --- Tests para tipos incorrectos ---
    def test_unit_id_non_int_raises(self):
        """unit_id no entero lanza ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_reservation_input("1", "Juan", "2025-01-15T10:00:00-03:00", "2025-01-15T11:00:00-03:00")
        assert exc.value.code == "INVALID_TYPE"

    def test_user_non_str_raises(self):
        """user no string lanza ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_reservation_input(1, 123, "2025-01-15T10:00:00-03:00", "2025-01-15T11:00:00-03:00")
        assert exc.value.code == "INVALID_TYPE"

    def test_start_non_str_raises(self):
        """start no string lanza ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_reservation_input(1, "Juan", 123, "2025-01-15T11:00:00-03:00")
        assert exc.value.code == "INVALID_TYPE"

    def test_end_non_str_raises(self):
        """end no string lanza ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_reservation_input(1, "Juan", "2025-01-15T10:00:00-03:00", 123)
        assert exc.value.code == "INVALID_TYPE"

    def test_notes_non_str_raises(self):
        """notes no string lanza ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_reservation_input(1, "Juan", "2025-01-15T10:00:00-03:00", "2025-01-15T11:00:00-03:00", notes=123)
        assert exc.value.code == "INVALID_TYPE"

    def test_start_none_raises(self):
        """start None lanza ValidationError por tipo."""
        with pytest.raises(ValidationError) as exc:
            validate_reservation_input(1, "Juan", None, "2025-01-15T11:00:00-03:00")
        assert exc.value.code == "INVALID_TYPE"

    def test_end_none_raises(self):
        """end None lanza ValidationError por tipo."""
        with pytest.raises(ValidationError) as exc:
            validate_reservation_input(1, "Juan", "2025-01-15T10:00:00-03:00", None)
        assert exc.value.code == "INVALID_TYPE"


class TestReservationToDict:
    """Tests para reservation_to_dict con fila compatible con esquema real."""

    def make_mock_row(self, **overrides):
        """Crea un mock row compatible con sqlite3.Row."""
        from unittest.mock import MagicMock
        
        base = {
            "id": 1,
            "unit_id": 1,
            "user": "Juan",
            "start_utc": "2025-01-15 13:00:00",
            "end_utc": "2025-01-15 14:00:00",
            "notes": "Prueba",
            "status": "activa",
            "created_at": "2025-01-15 12:00:00",
            "cancelled_at": None,
            "unit_code": "MIC-01",
            "unit_name": "Microscopio digital",
        }
        base.update(overrides)
        
        row = MagicMock()
        row.keys.return_value = list(base.keys())
        row.__getitem__.side_effect = lambda k: base[k]
        return row

    def test_reservation_to_dict_complete(self):
        """Convierte row completa con unit_code y unit_name."""
        row = self.make_mock_row()
        result = reservation_to_dict(row)
        
        assert result["id"] == 1
        assert result["unit_id"] == 1
        assert result["unit_code"] == "MIC-01"
        assert result["unit_name"] == "Microscopio digital"
        assert result["user"] == "Juan"
        assert result["start"] == "2025-01-15T10:00:00-03:00"
        assert result["end"] == "2025-01-15T11:00:00-03:00"
        assert result["notes"] == "Prueba"
        assert result["status"] == "activa"
        assert result["created_at"] == "2025-01-15 12:00:00"
        assert result["cancelled_at"] is None

    def test_reservation_to_dict_without_unit_info(self):
        """Convierte row sin unit_code ni unit_name (consulta simple)."""
        row = self.make_mock_row(unit_code=None, unit_name=None)
        # Simular que las claves no existen
        from unittest.mock import MagicMock
        base = {
            "id": 1,
            "unit_id": 1,
            "user": "Juan",
            "start_utc": "2025-01-15 13:00:00",
            "end_utc": "2025-01-15 14:00:00",
            "notes": "Prueba",
            "status": "activa",
            "created_at": "2025-01-15 12:00:00",
            "cancelled_at": None,
        }
        row = MagicMock()
        row.keys.return_value = list(base.keys())
        row.__getitem__.side_effect = lambda k: base[k]
        
        result = reservation_to_dict(row)
        
        assert result["unit_code"] is None
        assert result["unit_name"] is None
        assert result["start"] == "2025-01-15T10:00:00-03:00"
        assert result["end"] == "2025-01-15T11:00:00-03:00"

    def test_reservation_to_dict_null_dates(self):
        """Maneja fechas nulas correctamente."""
        from unittest.mock import MagicMock
        base = {
            "id": 1,
            "unit_id": 1,
            "user": "Juan",
            "start_utc": None,
            "end_utc": None,
            "notes": None,
            "status": "activa",
            "created_at": "2025-01-15 12:00:00",
            "cancelled_at": "2025-01-15 12:30:00",
        }
        row = MagicMock()
        row.keys.return_value = list(base.keys())
        row.__getitem__.side_effect = lambda k: base[k]
        
        result = reservation_to_dict(row)
        
        assert result["start"] is None
        assert result["end"] is None
        assert result["notes"] is None
        assert result["cancelled_at"] == "2025-01-15 12:30:00"

    def test_reservation_to_dict_cancelled_status(self):
        """Convierte reserva cancelada correctamente."""
        row = self.make_mock_row(status="cancelada", cancelled_at="2025-01-15 12:30:00")
        result = reservation_to_dict(row)
        
        assert result["status"] == "cancelada"
        assert result["cancelled_at"] == "2025-01-15 12:30:00"