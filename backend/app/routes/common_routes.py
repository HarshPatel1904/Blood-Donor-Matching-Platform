import json
from flask import Blueprint, jsonify
from app.config import Config

common_bp = Blueprint("common", __name__, url_prefix="/api")


@common_bp.route("/localities", methods=["GET"])
def get_localities():
    """Returns the list of supported Ahmedabad localities and their coordinates."""
    try:
        with open(Config.LOCALITIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"success": True, "data": data.get("localities", [])}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to load localities: {str(e)}"}), 500


@common_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "version": "1.1.0-cd",
        "env": Config.APP_ENV,
        "database": Config.DATABASE_BACKEND,
        "storage": Config.STORAGE_BACKEND,
        "email": Config.EMAIL_BACKEND
    }), 200