#!/usr/bin/env python3
"""Shared session management utilities for Claude Code hooks.

This module provides session management functionality that can be shared
across pre_tool_use.py and post_tool_use.py hooks to ensure consistent
session tracking.

Session Management Logic:
1. Check for existing session file at `.omni-cortex/current_session.json`
2. If session exists and is valid (not timed out), use it
3. If no valid session, create a new one in both file and database
4. Update last_activity_at on each use to track session activity
"""

import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Session timeout in seconds (4 hours of inactivity = new session)
SESSION_TIMEOUT_SECONDS = 4 * 60 * 60


def generate_session_id() -> str:
    """Generate a unique session ID matching the MCP format.

    Returns:
        Session ID in format: sess_{timestamp_ms}_{random_hex}
    """
    timestamp_ms = int(time.time() * 1000)
    random_hex = os.urandom(4).hex()
    return f"sess_{timestamp_ms}_{random_hex}"


def get_session_file_path() -> Path:
    """Get the path to the current session file.

    Returns:
        Path to .omni-cortex/current_session.json
    """
    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    return Path(project_path) / ".omni-cortex" / "current_session.json"


def load_session_file() -> Optional[dict]:
    """Load the current session from file if it exists.

    Returns:
        Session data dict or None if file doesn't exist or is invalid
    """
    session_file = get_session_file_path()
    if not session_file.exists():
        return None

    try:
        with open(session_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def save_session_file(session_data: dict) -> None:
    """Save the current session to file.

    Args:
        session_data: Dict containing session_id, project_path, started_at, last_activity_at
    """
    session_file = get_session_file_path()
    session_file.parent.mkdir(parents=True, exist_ok=True)

    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)


def is_session_valid(session_data: dict) -> bool:
    """Check if a session is still valid (not timed out).

    A session is valid if:
    - It has a last_activity_at timestamp
    - The timestamp is within SESSION_TIMEOUT_SECONDS of now

    Args:
        session_data: Session dict with last_activity_at field

    Returns:
        True if session is valid, False otherwise
    """
    last_activity = session_data.get("last_activity_at")
    if not last_activity:
        return False

    try:
        last_time = datetime.fromisoformat(last_activity.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        elapsed_seconds = (now - last_time).total_seconds()
        return elapsed_seconds < SESSION_TIMEOUT_SECONDS
    except (ValueError, TypeError):
        return False


def create_session_in_db(conn: sqlite3.Connection, session_id: str, project_path: str) -> None:
    """Create a new session record in the database.

    Also creates the sessions table if it doesn't exist (for first-run scenarios).

    Args:
        conn: SQLite database connection
        session_id: The session ID to create
        project_path: The project directory path
    """
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    # Check if sessions table exists (it might not if only activities table was created)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
    if cursor.fetchone() is None:
        # Create sessions table with minimal schema
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                project_path TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                summary TEXT,
                tags TEXT,
                metadata TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at DESC);
            CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_path);
        """)
        conn.commit()

    cursor.execute(
        """
        INSERT OR IGNORE INTO sessions (id, project_path, started_at)
        VALUES (?, ?, ?)
        """,
        (session_id, project_path, now),
    )
    conn.commit()


def get_or_create_session(conn: sqlite3.Connection, project_path: str) -> str:
    """Get the current session ID, creating a new one if needed.

    Session management logic:
    1. Check for existing session file
    2. If exists and not timed out, use it and update last_activity
    3. If doesn't exist or timed out, create new session

    Args:
        conn: SQLite database connection
        project_path: The project directory path

    Returns:
        The session ID to use for activity logging
    """
    session_data = load_session_file()
    now_iso = datetime.now(timezone.utc).isoformat()

    if session_data and is_session_valid(session_data):
        # Update last activity time
        session_data["last_activity_at"] = now_iso
        save_session_file(session_data)
        return session_data["session_id"]

    # Create new session
    session_id = generate_session_id()

    # Create in database
    create_session_in_db(conn, session_id, project_path)

    # Save to file
    session_data = {
        "session_id": session_id,
        "project_path": project_path,
        "started_at": now_iso,
        "last_activity_at": now_iso,
    }
    save_session_file(session_data)

    return session_id
