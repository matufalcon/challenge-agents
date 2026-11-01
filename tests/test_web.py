"""Tests de integración para vistas web."""

import pytest


class TestWebViews:
    """Tests para vistas web (páginas HTML)."""

    def test_availability_page(self, client):
        """GET /availability retorna 200 y renderiza la plantilla."""
        response = client.get("/availability")
        assert response.status_code == 200
        assert b"Disponibilidad" in response.data

    def test_reservations_page(self, client):
        """GET /reservations retorna 200 y renderiza la plantilla."""
        response = client.get("/reservations")
        assert response.status_code == 200
        assert b"Reservas" in response.data

    def test_nav_links_render(self, client):
        """GET / renderiza los enlaces de navegación funcionales."""
        response = client.get("/")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert 'href="/availability"' in html
        assert 'href="/reservations"' in html