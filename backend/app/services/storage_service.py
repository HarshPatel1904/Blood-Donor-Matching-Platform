import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from app.config import Config


class BaseStorageService(ABC):
    """Abstract interface defining document storage operations."""

    @abstractmethod
    def save_file(self, file: FileStorage, category: str) -> Tuple[bool, str, Optional[str]]:
        """
        Saves an uploaded file under a given category (e.g., 'requisitions', 'hospital_licenses').
        Returns (success, message, relative_file_path_or_url).
        """
        pass

    @abstractmethod
    def get_file_path(self, relative_path: str) -> Optional[Path]:
        """Resolves local absolute path for serving or inspection."""
        pass

    @abstractmethod
    def delete_file(self, relative_path: str) -> bool:
        """Deletes a stored file."""
        pass


class LocalStorageService(BaseStorageService):
    """Concrete local filesystem storage implementation for local development."""

    def __init__(self):
        self.base_upload_dir = Path(Config.UPLOAD_FOLDER).resolve()
        self.allowed_extensions = {ext.lower() for ext in Config.ALLOWED_EXTENSIONS}
        self.max_bytes = Config.MAX_CONTENT_LENGTH

        # Ensure root upload directories exist
        (self.base_upload_dir / "requisitions").mkdir(parents=True, exist_ok=True)
        (self.base_upload_dir / "hospital_licenses").mkdir(parents=True, exist_ok=True)

    def _is_allowed_extension(self, filename: str) -> bool:
        if "." not in filename:
            return False
        ext = filename.rsplit(".", 1)[1].lower()
        return ext in self.allowed_extensions

    def save_file(self, file: FileStorage, category: str) -> Tuple[bool, str, Optional[str]]:
        if not file or not file.filename:
            return False, "No file provided.", None

        if not self._is_allowed_extension(file.filename):
            allowed_list = ", ".join(sorted(list(self.allowed_extensions)))
            return False, f"Unsupported file type. Allowed formats: {allowed_list}", None

        # Sanitize category folder
        safe_category = "requisitions" if category == "requisitions" else "hospital_licenses"
        target_dir = self.base_upload_dir / safe_category
        target_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique, collisions-free, sanitized filename
        original_clean = secure_filename(file.filename)
        file_ext = original_clean.rsplit(".", 1)[1].lower() if "." in original_clean else "bin"
        unique_filename = f"{uuid.uuid4().hex[:12]}_{original_clean}"
        destination = target_dir / unique_filename

        try:
            file.save(str(destination))
            # Store normalized relative path using forward slashes
            relative_path = f"uploads/{safe_category}/{unique_filename}"
            return True, "File saved successfully.", relative_path
        except Exception as e:
            return False, f"Failed to save file to local disk: {str(e)}", None

    def get_file_path(self, relative_path: str) -> Optional[Path]:
        if not relative_path:
            return None

        # Normalize relative path to backend root
        clean_rel = relative_path.replace("\\", "/").lstrip("/")
        if clean_rel.startswith("uploads/"):
            clean_rel = clean_rel[len("uploads/"):]

        candidate = (self.base_upload_dir / clean_rel).resolve()

        # Prevent directory traversal attacks
        try:
            candidate.relative_to(self.base_upload_dir)
        except ValueError:
            return None

        return candidate if candidate.is_file() else None

    def delete_file(self, relative_path: str) -> bool:
        file_path = self.get_file_path(relative_path)
        if file_path and file_path.exists():
            try:
                file_path.unlink()
                return True
            except OSError:
                return False
        return False


_storage_instance: Optional[BaseStorageService] = None


def get_storage_service() -> BaseStorageService:
    """
    Factory function returning the active storage provider.
    Stage 1: returns LocalStorageService.
    Stage 2: switches to S3StorageService.
    """
    global _storage_instance
    if _storage_instance is None:
        if Config.STORAGE_BACKEND == "local":
            _storage_instance = LocalStorageService()
        elif Config.STORAGE_BACKEND == "s3":
            raise NotImplementedError("S3 storage adapter will be activated in Stage 2 during AWS deployment.")
        else:
            raise ValueError(f"Unsupported STORAGE_BACKEND: {Config.STORAGE_BACKEND}")
    return _storage_instance