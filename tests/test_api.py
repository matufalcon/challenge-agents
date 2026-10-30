"""Tests de integración para endpoints API."""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from app.utils.dates import parse_iso_with_tz, parse_db_utc
from app.services.reservations import ValidationError


class TestUnitsAPI:
    """Tests para GET /api/units."""

    def test_get_units_ok(self, client):
        """GET /api/units retorna 200 con lista de 5 equipos."""
        response = client.get("/api/units")
        assert response.status_code == 200
        data = response.get_json()
        assert "units" in data
        assert len(data["units"]) == 5
        
        # Verificar estructura de cada unidad
        for unit in data["units"]:
            assert "id" in unit
            assert "code" in unit
            assert "name" in unit
            assert "type" in unit
        
        # Verificar códigos esperados
        codes = [u["code"] for u in data["units"]]
        expected = ["FUE-01", "MIC-01", "MIC-02", "MUL-01", "OSC-01"]
        assert codes == expected


class TestReservationsAPI:
    """Tests para endpoints de reservas."""

    @pytest.fixture
    def sample_reservation(self, db_conn):
        """Crea una reserva de ejemplo para tests."""
        from app.models import create_reservation
        from app.utils.dates import parse_iso_with_tz
        
        start_utc = parse_iso_with_tz("2025-01-15T10:00:00-03:00")
        end_utc = parse_iso_with_tz("2025-01-15T11:00:00-03:00")
        res_id = create_reservation(db_conn, 1, "Juan", start_utc, end_utc, "Notas")
        return res_id

    def test_get_reservation_ok(self, client, sample_reservation):
        """GET /api/reservations/<id> retorna reserva completa."""
        response = client.get(f"/api/reservations/{sample_reservation}")
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["id"] == sample_reservation
        assert data["unit_id"] == 1
        assert data["unit_code"] == "MIC-01"
        assert data["unit_name"] == "Microscopio digital"
        assert data["user"] == "Juan"
        assert data["notes"] == "Notas"
        assert data["status"] == "activa"
        assert data["start"] == "2025-01-15T10:00:00-03:00"
        assert data["end"] == "2025-01-15T11:00:00-03:00"
        assert "created_at" in data
        assert data["cancelled_at"] is None

    def test_get_reservation_not_found(self, client):
        """GET /api/reservations/999 retorna 404."""
        response = client.get("/api/reservations/999")
        assert response.status_code == 404
        data = response.get_json()
        assert data["code"] == "NOT_FOUND"

    def test_post_reservation_ok(self, client):
        """POST /api/reservations crea reserva válida."""
        data = {
            "unit_id": 2,
            "user": "Pedro",
            "start": "2025-01-15T10:00:00-03:00",
            "end": "2025-01-15T11:00:00-03:00",
            "notes": "Prueba API"
        }
        response = client.post("/api/reservations", json=data)
        assert response.status_code == 201
        assert "Location" in response.headers
        
        data_resp = response.get_json()
        assert data_resp["unit_id"] == 2
        assert data_resp["user"] == "Pedro"
        assert data_resp["notes"] == "Prueba API"
        assert data_resp["status"] == "activa"
        assert data_resp["unit_code"] == "MIC-02"
        assert data_resp["unit_name"] == "Microscopio digital"
        assert data_resp["start"] == "2025-01-15T10:00:00-03:00"
        assert data_resp["end"] == "2025-01-15T11:00:00-03:00"
        assert "created_at" in data_resp
        assert data_resp["cancelled_at"] is None

    def test_post_reservation_invalid_user(self, client):
        """POST con user vacío retorna 400 INVALID_USER."""
        data = {
            "unit_id": 1,
            "user": "",
            "start": "2025-01-15T10:00:00-03:00",
            "end": "2025-01-15T11:00:00-03:00"
        }
        response = client.post("/api/reservations", json=data)
        assert response.status_code == 400
        data_resp = response.get_json()
        assert data_resp["code"] == "INVALID_USER"

    def test_post_reservation_invalid_interval(self, client):
        """POST con start >= end retorna 400 INVALID_INTERVAL."""
        data = {
            "unit_id": 1,
            "user": "Juan",
            "start": "2025-01-15T11:00:00-03:00",
            "end": "2025-01-15T10:00:00-03:00"
        }
        response = client.post("/api/reservations", json=data)
        assert response.status_code == 400
        data_resp = response.get_json()
        assert data_resp["code"] == "INVALID_INTERVAL"

    def test_post_reservation_invalid_datetime(self, client):
        """POST con formato datetime inválido retorna 400."""
        data = {
            "unit_id": 1,
            "user": "Juan",
            "start": "2025-01-15T10:00:00",  # sin zona horaria
            "end": "2025-01-15T11:00:00-03:00"
        }
        response = client.post("/api/reservations", json=data)
        assert response.status_code == 400
        data_resp = response.get_json()
        assert data_resp["code"] == "INVALID_DATETIME_FORMAT"

    def test_post_reservation_overlap(self, client, sample_reservation):
        """POST con solapamiento retorna 409 OVERLAP."""
        # sample_reservation es 10:00-11:00 en unit 1
        data = {
            "unit_id": 1,
            "user": "Pedro",
            "start": "2025-01-15T10:30:00-03:00",
            "end": "2025-01-15T11:30:00-03:00"
        }
        response = client.post("/api/reservations", json=data)
        assert response.status_code == 409
        data_resp = response.get_json()
        assert data_resp["code"] == "OVERLAP"

    def test_post_reservation_unit_not_found(self, client):
        """POST con unit_id inexistente retorna 404 UNIT_NOT_FOUND."""
        data = {
            "unit_id": 999,
            "user": "Juan",
            "start": "2025-01-15T10:00:00-03:00",
            "end": "2025-01-15T11:00:00-03:00"
        }
        response = client.post("/api/reservations", json=data)
        assert response.status_code == 404
        data_resp = response.get_json()
        assert data_resp["code"] == "UNIT_NOT_FOUND"

    def test_post_reservation_invalid_type(self, client):
        """POST con unit_id string retorna 400 INVALID_TYPE."""
        data = {
            "unit_id": "1",
            "user": "Juan",
            "start": "2025-01-15T10:00:00-03:00",
            "end": "2025-01-15T11:00:00-03:00"
        }
        response = client.post("/api/reservations", json=data)
        assert response.status_code == 400
        data_resp = response.get_json()
        assert data_resp["code"] == "INVALID_TYPE"

    def test_post_reservation_missing_json(self, client):
        """POST sin Content-Type JSON retorna 400."""
        response = client.post("/api/reservations", data="not json")
        assert response.status_code == 400
        data_resp = response.get_json()
        assert data_resp["code"] == "INVALID_CONTENT_TYPE"


