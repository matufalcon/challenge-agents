"""Pruebas de salud básica de la aplicación."""

import pytest


class TestHealth:
    """Pruebas del endpoint de salud y página inicial."""

    def test_health_endpoint(self, client):
        """GET /health devuelve 200 y JSON con status y timezone."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["tz"] == "America/Argentina/Buenos_Aires"

    def test_index_page(self, client):
        """GET / devuelve 200 y HTML con contenido identificable de la página inicial."""
        response = client.get("/")
        assert response.status_code == 200
        
        html = response.get_data(as_text=True)
        
        # Verificar elementos identificables de la página inicial
        assert "Equilab" in html
        assert "Sistema de reservas de equipos de laboratorio" in html
        assert "Versión 0.1.0" in html
        assert "Argentina (ART, UTC-3)" in html
        assert "Inventario fijo" in html
        assert "Calendario semanal" in html
        assert "Reservas persistentes" in html
        
        # Verificar estructura HTML básica
        assert "<html" in html.lower()
        assert "<head>" in html.lower()
        assert "<body>" in html.lower()
        assert "</html>" in html.lower()

    def test_index_contains_css_tokens(self, client):
        """La página incluye referencias a los tokens CSS de identidad visual."""
        response = client.get("/")
        html = response.get_data(as_text=True)
        
        # Verificar que se cargan los CSS
        assert "variables.css" in html
        assert "base.css" in html
        
        # Verificar que los colores clave están definidos en variables.css (carga indirecta)
        # Esto se verifica más a fondo en test de integración visual si se desea