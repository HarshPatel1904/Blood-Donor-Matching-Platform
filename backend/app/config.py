import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

# Load .env file explicitly
load_dotenv(BASE_DIR / ".env")

class Config:
    """Base application configuration loaded from environment variables."""
    APP_ENV = os.getenv("APP_ENV", "local")
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-jwt-secret-key")
    
    # Storage and Database selection
    DATABASE_BACKEND = os.getenv("DATABASE_BACKEND", "sqlite")
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
    EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "console")
    
    # Path configuration
    SQLITE_DB_PATH = BASE_DIR / os.getenv("SQLITE_DB_PATH", "instance/blood_platform.db")
    UPLOAD_FOLDER = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")
    LOCALITIES_FILE = ROOT_DIR / "data" / "localities.json"
    
    # Allowed Document Upload Settings
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB maximum upload
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
    
    # CORS
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    CORS_ORIGINS = [
        origin.strip().rstrip("/")
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5175,http://127.0.0.1:5175,http://localhost:5176,http://127.0.0.1:5176,http://raktsetu-web-harsh-2026.s3-website-us-east-1.amazonaws.com"
        ).split(",")
        if origin.strip()
    ]
    ADMIN_PORTAL_ORIGINS = [
        origin.strip().rstrip("/")
        for origin in os.getenv(
            "ADMIN_PORTAL_ORIGINS",
            "http://localhost:5176,http://127.0.0.1:5176"
        ).split(",")
        if origin.strip()
    ]

    # AWS configuration for Stage 2
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    DYNAMODB_TABLE_PREFIX = os.getenv("DYNAMODB_TABLE_PREFIX", "blood_platform_")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "raktsetu-docs-harsh-2026")