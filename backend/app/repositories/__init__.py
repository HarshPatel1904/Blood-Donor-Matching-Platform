from app.config import Config
from app.repositories.base_repository import BaseRepository
from app.repositories.sqlite_repository import SQLiteRepository

_repository_instance: BaseRepository = None


def get_repository() -> BaseRepository:
    """
    Returns the active database repository instance determined by Config.DATABASE_BACKEND.
    Stage 1: returns SQLiteRepository.
    Stage 2: switches to DynamoDBRepository when configured.
    """
    global _repository_instance
    if _repository_instance is None:
        if Config.DATABASE_BACKEND == "sqlite":
            _repository_instance = SQLiteRepository()
        elif Config.DATABASE_BACKEND == "dynamodb":
            from app.repositories.dynamodb_repository import DynamoDBRepository

            _repository_instance = DynamoDBRepository()
        else:
            raise ValueError(f"Unsupported DATABASE_BACKEND: {Config.DATABASE_BACKEND}")
    return _repository_instance
