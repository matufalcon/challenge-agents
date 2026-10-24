"""Rutas web: páginas que renderizan templates."""

from flask import Blueprint, render_template

bp = Blueprint("web", __name__)


@bp.route("/")
def index():
    """Página inicial con identidad visual del laboratorio."""
    return render_template("index.html")