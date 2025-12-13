# --- Base of Website Creation --- #

from flask import Flask
from app.routes.upload import bp as upload_bp
from app.routes.home import home_bp
from app.routes.pois import bp as pois_bp

def create_app():
    app = Flask(__name__)

    # ----------- Konfiguration -----------
    # Max. Upload‑Größe: 3MB  (3 * 1024 * 1024Bytes)
    app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024

    app.register_blueprint(upload_bp)  # Register the upload routes
    app.register_blueprint(home_bp)  # registriere die Startseite
    app.register_blueprint(pois_bp)
    return app
