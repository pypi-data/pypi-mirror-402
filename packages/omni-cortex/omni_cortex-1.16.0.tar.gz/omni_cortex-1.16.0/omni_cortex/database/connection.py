"""SQLite connection management for Omni Cortex."""

import sqlite3
import threading
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from ..config import get_project_db_path, get_global_db_path, get_project_db_dir, get_global_db_dir
from .schema import get_schema_sql, SCHEMA_VERSION


# Thread-local storage for connections
_local = threading.local()

# Connection cache by path
_connections: dict[str, sqlite3.Connection] = {}
_lock = threading.Lock()


def _configure_connection(conn: sqlite3.Connection) -> None:
    """Configure a SQLite connection with optimal settings."""
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = -64000")  # 64MB cache


def get_connection(db_path: Optional[Path] = None, is_global: bool = False) -> sqlite3.Connection:
    """Get a database connection, creating it if necessary.

    Args:
        db_path: Explicit path to database file
        is_global: If True and no db_path, use global database

    Returns:
        SQLite connection
    """
    if db_path is None:
        db_path = get_global_db_path() if is_global else get_project_db_path()

    path_str = str(db_path)

    with _lock:
        if path_str not in _connections:
            # Ensure directory exists
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create connection
            conn = sqlite3.connect(path_str, check_same_thread=False)
            _configure_connection(conn)
            _connections[path_str] = conn

        return _connections[path_str]


def init_database(db_path: Optional[Path] = None, is_global: bool = False) -> sqlite3.Connection:
    """Initialize the database with schema.

    Args:
        db_path: Explicit path to database file
        is_global: If True and no db_path, use global database

    Returns:
        SQLite connection
    """
    if db_path is None:
        if is_global:
            db_path = get_global_db_path()
            db_dir = get_global_db_dir()
        else:
            db_path = get_project_db_path()
            db_dir = get_project_db_dir()
    else:
        db_dir = db_path.parent

    # Ensure directory exists
    db_dir.mkdir(parents=True, exist_ok=True)

    conn = get_connection(db_path)

    # Check if schema needs initialization
    cursor = conn.cursor()

    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memories'")
    if cursor.fetchone() is None:
        # Apply schema
        conn.executescript(get_schema_sql())

        # Record schema version
        from ..utils.timestamps import now_iso
        cursor.execute(
            "INSERT OR REPLACE INTO schema_migrations (version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION, now_iso())
        )
        conn.commit()

    return conn


def close_connection(db_path: Optional[Path] = None, is_global: bool = False) -> None:
    """Close a database connection.

    Args:
        db_path: Explicit path to database file
        is_global: If True and no db_path, use global database
    """
    if db_path is None:
        db_path = get_global_db_path() if is_global else get_project_db_path()

    path_str = str(db_path)

    with _lock:
        if path_str in _connections:
            _connections[path_str].close()
            del _connections[path_str]


def close_all_connections() -> None:
    """Close all database connections."""
    with _lock:
        for conn in _connections.values():
            conn.close()
        _connections.clear()


@contextmanager
def transaction(conn: sqlite3.Connection):
    """Context manager for database transactions."""
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
