"""Session model and CRUD operations."""

import json
import sqlite3
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict

from ..utils.ids import generate_session_id, generate_summary_id
from ..utils.timestamps import now_iso


class SessionCreate(BaseModel):
    """Input model for creating a session."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    session_id: Optional[str] = Field(None, description="Custom session ID")
    project_path: str = Field(..., description="Project directory path")
    provide_context: bool = Field(True, description="Whether to provide previous context")
    context_depth: int = Field(3, description="Number of past sessions to summarize", ge=1, le=10)


class Session(BaseModel):
    """Full session model from database."""

    id: str
    project_path: str
    started_at: str
    ended_at: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class SessionSummary(BaseModel):
    """Session summary model."""

    id: str
    session_id: str
    key_learnings: Optional[list[str]] = None
    key_decisions: Optional[list[str]] = None
    key_errors: Optional[list[str]] = None
    files_modified: Optional[list[str]] = None
    tools_used: Optional[dict[str, int]] = None
    total_activities: int = 0
    total_memories_created: int = 0
    created_at: str


def create_session(
    conn: sqlite3.Connection,
    data: SessionCreate,
) -> Session:
    """Create a new session.

    Args:
        conn: Database connection
        data: Session creation data

    Returns:
        Created session object
    """
    session_id = data.session_id or generate_session_id()
    now = now_iso()

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO sessions (id, project_path, started_at)
        VALUES (?, ?, ?)
        """,
        (session_id, data.project_path, now),
    )
    conn.commit()

    return Session(
        id=session_id,
        project_path=data.project_path,
        started_at=now,
    )


def get_session(conn: sqlite3.Connection, session_id: str) -> Optional[Session]:
    """Get a session by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    return _row_to_session(row) if row else None


def end_session(
    conn: sqlite3.Connection,
    session_id: str,
    summary: Optional[str] = None,
    key_learnings: Optional[list[str]] = None,
) -> Optional[Session]:
    """End a session and create summary.

    Args:
        conn: Database connection
        session_id: Session ID to end
        summary: Optional summary text
        key_learnings: Optional list of key learnings

    Returns:
        Updated session or None if not found
    """
    session = get_session(conn, session_id)
    if not session:
        return None

    now = now_iso()
    cursor = conn.cursor()

    # Update session
    cursor.execute(
        """
        UPDATE sessions
        SET ended_at = ?, summary = ?
        WHERE id = ?
        """,
        (now, summary, session_id),
    )

    # Gather session statistics
    cursor.execute(
        "SELECT COUNT(*) FROM activities WHERE session_id = ?",
        (session_id,),
    )
    total_activities = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM memories WHERE source_session_id = ?",
        (session_id,),
    )
    total_memories = cursor.fetchone()[0]

    # Get tools used
    cursor.execute(
        """
        SELECT tool_name, COUNT(*) as cnt
        FROM activities
        WHERE session_id = ? AND tool_name IS NOT NULL
        GROUP BY tool_name
        """,
        (session_id,),
    )
    tools_used = {row["tool_name"]: row["cnt"] for row in cursor.fetchall()}

    # Get files modified
    cursor.execute(
        """
        SELECT DISTINCT file_path
        FROM activities
        WHERE session_id = ? AND file_path IS NOT NULL
        """,
        (session_id,),
    )
    files_modified = [row["file_path"] for row in cursor.fetchall()]

    # Get errors
    cursor.execute(
        """
        SELECT error_message
        FROM activities
        WHERE session_id = ? AND success = 0 AND error_message IS NOT NULL
        LIMIT 10
        """,
        (session_id,),
    )
    key_errors = [row["error_message"] for row in cursor.fetchall()]

    # Create summary record
    summary_id = generate_summary_id()
    cursor.execute(
        """
        INSERT INTO session_summaries (
            id, session_id, key_learnings, key_decisions, key_errors,
            files_modified, tools_used, total_activities,
            total_memories_created, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            summary_id,
            session_id,
            json.dumps(key_learnings) if key_learnings else None,
            None,  # key_decisions - could be extracted from memories
            json.dumps(key_errors) if key_errors else None,
            json.dumps(files_modified) if files_modified else None,
            json.dumps(tools_used) if tools_used else None,
            total_activities,
            total_memories,
            now,
        ),
    )

    conn.commit()
    return get_session(conn, session_id)


def get_recent_sessions(
    conn: sqlite3.Connection,
    project_path: Optional[str] = None,
    limit: int = 5,
) -> list[Session]:
    """Get recent sessions.

    Args:
        conn: Database connection
        project_path: Filter by project path
        limit: Maximum number of sessions

    Returns:
        List of recent sessions
    """
    cursor = conn.cursor()

    if project_path:
        cursor.execute(
            """
            SELECT * FROM sessions
            WHERE project_path = ?
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (project_path, limit),
        )
    else:
        cursor.execute(
            """
            SELECT * FROM sessions
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (limit,),
        )

    return [_row_to_session(row) for row in cursor.fetchall()]


def get_session_summary(
    conn: sqlite3.Connection,
    session_id: str,
) -> Optional[SessionSummary]:
    """Get session summary."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM session_summaries WHERE session_id = ?",
        (session_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None

    return SessionSummary(
        id=row["id"],
        session_id=row["session_id"],
        key_learnings=json.loads(row["key_learnings"]) if row["key_learnings"] else None,
        key_decisions=json.loads(row["key_decisions"]) if row["key_decisions"] else None,
        key_errors=json.loads(row["key_errors"]) if row["key_errors"] else None,
        files_modified=json.loads(row["files_modified"]) if row["files_modified"] else None,
        tools_used=json.loads(row["tools_used"]) if row["tools_used"] else None,
        total_activities=row["total_activities"],
        total_memories_created=row["total_memories_created"],
        created_at=row["created_at"],
    )


def _row_to_session(row: sqlite3.Row) -> Session:
    """Convert database row to Session object."""
    tags = row["tags"]
    if tags and isinstance(tags, str):
        tags = json.loads(tags)

    metadata = row["metadata"]
    if metadata and isinstance(metadata, str):
        metadata = json.loads(metadata)

    return Session(
        id=row["id"],
        project_path=row["project_path"],
        started_at=row["started_at"],
        ended_at=row["ended_at"],
        summary=row["summary"],
        tags=tags,
        metadata=metadata,
    )