class TestCancelReservationAPI:
    """Tests para PATCH /api/reservations/<id>/cancel."""

    @pytest.fixture
    def active_reservation(self, db_conn):
        """Crea una reserva activa para cancelar."""
        from app.models import create_reservation
        from app.utils.dates import parse_iso_with_tz
        
        start_utc = parse_iso_with_tz("2025-01-15T10:00:00-03:00")
        end_utc = parse_iso_with_tz("2025-01-15T11:00:00-03:00")
        return create_reservation(db_conn, 1, "Juan", start_utc, end_utc, "Cancelar")

    def test_cancel_ok(self, client, active_reservation):
        """PATCH /cancel cancela reserva y retorna estado actualizado."""
        response = client.patch(f"/api/reservations/{active_reservation}/cancel")
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["id"] == active_reservation
        assert data["status"] == "cancelada"
        assert data["cancelled_at"] is not None
        assert "T" in data["cancelled_at"]  # Formato ISO 8601
        assert "-03:00" in data["cancelled_at"] or "+00:00" in data["cancelled_at"]

    def test_cancel_not_found(self, client):
        """PATCH /cancel en ID inexistente retorna 404."""
        response = client.patch("/api/reservations/999/cancel")
        assert response.status_code == 404
        data = response.get_json()
        assert data["code"] == "NOT_FOUND"

    def test_cancel_idempotent(self, client, active_reservation):
        """Segunda cancelación retorna 404."""
        # Primera cancelación
        client.patch(f"/api/reservations/{active_reservation}/cancel")
        # Segunda cancelación
        response = client.patch(f"/api/reservations/{active_reservation}/cancel")
        assert response.status_code == 404
        data = response.get_json()
        assert data["code"] == "NOT_FOUND"


