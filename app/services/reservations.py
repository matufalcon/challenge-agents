"""Servicio de reservas — Lógica de negocio (sin dependencias Flask).

Capa pura de validación y reglas de negocio. No accede a BD directamente.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from app.utils.dates import (
    validate_interval,
    validate_user,
    to_utc,
    parse_iso_with_tz,
    fmt_db,
    fmt_iso_with_offset,
    parse_db_utc,
)


class ValidationError(Exception):
    """Error de validación de datos de reserva."""
    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.code = code


def _validate_type(value: Any, expected_type: type, field_name: str, code: str) -> None:
    """Valida que un valor sea del tipo esperado."""
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"Campo '{field_name}' debe ser de tipo {expected_type.__name__}, se recibió {type(value).__name__}",
            code
        )


def validate_reservation_input(
    unit_id: int,
    user: str,
    start: str,
    end: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """Valida datos de entrada para crear reserva.
    
    Args:
        unit_id: ID del equipo (debe existir en BD, validación aparte)
        user: Solicitante (obligatorio, no vacío)
        start: ISO 8601 con zona horaria (ej. '2025-01-15T10:00:00-03:00')
        end: ISO 8601 con zona horaria
        notes: Opcional
    
    Returns:
        Dict con datos normalizados: unit_id, user, start_utc, end_utc, notes
    
    Raises:
        ValidationError: Si hay error de validación (códigos: INVALID_USER, INVALID_DATETIME_FORMAT, INVALID_INTERVAL, INVALID_TYPE)
    """
    # Validar tipos de entrada
    _validate_type(unit_id, int, "unit_id", "INVALID_TYPE")
    _validate_type(user, str, "user", "INVALID_TYPE")
    _validate_type(start, str, "start", "INVALID_TYPE")
    _validate_type(end, str, "end", "INVALID_TYPE")
    if notes is not None:
        _validate_type(notes, str, "notes", "INVALID_TYPE")
    
    # Validar user
    err = validate_user(user)
    if err:
        raise ValidationError(err, "INVALID_USER")
    
    # Parsear fechas (exige zona horaria explícita)
    try:
        start_utc = parse_iso_with_tz(start)
        end_utc = parse_iso_with_tz(end)
    except ValueError as e:
        raise ValidationError(str(e), "INVALID_DATETIME_FORMAT")
    
    # Validar intervalo
    err = validate_interval(start_utc, end_utc)
    if err:
        raise ValidationError(err, "INVALID_INTERVAL")
    
    # Normalizar notes
    notes_norm = notes.strip() if notes and notes.strip() else None
    
    return {
        "unit_id": unit_id,
        "user": user.strip(),
        "start_utc": start_utc,
        "end_utc": end_utc,
        "notes": notes_norm,
    }


def reservation_to_dict(row: Any) -> Dict[str, Any]:
    """Convierte Row de BD a dict para respuesta API.
    
    Espera columnas de reservations: id, unit_id, user, start_utc, end_utc, notes, status, created_at, cancelled_at
    Opcionalmente (si se hace JOIN con units): unit_code, unit_name
    """
    # Parsear fechas de BD (formato UTC: YYYY-MM-DD HH:MM:SS) y convertir a ISO con offset ART
    start_iso = None
    end_iso = None
    if row["start_utc"]:
        start_iso = fmt_iso_with_offset(to_utc(parse_db_utc(row["start_utc"])))
    if row["end_utc"]:
        end_iso = fmt_iso_with_offset(to_utc(parse_db_utc(row["end_utc"])))
    
    return {
        "id": row["id"],
        "unit_id": row["unit_id"],
        "unit_code": row["unit_code"] if "unit_code" in row.keys() else None,
        "unit_name": row["unit_name"] if "unit_name" in row.keys() else None,
        "user": row["user"],
        "start": start_iso,
        "end": end_iso,
        "notes": row["notes"],
        "status": row["status"],
        "created_at": row["created_at"],
        "cancelled_at": row["cancelled_at"],
    }