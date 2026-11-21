from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for React frontend portals (local dev + Stage 2 S3 website)
    cors_origins = list(dict.fromkeys(
        origin.rstrip("/")
        for origin in [
            *getattr(config_class, "CORS_ORIGINS", []),
            config_class.FRONTEND_URL,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://raktsetu-web-harsh-2026.s3-website-us-east-1.amazonaws.com",
        ]
        if origin
    ))
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    )

    # Register Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.common_routes import common_bp
    from app.routes.donor_routes import donor_bp
    from app.routes.request_routes import request_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.matching_routes import matching_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(common_bp)
    app.register_blueprint(donor_bp)
    app.register_blueprint(request_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(matching_bp)

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"success": False, "error": "Endpoint not found."}), 404

    @app.errorhandler(500)
    def handle_internal_error(e):
        return jsonify({"success": False, "error": "Internal server error."}), 500

    return app