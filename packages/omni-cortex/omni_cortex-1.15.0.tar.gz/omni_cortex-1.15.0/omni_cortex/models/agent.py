"""Agent model and CRUD operations."""

import json
import sqlite3
from typing import Optional, Any
from pydantic import BaseModel

from ..utils.timestamps import now_iso


class Agent(BaseModel):
    """Agent model from database."""

    id: str
    name: Optional[str] = None
    type: str = "main"  # main, subagent, tool
    first_seen: str
    last_seen: str
    total_activities: int = 0
    metadata: Optional[dict[str, Any]] = None


def get_or_create_agent(
    conn: sqlite3.Connection,
    agent_id: str,
    agent_type: str = "main",
    name: Optional[str] = None,
) -> Agent:
    """Get an existing agent or create a new one.

    Args:
        conn: Database connection
        agent_id: Agent ID
        agent_type: Type of agent (main, subagent, tool)
        name: Optional agent name

    Returns:
        Agent object
    """
    now = now_iso()
    cursor = conn.cursor()

    # Try to get existing
    cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
    row = cursor.fetchone()

    if row:
        # Update last_seen
        cursor.execute(
            "UPDATE agents SET last_seen = ? WHERE id = ?",
            (now, agent_id),
        )
        conn.commit()
        return _row_to_agent(row)

    # Create new
    cursor.execute(
        """
        INSERT INTO agents (id, name, type, first_seen, last_seen, total_activities)
        VALUES (?, ?, ?, ?, ?, 0)
        """,
        (agent_id, name, agent_type, now, now),
    )
    conn.commit()

    return Agent(
        id=agent_id,
        name=name,
        type=agent_type,
        first_seen=now,
        last_seen=now,
        total_activities=0,
    )


def get_agent(conn: sqlite3.Connection, agent_id: str) -> Optional[Agent]:
    """Get an agent by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
    row = cursor.fetchone()
    return _row_to_agent(row) if row else None


def list_agents(
    conn: sqlite3.Connection,
    agent_type: Optional[str] = None,
    limit: int = 50,
) -> list[Agent]:
    """List agents with optional type filter."""
    cursor = conn.cursor()

    if agent_type:
        cursor.execute(
            """
            SELECT * FROM agents
            WHERE type = ?
            ORDER BY last_seen DESC
            LIMIT ?
            """,
            (agent_type, limit),
        )
    else:
        cursor.execute(
            """
            SELECT * FROM agents
            ORDER BY last_seen DESC
            LIMIT ?
            """,
            (limit,),
        )

    return [_row_to_agent(row) for row in cursor.fetchall()]


def increment_agent_activities(conn: sqlite3.Connection, agent_id: str) -> None:
    """Increment an agent's activity count."""
    now = now_iso()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE agents
        SET total_activities = total_activities + 1, last_seen = ?
        WHERE id = ?
        """,
        (now, agent_id),
    )
    conn.commit()


def _row_to_agent(row: sqlite3.Row) -> Agent:
    """Convert database row to Agent object."""
    metadata = row["metadata"]
    if metadata and isinstance(metadata, str):
        metadata = json.loads(metadata)

    return Agent(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        first_seen=row["first_seen"],
        last_seen=row["last_seen"],
        total_activities=row["total_activities"],
        metadata=metadata,
    )
