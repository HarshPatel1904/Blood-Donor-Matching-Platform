import io
import mimetypes
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Tuple

import boto3
from botocore.exceptions import ClientError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.config import Config


class BaseStorageService(ABC):
    """Abstract interface defining document storage operations."""

    @abstractmethod
    def save_file(self, file: FileStorage, category: str) -> Tuple[bool, str, Optional[str]]:
        """
        Saves an uploaded file under a given category (e.g., 'requisitions', 'hospital_licenses').
        Returns (success, message, relative_file_path_or_key).
        """
        pass

    @abstractmethod
    def get_file_path(self, relative_path: str) -> Optional[Path]:
        """Resolves local absolute path for serving or inspection (None for remote storage)."""
        pass

    @abstractmethod
    def get_file_stream(self, relative_path: str) -> Optional[Tuple[io.BytesIO, str, str]]:
        """Returns (BytesIO stream, content_type, download_filename) if available."""
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

        # Generate unique, collision-free, sanitized filename
        original_clean = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex[:12]}_{original_clean}"
        destination = target_dir / unique_filename

        try:
            file.save(str(destination))
            relative_path = f"uploads/{safe_category}/{unique_filename}"
            return True, "File saved successfully.", relative_path
        except Exception as e:
            return False, f"Failed to save file to local disk: {str(e)}", None

    def get_file_path(self, relative_path: str) -> Optional[Path]:
        if not relative_path:
            return None

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

    def get_file_stream(self, relative_path: str) -> Optional[Tuple[io.BytesIO, str, str]]:
        resolved = self.get_file_path(relative_path)
        if not resolved:
            return None
        content_type, _ = mimetypes.guess_type(str(resolved))
        data = io.BytesIO(resolved.read_bytes())
        data.seek(0)
        return data, content_type or "application/octet-stream", resolved.name

    def delete_file(self, relative_path: str) -> bool:
        file_path = self.get_file_path(relative_path)
        if file_path and file_path.exists():
            try:
                file_path.unlink()
                return True
            except OSError:
                return False
        return False


class S3StorageService(BaseStorageService):
    """Concrete Amazon S3 storage implementation for Stage 2 AWS deployment."""

    def __init__(self, s3_client: Optional[Any] = None, bucket_name: Optional[str] = None):
        self.s3_client = s3_client or boto3.client("s3", region_name=Config.AWS_REGION)
        self.bucket_name = bucket_name or Config.S3_BUCKET_NAME
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME must be configured when STORAGE_BACKEND='s3'.")
        self.allowed_extensions = {ext.lower() for ext in Config.ALLOWED_EXTENSIONS}
        self.max_bytes = Config.MAX_CONTENT_LENGTH

    def _is_allowed_extension(self, filename: str) -> bool:
        if "." not in filename:
            return False
        ext = filename.rsplit(".", 1)[1].lower()
        return ext in self.allowed_extensions

    @staticmethod
    def _normalize_key(relative_path: str) -> Optional[str]:
        if not relative_path:
            return None
        clean = relative_path.replace("\\", "/").lstrip("/")
        if ".." in clean.split("/"):
            return None
        if clean.startswith("uploads/"):
            clean = clean[len("uploads/"):]
        if clean.startswith("hospital_licenses/"):
            clean = "licenses/" + clean[len("hospital_licenses/"):]
        return clean or None

    def save_file(self, file: FileStorage, category: str) -> Tuple[bool, str, Optional[str]]:
        if not file or not file.filename:
            return False, "No file provided.", None

        if not self._is_allowed_extension(file.filename):
            allowed_list = ", ".join(sorted(list(self.allowed_extensions)))
            return False, f"Unsupported file type. Allowed formats: {allowed_list}", None

        safe_category = "requisitions" if category == "requisitions" else "licenses"
        original_clean = secure_filename(file.filename)
        if not original_clean:
            return False, "Invalid filename.", None

        unique_filename = f"{uuid.uuid4().hex[:12]}_{original_clean}"
        s3_key = f"{safe_category}/{unique_filename}"

        try:
            stream = file.stream if hasattr(file, "stream") else file
            stream.seek(0)
            payload = stream.read()
            if len(payload) > self.max_bytes:
                return False, "File exceeds maximum allowed size (5 MB).", None

            content_type = (
                getattr(file, "content_type", None)
                or mimetypes.guess_type(original_clean)[0]
                or "application/octet-stream"
            )
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=payload,
                ContentType=content_type,
                ServerSideEncryption="AES256",
            )
            return True, "File uploaded to S3 successfully.", s3_key
        except Exception as e:
            return False, f"Failed to upload file to S3: {str(e)}", None

    def get_file_path(self, relative_path: str) -> Optional[Path]:
        return None

    def get_file_stream(self, relative_path: str) -> Optional[Tuple[io.BytesIO, str, str]]:
        s3_key = self._normalize_key(relative_path)
        if not s3_key:
            return None

        try:
            obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchKey", "404", "NotFound"):
                return None
            raise

        body_bytes = obj["Body"].read()
        content_type = (
            obj.get("ContentType")
            or mimetypes.guess_type(s3_key)[0]
            or "application/octet-stream"
        )
        filename = s3_key.rsplit("/", 1)[-1]
        stream = io.BytesIO(body_bytes)
        stream.seek(0)
        return stream, content_type, filename

    def generate_presigned_url(self, relative_path: str, expires_in: int = 300) -> Optional[str]:
        s3_key = self._normalize_key(relative_path)
        if not s3_key:
            return None
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": s3_key},
            ExpiresIn=expires_in,
        )

    def delete_file(self, relative_path: str) -> bool:
        s3_key = self._normalize_key(relative_path)
        if not s3_key:
            return False
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except Exception:
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
            _storage_instance = S3StorageService()
        else:
            raise ValueError(f"Unsupported STORAGE_BACKEND: {Config.STORAGE_BACKEND}")
    return _storage_instance
