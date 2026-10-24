#!/usr/bin/env python
"""Punto de entrada de la aplicación."""

import os
from app import create_app

if __name__ == "__main__":
    config_name = os.environ.get("FLASK_ENV", "development")
    app = create_app(config_name)
    app.run(host="127.0.0.1", port=5000, debug=True)