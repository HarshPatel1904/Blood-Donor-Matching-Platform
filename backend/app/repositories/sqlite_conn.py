import sqlite3
from contextlib import contextmanager
from app.config import Config


def get_db_path() -> str:
    """Returns the resolved absolute path to the SQLite database file."""
    Config.SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return str(Config.SQLITE_DB_PATH)


@contextmanager
def get_db_connection():
    """
    Context manager yielding a thread-safe SQLite connection with foreign keys enabled.
    Automatically commits on normal exit and rolls back if an unhandled exception occurs.
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()