"""Memory model and CRUD operations."""

import json
import sqlite3
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator

from ..utils.ids import generate_memory_id
from ..utils.timestamps import now_iso


class MemoryBase(BaseModel):
    """Base memory model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    content: str = Field(..., description="The memory content", min_length=1)
    context: Optional[str] = Field(None, description="Additional context")
    tags: Optional[list[str]] = Field(default_factory=list, description="Tags for categorization")
    type: str = Field("general", description="Memory type")


class MemoryCreate(MemoryBase):
    """Input model for creating a memory."""

    importance: Optional[int] = Field(
        None, description="Importance score 1-100", ge=1, le=100
    )
    related_activity_id: Optional[str] = Field(None, description="Related activity ID")
    related_memory_ids: Optional[list[str]] = Field(
        default_factory=list, description="Related memory IDs"
    )

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        return list(v)


class MemoryUpdate(BaseModel):
    """Input model for updating a memory."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    content: Optional[str] = Field(None, description="New content")
    context: Optional[str] = Field(None, description="New context")
    tags: Optional[list[str]] = Field(None, description="Replace all tags")
    add_tags: Optional[list[str]] = Field(None, description="Tags to add")
    remove_tags: Optional[list[str]] = Field(None, description="Tags to remove")
    status: Optional[str] = Field(None, description="New status")
    importance: Optional[int] = Field(None, description="New importance", ge=1, le=100)


class Memory(MemoryBase):
    """Full memory model from database."""

    id: str
    created_at: str
    updated_at: str
    last_accessed: str
    last_verified: Optional[str] = None
    access_count: int = 0
    importance_score: float = 50.0
    manual_importance: Optional[int] = None
    status: str = "fresh"
    source_session_id: Optional[str] = None
    source_agent_id: Optional[str] = None
    source_activity_id: Optional[str] = None
    project_path: Optional[str] = None
    file_context: Optional[list[str]] = None
    has_embedding: bool = False
    metadata: Optional[dict[str, Any]] = None


def create_memory(
    conn: sqlite3.Connection,
    data: MemoryCreate,
    project_path: Optional[str] = None,
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Memory:
    """Create a new memory in the database.

    Args:
        conn: Database connection
        data: Memory creation data
        project_path: Current project path
        session_id: Current session ID
        agent_id: Current agent ID

    Returns:
        Created memory object
    """
    from ..categorization import detect_memory_type, suggest_tags

    memory_id = generate_memory_id()
    now = now_iso()

    # Auto-detect type if not specified or is default
    mem_type = data.type
    if mem_type == "general":
        mem_type = detect_memory_type(data.content, data.context)

    # Auto-suggest tags and merge with provided
    suggested = suggest_tags(data.content, data.context)
    tags = list(set((data.tags or []) + suggested))

    # Determine importance
    importance = float(data.importance) if data.importance else 50.0
    manual_importance = data.importance

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO memories (
            id, content, type, tags, context,
            created_at, updated_at, last_accessed,
            access_count, importance_score, manual_importance, status,
            source_session_id, source_agent_id, source_activity_id,
            project_path, has_embedding
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            memory_id,
            data.content,
            mem_type,
            json.dumps(tags),
            data.context,
            now,
            now,
            now,
            0,
            importance,
            manual_importance,
            "fresh",
            session_id,
            agent_id,
            data.related_activity_id,
            project_path,
            0,
        ),
    )
    conn.commit()

    return Memory(
        id=memory_id,
        content=data.content,
        type=mem_type,
        tags=tags,
        context=data.context,
        created_at=now,
        updated_at=now,
        last_accessed=now,
        access_count=0,
        importance_score=importance,
        manual_importance=manual_importance,
        status="fresh",
        source_session_id=session_id,
        source_activity_id=data.related_activity_id,
        project_path=project_path,
    )


