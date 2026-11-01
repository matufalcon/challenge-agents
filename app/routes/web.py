"""Rutas web: páginas que renderizan templates."""

from flask import Blueprint, render_template

bp = Blueprint("web", __name__)


@bp.route("/")
def index():
    """Página inicial con identidad visual del laboratorio."""
    return render_template("index.html")


@bp.route("/availability")
def availability():
    """Página de consulta de disponibilidad."""
    return render_template("availability.html")


@bp.route("/reservations")
def reservations():
    """Página de listado de reservas."""
    return render_template("reservations.html")