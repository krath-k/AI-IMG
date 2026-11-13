"""
app.py
Application Entrypoint for the SpectraForensics AI Image Detector System.
Runs out-of-the-box with a single command: python app.py
"""

import os
import sys
import logging
from flask import Flask, render_template, send_from_directory, jsonify

# Configure root directory in Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app")

# Import database models and blueprint routes
from models.database import init_db
from init_db import seed_database
from routes.auth_routes import auth_bp
from routes.detector_routes import detector_bp
from routes.admin_routes import admin_bp


def create_app() -> Flask:
    """Application factory for Flask with modular blueprints and static frontend routing."""
    template_folder = os.path.join(BASE_DIR, "frontend", "templates")
    static_folder = os.path.join(BASE_DIR, "frontend", "static")

    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder
    )

    # Configuration
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "spectra-forensics-production-session-key-999")
    app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB max upload
    app.config["UPLOAD_FOLDER_ORIGINALS"] = os.path.join(static_folder, "uploads", "originals")
    app.config["UPLOAD_FOLDER_HEATMAPS"] = os.path.join(static_folder, "uploads", "heatmaps")

    # Ensure directories exist
    os.makedirs(app.config["UPLOAD_FOLDER_ORIGINALS"], exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER_HEATMAPS"], exist_ok=True)

    # Auto-initialize and seed SQLite database
    logger.info("Initializing database schema and seed accounts...")
    seed_database()

    # Register modular Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(detector_bp)
    app.register_blueprint(admin_bp)

    # Root Web Route
    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    # Static uploads handler
    @app.route("/static/uploads/<path:filename>", methods=["GET"])
    def serve_uploads(filename):
        return send_from_directory(os.path.join(static_folder, "uploads"), filename)

    # Health Check API
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "SpectraForensics AI Image Detector",
            "version": "2.1.0"
        }), 200

    # Error Handlers
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({"error": "File size exceeds the 25MB maximum limit."}), 413

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found."}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({"error": "An internal server error occurred in the forensic engine."}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")

    print("\n" + "=" * 65)
    print("  SPECTRA FORENSICS | AI IMAGE DETECTOR SYSTEM")
    print(f"  Server URL:  http://127.0.0.1:{port}")
    print("  Default Admin:   admin@forensic.ai   / AdminPass123!")
    print("  Default Analyst: demo@forensic.ai    / DemoUser123!")
    print("=" * 65 + "\n")

    app.run(host=host, port=port, debug=False)