class TestAvailabilityAPI:
    """Tests para GET /api/availability."""

    @pytest.fixture
    def existing_reservation(self, db_conn):
        """Crea reserva existente para tests de disponibilidad."""
        from app.models import create_reservation
        from app.utils.dates import parse_iso_with_tz
        
        start_utc = parse_iso_with_tz("2025-01-15T10:00:00-03:00")
        end_utc = parse_iso_with_tz("2025-01-15T12:00:00-03:00")
        return create_reservation(db_conn, 1, "Juan", start_utc, end_utc)

    def test_availability_ok(self, client):
        """GET /api/availability en intervalo libre retorna available=true."""
        response = client.get("/api/availability?unit_id=2&start=2025-01-15T10:00:00-03:00&end=2025-01-15T11:00:00-03:00")
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["unit_id"] == 2
        assert data["unit_code"] == "MIC-02"
        assert data["available"] is True
        assert data["conflicts"] == []
        assert data["requested_start"] == "2025-01-15T10:00:00-03:00"
        assert data["requested_end"] == "2025-01-15T11:00:00-03:00"

    def test_availability_conflict(self, client, existing_reservation):
        """GET /api/availability con conflicto retorna available=false y conflicts."""
        # existing_reservation es 10:00-12:00 en unit 1
        response = client.get("/api/availability?unit_id=1&start=2025-01-15T11:00:00-03:00&end=2025-01-15T13:00:00-03:00")
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["available"] is False
        assert len(data["conflicts"]) == 1
        conflict = data["conflicts"][0]
        assert conflict["id"] == 1
        assert conflict["user"] == "Juan"
        assert "start" in conflict
        assert "end" in conflict

    def test_availability_consecutive_allowed(self, client, db_conn):
        """Intervalos consecutivos no son conflicto."""
        # Crear reserva 10:00-12:00 en unit 2 usando la misma conexión
        from app.services.reservations import create_reservation_with_validation
        
        create_reservation_with_validation(db_conn, 2, "Juan", "2025-01-15T10:00:00-03:00", "2025-01-15T12:00:00-03:00")
        
        # Consultar disponibilidad exactamente al final: 12:00-14:00
        response = client.get("/api/availability?unit_id=2&start=2025-01-15T12:00:00-03:00&end=2025-01-15T14:00:00-03:00")
        assert response.status_code == 200
        data = response.get_json()
        assert data["available"] is True
        assert data["conflicts"] == []

    def test_availability_missing_params(self, client):
        """GET sin parámetros retorna 400 MISSING_PARAMS."""
        response = client.get("/api/availability")
        assert response.status_code == 400
        data = response.get_json()
        assert data["code"] == "MISSING_PARAMS"

    def test_availability_invalid_unit_id(self, client):
        """unit_id string retorna 400 INVALID_TYPE."""
        response = client.get("/api/availability?unit_id=abc&start=2025-01-15T10:00:00-03:00&end=2025-01-15T11:00:00-03:00")
        assert response.status_code == 400
        data = response.get_json()
        assert data["code"] == "INVALID_TYPE"

    def test_availability_unit_not_found(self, client):
        """unit_id inexistente retorna 404 UNIT_NOT_FOUND."""
        response = client.get("/api/availability?unit_id=999&start=2025-01-15T10:00:00-03:00&end=2025-01-15T11:00:00-03:00")
        assert response.status_code == 404
        data = response.get_json()
        assert data["code"] == "UNIT_NOT_FOUND"

    def test_availability_invalid_datetime(self, client):
        """Formato datetime inválido retorna 400 INVALID_DATETIME_FORMAT."""
        response = client.get("/api/availability?unit_id=1&start=2025-01-15T10:00:00&end=2025-01-15T11:00:00-03:00")
        assert response.status_code == 400
        data = response.get_json()
        assert data["code"] == "INVALID_DATETIME_FORMAT"

    def test_availability_invalid_interval(self, client):
        """start >= end retorna 400 INVALID_INTERVAL."""
        response = client.get("/api/availability?unit_id=1&start=2025-01-15T11:00:00-03:00&end=2025-01-15T10:00:00-03:00")
        assert response.status_code == 400
        data = response.get_json()
        assert data["code"] == "INVALID_INTERVAL"

    def test_availability_conflicts_always_list(self, client):
        """conflicts siempre es lista (vacía si disponible)."""
        response = client.get("/api/availability?unit_id=1&start=2025-01-15T10:00:00-03:00&end=2025-01-15T11:00:00-03:00")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data["conflicts"], list)
        assert data["conflicts"] == []