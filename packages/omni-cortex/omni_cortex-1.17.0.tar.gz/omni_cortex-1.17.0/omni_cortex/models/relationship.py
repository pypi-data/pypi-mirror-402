"""Memory relationship model and operations."""

import json
import sqlite3
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict

from ..utils.ids import generate_relationship_id
from ..utils.timestamps import now_iso


class MemoryRelationship(BaseModel):
    """Memory relationship model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    id: str
    source_memory_id: str
    target_memory_id: str
    relationship_type: str  # related_to, supersedes, derived_from, contradicts
    strength: float = 1.0
    created_at: str
    metadata: Optional[dict[str, Any]] = None


class LinkMemoriesInput(BaseModel):
    """Input for linking two memories."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    source_id: str = Field(..., description="Source memory ID")
    target_id: str = Field(..., description="Target memory ID")
    relationship_type: str = Field(
        ...,
        description="Relationship type: related_to, supersedes, derived_from, contradicts",
    )
    strength: float = Field(1.0, description="Relationship strength 0.0-1.0", ge=0.0, le=1.0)


VALID_RELATIONSHIP_TYPES = ["related_to", "supersedes", "derived_from", "contradicts"]


def create_relationship(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
    relationship_type: str,
    strength: float = 1.0,
) -> Optional[MemoryRelationship]:
    """Create a relationship between two memories.

    Args:
        conn: Database connection
        source_id: Source memory ID
        target_id: Target memory ID
        relationship_type: Type of relationship
        strength: Relationship strength

    Returns:
        Created relationship or None if memories don't exist
    """
    if relationship_type not in VALID_RELATIONSHIP_TYPES:
        raise ValueError(f"Invalid relationship type: {relationship_type}")

    # Verify both memories exist
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM memories WHERE id IN (?, ?)", (source_id, target_id))
    found = [row[0] for row in cursor.fetchall()]
    if len(found) != 2:
        return None

    rel_id = generate_relationship_id()
    now = now_iso()

    try:
        cursor.execute(
            """
            INSERT INTO memory_relationships (
                id, source_memory_id, target_memory_id,
                relationship_type, strength, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (rel_id, source_id, target_id, relationship_type, strength, now),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Relationship already exists
        cursor.execute(
            """
            SELECT * FROM memory_relationships
            WHERE source_memory_id = ? AND target_memory_id = ? AND relationship_type = ?
            """,
            (source_id, target_id, relationship_type),
        )
        row = cursor.fetchone()
        if row:
            return _row_to_relationship(row)
        return None

    return MemoryRelationship(
        id=rel_id,
        source_memory_id=source_id,
        target_memory_id=target_id,
        relationship_type=relationship_type,
        strength=strength,
        created_at=now,
    )


def get_relationships(
    conn: sqlite3.Connection,
    memory_id: str,
    as_source: bool = True,
    as_target: bool = True,
) -> list[MemoryRelationship]:
    """Get all relationships for a memory.

    Args:
        conn: Database connection
        memory_id: Memory ID
        as_source: Include relationships where memory is source
        as_target: Include relationships where memory is target

    Returns:
        List of relationships
    """
    cursor = conn.cursor()
    relationships = []

    if as_source:
        cursor.execute(
            "SELECT * FROM memory_relationships WHERE source_memory_id = ?",
            (memory_id,),
        )
        relationships.extend([_row_to_relationship(row) for row in cursor.fetchall()])

    if as_target:
        cursor.execute(
            "SELECT * FROM memory_relationships WHERE target_memory_id = ?",
            (memory_id,),
        )
        relationships.extend([_row_to_relationship(row) for row in cursor.fetchall()])

    return relationships


def delete_relationship(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
    relationship_type: Optional[str] = None,
) -> int:
    """Delete relationships between memories.

    Args:
        conn: Database connection
        source_id: Source memory ID
        target_id: Target memory ID
        relationship_type: Optional type filter

    Returns:
        Number of relationships deleted
    """
    cursor = conn.cursor()

    if relationship_type:
        cursor.execute(
            """
            DELETE FROM memory_relationships
            WHERE source_memory_id = ? AND target_memory_id = ? AND relationship_type = ?
            """,
            (source_id, target_id, relationship_type),
        )
    else:
        cursor.execute(
            """
            DELETE FROM memory_relationships
            WHERE source_memory_id = ? AND target_memory_id = ?
            """,
            (source_id, target_id),
        )

    conn.commit()
    return cursor.rowcount


def _row_to_relationship(row: sqlite3.Row) -> MemoryRelationship:
    """Convert database row to MemoryRelationship object."""
    metadata = row["metadata"]
    if metadata and isinstance(metadata, str):
        metadata = json.loads(metadata)

    return MemoryRelationship(
        id=row["id"],
        source_memory_id=row["source_memory_id"],
        target_memory_id=row["target_memory_id"],
        relationship_type=row["relationship_type"],
        strength=row["strength"],
        created_at=row["created_at"],
        metadata=metadata,
    )