def get_memory(conn: sqlite3.Connection, memory_id: str) -> Optional[Memory]:
    """Get a memory by ID.

    Args:
        conn: Database connection
        memory_id: Memory ID

    Returns:
        Memory object or None if not found
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
    row = cursor.fetchone()

    if not row:
        return None

    return _row_to_memory(row)


def update_memory(
    conn: sqlite3.Connection,
    memory_id: str,
    data: MemoryUpdate,
) -> Optional[Memory]:
    """Update a memory.

    Args:
        conn: Database connection
        memory_id: Memory ID
        data: Update data

    Returns:
        Updated memory or None if not found
    """
    memory = get_memory(conn, memory_id)
    if not memory:
        return None

    updates = []
    params = []

    if data.content is not None:
        updates.append("content = ?")
        params.append(data.content)

    if data.context is not None:
        updates.append("context = ?")
        params.append(data.context)

    if data.status is not None:
        updates.append("status = ?")
        params.append(data.status)

    if data.importance is not None:
        updates.append("manual_importance = ?")
        params.append(data.importance)
        updates.append("importance_score = ?")
        params.append(float(data.importance))

    # Handle tags
    current_tags = memory.tags or []
    new_tags = current_tags

    if data.tags is not None:
        new_tags = data.tags
    else:
        if data.add_tags:
            new_tags = list(set(current_tags + data.add_tags))
        if data.remove_tags:
            new_tags = [t for t in new_tags if t not in data.remove_tags]

    if new_tags != current_tags:
        updates.append("tags = ?")
        params.append(json.dumps(new_tags))

    if updates:
        updates.append("updated_at = ?")
        params.append(now_iso())
        params.append(memory_id)

        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE memories SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()

    return get_memory(conn, memory_id)


def delete_memory(conn: sqlite3.Connection, memory_id: str) -> bool:
    """Delete a memory.

    Args:
        conn: Database connection
        memory_id: Memory ID

    Returns:
        True if deleted, False if not found
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    conn.commit()
    return cursor.rowcount > 0


def list_memories(
    conn: sqlite3.Connection,
    type_filter: Optional[str] = None,
    tags_filter: Optional[list[str]] = None,
    status_filter: Optional[str] = None,
    sort_by: str = "last_accessed",
    sort_order: str = "desc",
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Memory], int]:
    """List memories with filters.

    Returns:
        Tuple of (memories list, total count)
    """
    where_clauses = []
    params: list[Any] = []

    if type_filter:
        where_clauses.append("type = ?")
        params.append(type_filter)

    if status_filter:
        where_clauses.append("status = ?")
        params.append(status_filter)

    if tags_filter:
        # Match any of the tags
        tag_conditions = []
        for tag in tags_filter:
            tag_conditions.append("tags LIKE ?")
            params.append(f'%"{tag}"%')
        where_clauses.append(f"({' OR '.join(tag_conditions)})")

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    # Validate sort column
    valid_sorts = ["last_accessed", "created_at", "importance_score", "access_count"]
    if sort_by not in valid_sorts:
        sort_by = "last_accessed"

    order = "DESC" if sort_order.lower() == "desc" else "ASC"

    # Get total count
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM memories {where_sql}", params)
    total = cursor.fetchone()[0]

    # Get page
    params_page = params + [limit, offset]
    cursor.execute(
        f"""
        SELECT * FROM memories {where_sql}
        ORDER BY {sort_by} {order}
        LIMIT ? OFFSET ?
        """,
        params_page,
    )

    memories = [_row_to_memory(row) for row in cursor.fetchall()]
    return memories, total


def touch_memory(conn: sqlite3.Connection, memory_id: str) -> None:
    """Update last_accessed and increment access_count."""
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE memories
        SET last_accessed = ?, access_count = access_count + 1
        WHERE id = ?
        """,
        (now_iso(), memory_id),
    )
    conn.commit()


def _row_to_memory(row: sqlite3.Row) -> Memory:
    """Convert database row to Memory object."""
    tags = row["tags"]
    if tags and isinstance(tags, str):
        tags = json.loads(tags)

    file_context = row["file_context"]
    if file_context and isinstance(file_context, str):
        file_context = json.loads(file_context)

    metadata = row["metadata"]
    if metadata and isinstance(metadata, str):
        metadata = json.loads(metadata)

    return Memory(
        id=row["id"],
        content=row["content"],
        type=row["type"],
        tags=tags or [],
        context=row["context"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_accessed=row["last_accessed"],
        last_verified=row["last_verified"],
        access_count=row["access_count"],
        importance_score=row["importance_score"],
        manual_importance=row["manual_importance"],
        status=row["status"],
        source_session_id=row["source_session_id"],
        source_agent_id=row["source_agent_id"],
        source_activity_id=row["source_activity_id"],
        project_path=row["project_path"],
        file_context=file_context,
        has_embedding=bool(row["has_embedding"]),
        metadata=metadata,
    )
