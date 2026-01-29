"""Database layer for Omni Cortex - SQLite with FTS5."""

from .connection import get_connection, init_database, close_connection
from .schema import SCHEMA_VERSION, get_schema_sql
from .sync import (
    sync_memory_to_global,
    delete_memory_from_global,
    search_global_memories,
    get_global_stats,
    sync_all_project_memories,
)

__all__ = [
    "get_connection",
    "init_database",
    "close_connection",
    "SCHEMA_VERSION",
    "get_schema_sql",
    "sync_memory_to_global",
    "delete_memory_from_global",
    "search_global_memories",
    "get_global_stats",
    "sync_all_project_memories",
]
