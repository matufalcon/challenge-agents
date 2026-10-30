"""Endpoints API REST para Equilab."""

from flask import Blueprint, request, jsonify, url_for
import sqlite3

from app.services.reservations import (
    validate_reservation_input,
    check_overlap,
    create_reservation_with_validation,
    ValidationError,
    reservation_to_dict,
    check_availability,
)
from app.models import (
    get_db,
    get_all_units,
    get_reservation_by_id,
    get_reservation_with_unit,
    cancel_reservation,
    unit_exists,
)
from app.utils.dates import parse_iso_with_tz, parse_db_utc, to_utc, fmt_iso_with_offset

bp = Blueprint("api", __name__, url_prefix="/api")


def _json_error(message: str, code: str, status: int):
    """Respuesta de error JSON estándar."""
    return jsonify({"error": message, "code": code}), status


@bp.route("/units", methods=["GET"])
def get_units():
    """Lista el inventario fijo de equipos."""
    try:
        units = get_all_units()
        result = [
            {
                "id": u["id"],
                "code": u["code"],
                "name": u["name"],
                "type": u["type"],
            }
            for u in units
        ]
        return jsonify({"units": result}), 200
    except Exception:
        return _json_error("Error interno del servidor", "INTERNAL_ERROR", 500)


@bp.route("/reservations/<int:reservation_id>", methods=["GET"])
def get_reservation(reservation_id: int):
    """Consulta una reserva por ID."""
    try:
        conn = get_db()
        row = get_reservation_with_unit(conn, reservation_id)
        if not row:
            return _json_error("Reserva no encontrada", "NOT_FOUND", 404)
        return jsonify(reservation_to_dict(row)), 200
    except Exception:
        return _json_error("Error interno del servidor", "INTERNAL_ERROR", 500)


@bp.route("/reservations", methods=["POST"])
def create_reservation():
    """Crea una reserva con validación completa."""
    if not request.is_json:
        return _json_error("Content-Type debe ser application/json", "INVALID_CONTENT_TYPE", 400)

    data = request.get_json(silent=True)
    if not data:
        return _json_error("Body JSON inválido", "INVALID_JSON", 400)

    # Extraer y validar campos requeridos
    unit_id = data.get("unit_id")
    user = data.get("user")
    start = data.get("start")
    end = data.get("end")
    notes = data.get("notes")

    # Validar existencia de unit_id antes de insertar
    if not isinstance(unit_id, int):
        return _json_error("unit_id debe ser un entero", "INVALID_TYPE", 400)

    if not unit_exists(unit_id):
        return _json_error("Equipo no encontrado", "UNIT_NOT_FOUND", 404)

    # Usar servicio para validación completa y creación
    conn = get_db()
    try:
        result = create_reservation_with_validation(
            conn, unit_id, user, start, end, notes
        )
        response = jsonify(result)
        response.status_code = 201
        response.headers["Location"] = url_for("api.get_reservation", reservation_id=result["id"])
        return response
    except ValidationError as e:
        status = 409 if e.code == "OVERLAP" else 400
        return _json_error(str(e), e.code, status)
    except sqlite3.IntegrityError:
        return _json_error("Error de integridad en la base de datos", "INTEGRITY_ERROR", 500)
    except Exception:
        return _json_error("Error interno del servidor", "INTERNAL_ERROR", 500)


@bp.route("/reservations/<int:reservation_id>/cancel", methods=["PATCH"])
def cancel_reservation_endpoint(reservation_id: int):
    """Cancela una reserva activa."""
    try:
        conn = get_db()
        result = cancel_reservation(conn, reservation_id)
        if not result:
            return _json_error("Reserva no encontrada o ya cancelada", "NOT_FOUND", 404)

        # Retornar reserva actualizada
        row = get_reservation_with_unit(conn, reservation_id)
        return jsonify(reservation_to_dict(row)), 200
    except Exception:
        return _json_error("Error interno del servidor", "INTERNAL_ERROR", 500)


@bp.route("/availability", methods=["GET"])
def get_availability():
    """Consulta disponibilidad de un equipo en un intervalo."""
    # Parámetros query
    unit_id_str = request.args.get("unit_id")
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    # Validar parámetros requeridos
    if unit_id_str is None or start_str is None or end_str is None:
        return _json_error("Parámetros requeridos: unit_id, start, end", "MISSING_PARAMS", 400)

    # Validar unit_id
    try:
        unit_id = int(unit_id_str)
    except (ValueError, TypeError):
        return _json_error("unit_id debe ser un entero", "INVALID_TYPE", 400)

    if not unit_exists(unit_id):
        return _json_error("Equipo no encontrado", "UNIT_NOT_FOUND", 404)

    # Parsear y validar fechas
    try:
        start_utc = parse_iso_with_tz(start_str)
        end_utc = parse_iso_with_tz(end_str)
    except ValueError as e:
        return _json_error(str(e), "INVALID_DATETIME_FORMAT", 400)

    # Validar intervalo
    from app.utils.dates import validate_interval
    err = validate_interval(start_utc, end_utc)
    if err:
        return _json_error(err, "INVALID_INTERVAL", 400)

    # Verificar disponibilidad
    conn = get_db()
    result = check_availability(conn, unit_id, start_utc, end_utc)

    # Obtener info del equipo
    from app.models import get_unit_by_id
    unit = get_unit_by_id(unit_id)

    # Formatear respuesta
    response = {
        "unit_id": unit_id,
        "unit_code": unit["code"] if unit else None,
        "unit_name": unit["name"] if unit else None,
        "requested_start": fmt_iso_with_offset(start_utc),
        "requested_end": fmt_iso_with_offset(end_utc),
        "available": result["available"],
        "conflicts": result["conflicts"],
    }
    return jsonify(response), 200