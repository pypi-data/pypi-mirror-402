"""Database query functions for reading omni-cortex SQLite databases."""

import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from models import Activity, FilterParams, Memory, MemoryStats, MemoryUpdate, Session, TimelineEntry


def get_connection(db_path: str) -> sqlite3.Connection:
    """Get a read-only connection to the database."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def get_write_connection(db_path: str) -> sqlite3.Connection:
    """Get a writable connection to the database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_migrations(db_path: str) -> None:
    """Ensure database has latest migrations applied.

    This function checks for and applies any missing schema updates,
    including command analytics columns and natural language summary columns.
    """
    conn = get_write_connection(db_path)

    # Check if activities table exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='activities'"
    ).fetchone()

    if not table_check:
        conn.close()
        return

    # Check available columns
    columns = conn.execute("PRAGMA table_info(activities)").fetchall()
    column_names = {col[1] for col in columns}

    migrations_applied = []

    # Migration v1.1: Command analytics columns
    if "command_name" not in column_names:
        conn.executescript("""
            ALTER TABLE activities ADD COLUMN command_name TEXT;
            ALTER TABLE activities ADD COLUMN command_scope TEXT;
            ALTER TABLE activities ADD COLUMN mcp_server TEXT;
            ALTER TABLE activities ADD COLUMN skill_name TEXT;

            CREATE INDEX IF NOT EXISTS idx_activities_command ON activities(command_name);
            CREATE INDEX IF NOT EXISTS idx_activities_mcp ON activities(mcp_server);
            CREATE INDEX IF NOT EXISTS idx_activities_skill ON activities(skill_name);
        """)
        migrations_applied.append("v1.1: command analytics columns")

    # Migration v1.2: Natural language summary columns
    if "summary" not in column_names:
        conn.executescript("""
            ALTER TABLE activities ADD COLUMN summary TEXT;
            ALTER TABLE activities ADD COLUMN summary_detail TEXT;
        """)
        migrations_applied.append("v1.2: summary columns")

    if migrations_applied:
        conn.commit()
        print(f"[Database] Applied migrations: {', '.join(migrations_applied)}")

    conn.close()


def parse_tags(tags_str: Optional[str]) -> list[str]:
    """Parse tags from JSON string."""
    if not tags_str:
        return []
    try:
        tags = json.loads(tags_str)
        return tags if isinstance(tags, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def get_memories(db_path: str, filters: FilterParams) -> list[Memory]:
    """Get memories with filtering, sorting, and pagination."""
    conn = get_connection(db_path)

    # Build query
    query = "SELECT * FROM memories WHERE 1=1"
    params: list = []

    if filters.memory_type:
        query += " AND type = ?"
        params.append(filters.memory_type)

    if filters.status:
        query += " AND status = ?"
        params.append(filters.status)

    if filters.min_importance is not None:
        query += " AND importance_score >= ?"
        params.append(filters.min_importance)

    if filters.max_importance is not None:
        query += " AND importance_score <= ?"
        params.append(filters.max_importance)

    if filters.search:
        query += " AND (content LIKE ? OR context LIKE ?)"
        search_term = f"%{filters.search}%"
        params.extend([search_term, search_term])

    # Sorting
    valid_sort_columns = ["created_at", "last_accessed", "importance_score", "access_count"]
    sort_by = filters.sort_by if filters.sort_by in valid_sort_columns else "last_accessed"
    sort_order = "DESC" if filters.sort_order.lower() == "desc" else "ASC"
    query += f" ORDER BY {sort_by} {sort_order}"

    # Pagination
    query += " LIMIT ? OFFSET ?"
    params.extend([filters.limit, filters.offset])

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    memories = []
    for row in rows:
        # Parse tags from JSON string
        tags = parse_tags(row["tags"])

        memories.append(
            Memory(
                id=row["id"],
                content=row["content"],
                context=row["context"],
                type=row["type"],
                status=row["status"] or "fresh",
                importance_score=int(row["importance_score"] or 50),
                access_count=row["access_count"] or 0,
                created_at=datetime.fromisoformat(row["created_at"]),
                last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
                tags=tags,
            )
        )

    conn.close()
    return memories


def get_memory_by_id(db_path: str, memory_id: str) -> Optional[Memory]:
    """Get a single memory by ID."""
    conn = get_connection(db_path)

    cursor = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    # Parse tags from JSON string
    tags = parse_tags(row["tags"])

    memory = Memory(
        id=row["id"],
        content=row["content"],
        context=row["context"],
        type=row["type"],
        status=row["status"] or "fresh",
        importance_score=int(row["importance_score"] or 50),
        access_count=row["access_count"] or 0,
        created_at=datetime.fromisoformat(row["created_at"]),
        last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
        tags=tags,
    )

    conn.close()
    return memory


def get_memory_stats(db_path: str) -> MemoryStats:
    """Get statistics about memories in the database."""
    conn = get_connection(db_path)

    # Total count
    total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

    # By type
    type_cursor = conn.execute("SELECT type, COUNT(*) as count FROM memories GROUP BY type")
    by_type = {row["type"]: row["count"] for row in type_cursor.fetchall()}

    # By status
    status_cursor = conn.execute("SELECT status, COUNT(*) as count FROM memories GROUP BY status")
    by_status = {(row["status"] or "fresh"): row["count"] for row in status_cursor.fetchall()}

    # Average importance
    avg_cursor = conn.execute("SELECT AVG(importance_score) FROM memories")
    avg_importance = avg_cursor.fetchone()[0] or 0.0

    # Total access count
    access_cursor = conn.execute("SELECT SUM(access_count) FROM memories")
    total_access = access_cursor.fetchone()[0] or 0

    # Tags with counts - extract from JSON column
    tags_cursor = conn.execute("SELECT tags FROM memories WHERE tags IS NOT NULL AND tags != ''")
    tag_counter: Counter = Counter()
    for row in tags_cursor.fetchall():
        tags = parse_tags(row["tags"])
        tag_counter.update(tags)

    tags = [{"name": name, "count": count} for name, count in tag_counter.most_common(50)]

    conn.close()

    return MemoryStats(
        total_count=total,
        by_type=by_type,
        by_status=by_status,
        avg_importance=round(avg_importance, 1),
        total_access_count=total_access,
        tags=tags,
    )


def get_activities(
    db_path: str,
    event_type: Optional[str] = None,
    tool_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Activity]:
    """Get activity log entries with all available fields."""
    conn = get_connection(db_path)

    # Check available columns for backward compatibility
    columns = conn.execute("PRAGMA table_info(activities)").fetchall()
    column_names = {col[1] for col in columns}

    query = "SELECT * FROM activities WHERE 1=1"
    params: list = []

    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)

    if tool_name:
        query += " AND tool_name = ?"
        params.append(tool_name)

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = conn.execute(query, params)
    activities = []

    for row in cursor.fetchall():
        # Parse timestamp - handle both with and without timezone
        ts_str = row["timestamp"]
        try:
            ts = datetime.fromisoformat(ts_str)
        except ValueError:
            # Fallback for edge cases
            ts = datetime.now()

        activity_data = {
            "id": row["id"],
            "session_id": row["session_id"],
            "event_type": row["event_type"],
            "tool_name": row["tool_name"],
            "tool_input": row["tool_input"],
            "tool_output": row["tool_output"],
            "success": bool(row["success"]),
            "error_message": row["error_message"],
            "duration_ms": row["duration_ms"],
            "file_path": row["file_path"],
            "timestamp": ts,
        }

        # Add command analytics fields if available
        if "command_name" in column_names:
            activity_data["command_name"] = row["command_name"]
        if "command_scope" in column_names:
            activity_data["command_scope"] = row["command_scope"]
        if "mcp_server" in column_names:
            activity_data["mcp_server"] = row["mcp_server"]
        if "skill_name" in column_names:
            activity_data["skill_name"] = row["skill_name"]

        # Add summary fields if available
        if "summary" in column_names:
            activity_data["summary"] = row["summary"]
        if "summary_detail" in column_names:
            activity_data["summary_detail"] = row["summary_detail"]

        activities.append(Activity(**activity_data))

    conn.close()
    return activities


def get_timeline(
    db_path: str,
    hours: int = 24,
    include_memories: bool = True,
    include_activities: bool = True,
) -> list[TimelineEntry]:
    """Get a timeline of memories and activities."""
    conn = get_connection(db_path)
    since = datetime.now() - timedelta(hours=hours)
    since_str = since.isoformat()

    entries: list[TimelineEntry] = []

    if include_memories:
        cursor = conn.execute(
            "SELECT * FROM memories WHERE created_at >= ? ORDER BY created_at DESC",
            (since_str,),
        )
        for row in cursor.fetchall():
            entries.append(
                TimelineEntry(
                    timestamp=datetime.fromisoformat(row["created_at"]),
                    entry_type="memory",
                    data={
                        "id": row["id"],
                        "content": row["content"][:200] + "..." if len(row["content"]) > 200 else row["content"],
                        "type": row["type"],
                        "importance": row["importance_score"],
                    },
                )
            )

    if include_activities:
        cursor = conn.execute(
            "SELECT * FROM activities WHERE timestamp >= ? ORDER BY timestamp DESC",
            (since_str,),
        )
        for row in cursor.fetchall():
            entries.append(
                TimelineEntry(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    entry_type="activity",
                    data={
                        "id": row["id"],
                        "event_type": row["event_type"],
                        "tool_name": row["tool_name"],
                        "success": bool(row["success"]),
                        "duration_ms": row["duration_ms"],
                    },
                )
            )

    # Sort by timestamp descending
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    conn.close()
    return entries


def get_sessions(db_path: str, limit: int = 20) -> list[Session]:
    """Get recent sessions."""
    conn = get_connection(db_path)

    cursor = conn.execute(
        """
        SELECT s.*, COUNT(a.id) as activity_count
        FROM sessions s
        LEFT JOIN activities a ON s.id = a.session_id
        GROUP BY s.id
        ORDER BY s.started_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    sessions = []
    for row in cursor.fetchall():
        sessions.append(
            Session(
                id=row["id"],
                project_path=row["project_path"],
                started_at=datetime.fromisoformat(row["started_at"]),
                ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
                summary=row["summary"],
                activity_count=row["activity_count"],
            )
        )

    conn.close()
    return sessions


def get_all_tags(db_path: str) -> list[dict]:
    """Get all tags with their usage counts."""
    conn = get_connection(db_path)

    # Extract tags from JSON column
    cursor = conn.execute("SELECT tags FROM memories WHERE tags IS NOT NULL AND tags != ''")
    tag_counter: Counter = Counter()
    for row in cursor.fetchall():
        tags = parse_tags(row["tags"])
        tag_counter.update(tags)

    tags = [{"name": name, "count": count} for name, count in tag_counter.most_common()]

    conn.close()
    return tags


def get_type_distribution(db_path: str) -> dict[str, int]:
    """Get memory type distribution."""
    conn = get_connection(db_path)

    cursor = conn.execute("SELECT type, COUNT(*) as count FROM memories GROUP BY type")
    distribution = {row["type"]: row["count"] for row in cursor.fetchall()}

    conn.close()
    return distribution


def search_memories(db_path: str, query: str, limit: int = 20) -> list[Memory]:
    """Search memories using FTS if available, otherwise LIKE."""
    conn = get_connection(db_path)

    # Check if FTS table exists
    fts_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='memories_fts'"
    ).fetchone()

    if fts_check:
        # Use FTS search - FTS5 uses rowid to match the memories table rowid
        # Escape special FTS5 characters and wrap in quotes for phrase search
        safe_query = query.replace('"', '""')
        try:
            cursor = conn.execute(
                """
                SELECT m.* FROM memories m
                JOIN memories_fts fts ON m.rowid = fts.rowid
                WHERE memories_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (f'"{safe_query}"', limit),
            )
        except sqlite3.OperationalError:
            # Fallback if FTS query fails
            search_term = f"%{query}%"
            cursor = conn.execute(
                """
                SELECT * FROM memories
                WHERE content LIKE ? OR context LIKE ?
                ORDER BY importance_score DESC
                LIMIT ?
                """,
                (search_term, search_term, limit),
            )
    else:
        # Fallback to LIKE
        search_term = f"%{query}%"
        cursor = conn.execute(
            """
            SELECT * FROM memories
            WHERE content LIKE ? OR context LIKE ?
            ORDER BY importance_score DESC
            LIMIT ?
            """,
            (search_term, search_term, limit),
        )

    memories = []
    for row in cursor.fetchall():
        # Parse tags from JSON string
        tags = parse_tags(row["tags"])

        memories.append(
            Memory(
                id=row["id"],
                content=row["content"],
                context=row["context"],
                type=row["type"],
                status=row["status"] or "fresh",
                importance_score=int(row["importance_score"] or 50),
                access_count=row["access_count"] or 0,
                created_at=datetime.fromisoformat(row["created_at"]),
                last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
                tags=tags,
            )
        )

    conn.close()
    return memories


def update_memory(db_path: str, memory_id: str, updates: MemoryUpdate) -> Optional[Memory]:
    """Update a memory and return the updated record."""
    conn = get_write_connection(db_path)

    # Build update query dynamically based on provided fields
    update_fields = []
    params = []

    if updates.content is not None:
        update_fields.append("content = ?")
        params.append(updates.content)

    if updates.context is not None:
        update_fields.append("context = ?")
        params.append(updates.context)

    if updates.memory_type is not None:
        update_fields.append("type = ?")
        params.append(updates.memory_type)

    if updates.status is not None:
        update_fields.append("status = ?")
        params.append(updates.status)

    if updates.importance_score is not None:
        update_fields.append("importance_score = ?")
        params.append(updates.importance_score)

    if updates.tags is not None:
        update_fields.append("tags = ?")
        params.append(json.dumps(updates.tags))

    if not update_fields:
        conn.close()
        return get_memory_by_id(db_path, memory_id)

    # Add updated timestamp
    update_fields.append("last_accessed = ?")
    params.append(datetime.now().isoformat())

    # Add memory_id to params
    params.append(memory_id)

    query = f"UPDATE memories SET {', '.join(update_fields)} WHERE id = ?"
    cursor = conn.execute(query, params)
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        return None

    conn.close()
    return get_memory_by_id(db_path, memory_id)


def delete_memory(db_path: str, memory_id: str) -> bool:
    """Delete a memory by ID. Returns True if deleted, False if not found."""
    conn = get_write_connection(db_path)

    # Also delete related entries in memory_relationships
    conn.execute(
        "DELETE FROM memory_relationships WHERE source_id = ? OR target_id = ?",
        (memory_id, memory_id),
    )

    cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    conn.commit()

    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


# --- Stats Functions for Dashboard Charts ---


def get_activity_heatmap(db_path: str, days: int = 90) -> list[dict]:
    """Get activity counts grouped by day for heatmap visualization."""
    conn = get_connection(db_path)
    query = """
        SELECT date(timestamp) as date, COUNT(*) as count
        FROM activities
        WHERE timestamp >= date('now', ?)
        GROUP BY date(timestamp)
        ORDER BY date
    """
    cursor = conn.execute(query, (f'-{days} days',))
    result = [{"date": row["date"], "count": row["count"]} for row in cursor.fetchall()]
    conn.close()
    return result


def get_tool_usage(db_path: str, limit: int = 10) -> list[dict]:
    """Get tool usage statistics with success rates."""
    conn = get_connection(db_path)
    query = """
        SELECT
            tool_name,
            COUNT(*) as count,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
        FROM activities
        WHERE tool_name IS NOT NULL AND tool_name != ''
        GROUP BY tool_name
        ORDER BY count DESC
        LIMIT ?
    """
    cursor = conn.execute(query, (limit,))
    result = [
        {
            "tool_name": row["tool_name"],
            "count": row["count"],
            "success_rate": round(row["success_rate"], 2) if row["success_rate"] else 1.0,
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return result


def get_memory_growth(db_path: str, days: int = 30) -> list[dict]:
    """Get memory creation over time with cumulative totals."""
    conn = get_connection(db_path)
    query = """
        WITH daily_counts AS (
            SELECT date(created_at) as date, COUNT(*) as count
            FROM memories
            WHERE created_at >= date('now', ?)
            GROUP BY date(created_at)
        )
        SELECT
            date,
            count,
            SUM(count) OVER (ORDER BY date) as cumulative
        FROM daily_counts
        ORDER BY date
    """
    cursor = conn.execute(query, (f'-{days} days',))
    result = [
        {"date": row["date"], "count": row["count"], "cumulative": row["cumulative"]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return result


def get_recent_sessions(db_path: str, limit: int = 5) -> list[dict]:
    """Get recent sessions with activity counts and memory counts."""
    conn = get_connection(db_path)
    query = """
        SELECT
            s.id,
            s.project_path,
            s.started_at,
            s.ended_at,
            s.summary,
            COUNT(DISTINCT a.id) as activity_count
        FROM sessions s
        LEFT JOIN activities a ON a.session_id = s.id
        GROUP BY s.id
        ORDER BY s.started_at DESC
        LIMIT ?
    """
    cursor = conn.execute(query, (limit,))
    result = [
        {
            "id": row["id"],
            "project_path": row["project_path"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
            "summary": row["summary"],
            "activity_count": row["activity_count"],
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return result


def bulk_update_memory_status(db_path: str, memory_ids: list[str], status: str) -> int:
    """Update status for multiple memories. Returns count updated."""
    if not memory_ids:
        return 0
    conn = get_write_connection(db_path)
    placeholders = ','.join('?' * len(memory_ids))
    query = f"UPDATE memories SET status = ?, last_accessed = datetime('now') WHERE id IN ({placeholders})"
    cursor = conn.execute(query, [status] + memory_ids)
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count


def get_memories_needing_review(db_path: str, days_threshold: int = 30, limit: int = 50) -> list[Memory]:
    """Get memories that haven't been accessed recently and may need review."""
    conn = get_connection(db_path)
    query = """
        SELECT * FROM memories
        WHERE last_accessed < date('now', ?)
           OR last_accessed IS NULL
        ORDER BY last_accessed ASC NULLS FIRST, importance_score DESC
        LIMIT ?
    """
    cursor = conn.execute(query, (f'-{days_threshold} days', limit))

    memories = []
    for row in cursor.fetchall():
        tags = parse_tags(row["tags"])
        memories.append(
            Memory(
                id=row["id"],
                content=row["content"],
                context=row["context"],
                type=row["type"],
                status=row["status"] or "fresh",
                importance_score=int(row["importance_score"] or 50),
                access_count=row["access_count"] or 0,
                created_at=datetime.fromisoformat(row["created_at"]),
                last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
                tags=tags,
            )
        )

    conn.close()
    return memories


def get_relationships(db_path: str, memory_id: Optional[str] = None) -> list[dict]:
    """Get memory relationships for graph visualization."""
    conn = get_connection(db_path)

    # Check if memory_relationships table exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_relationships'"
    ).fetchone()

    if not table_check:
        conn.close()
        return []

    query = """
        SELECT
            r.source_memory_id as source_id,
            r.target_memory_id as target_id,
            r.relationship_type,
            r.strength,
            ms.content as source_content,
            ms.type as source_type,
            mt.content as target_content,
            mt.type as target_type
        FROM memory_relationships r
        JOIN memories ms ON r.source_memory_id = ms.id
        JOIN memories mt ON r.target_memory_id = mt.id
    """

    try:
        if memory_id:
            query += " WHERE r.source_memory_id = ? OR r.target_memory_id = ?"
            cursor = conn.execute(query, (memory_id, memory_id))
        else:
            cursor = conn.execute(query)

        result = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"[Database] Error querying relationships: {e}")
        result = []
    finally:
        conn.close()

    return result


def get_relationship_graph(db_path: str, center_id: Optional[str] = None, depth: int = 2) -> dict:
    """Get graph data with nodes and edges for D3 visualization."""
    relationships = get_relationships(db_path, center_id)

    nodes = {}
    edges = []

    for rel in relationships:
        # Add source node
        if rel["source_id"] not in nodes:
            nodes[rel["source_id"]] = {
                "id": rel["source_id"],
                "content": rel["source_content"][:100] if rel["source_content"] else "",
                "type": rel["source_type"],
            }
        # Add target node
        if rel["target_id"] not in nodes:
            nodes[rel["target_id"]] = {
                "id": rel["target_id"],
                "content": rel["target_content"][:100] if rel["target_content"] else "",
                "type": rel["target_type"],
            }
        # Add edge
        edges.append({
            "source": rel["source_id"],
            "target": rel["target_id"],
            "type": rel["relationship_type"],
            "strength": rel["strength"] or 1.0,
        })

    return {"nodes": list(nodes.values()), "edges": edges}


# --- Command Analytics Functions ---


def get_command_usage(db_path: str, scope: Optional[str] = None, days: int = 30) -> list[dict]:
    """Get slash command usage statistics aggregated by command_name.

    Args:
        db_path: Path to database
        scope: Filter by scope ('universal', 'project', or None for all)
        days: Number of days to look back

    Returns:
        List of command usage entries with counts and success rates
    """
    conn = get_connection(db_path)

    # Check if command_name column exists
    columns = conn.execute("PRAGMA table_info(activities)").fetchall()
    column_names = [col[1] for col in columns]
    if "command_name" not in column_names:
        conn.close()
        return []

    query = """
        SELECT
            command_name,
            command_scope,
            COUNT(*) as count,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate,
            AVG(duration_ms) as avg_duration_ms
        FROM activities
        WHERE command_name IS NOT NULL
          AND command_name != ''
          AND timestamp >= date('now', ?)
    """
    params = [f'-{days} days']

    if scope:
        query += " AND command_scope = ?"
        params.append(scope)

    query += " GROUP BY command_name, command_scope ORDER BY count DESC"

    cursor = conn.execute(query, params)
    result = [
        {
            "command_name": row["command_name"],
            "command_scope": row["command_scope"] or "unknown",
            "count": row["count"],
            "success_rate": round(row["success_rate"], 2) if row["success_rate"] else 1.0,
            "avg_duration_ms": round(row["avg_duration_ms"]) if row["avg_duration_ms"] else None,
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return result


def get_skill_usage(db_path: str, scope: Optional[str] = None, days: int = 30) -> list[dict]:
    """Get skill usage statistics aggregated by skill_name.

    Args:
        db_path: Path to database
        scope: Filter by scope ('universal', 'project', or None for all)
        days: Number of days to look back

    Returns:
        List of skill usage entries with counts and success rates
    """
    conn = get_connection(db_path)

    # Check if skill_name column exists
    columns = conn.execute("PRAGMA table_info(activities)").fetchall()
    column_names = [col[1] for col in columns]
    if "skill_name" not in column_names:
        conn.close()
        return []

    query = """
        SELECT
            skill_name,
            command_scope,
            COUNT(*) as count,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate,
            AVG(duration_ms) as avg_duration_ms
        FROM activities
        WHERE skill_name IS NOT NULL
          AND skill_name != ''
          AND timestamp >= date('now', ?)
    """
    params = [f'-{days} days']

    if scope:
        query += " AND command_scope = ?"
        params.append(scope)

    query += " GROUP BY skill_name, command_scope ORDER BY count DESC"

    cursor = conn.execute(query, params)
    result = [
        {
            "skill_name": row["skill_name"],
            "skill_scope": row["command_scope"] or "unknown",
            "count": row["count"],
            "success_rate": round(row["success_rate"], 2) if row["success_rate"] else 1.0,
            "avg_duration_ms": round(row["avg_duration_ms"]) if row["avg_duration_ms"] else None,
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return result


def get_mcp_usage(db_path: str, days: int = 30) -> list[dict]:
    """Get MCP server usage statistics.

    Args:
        db_path: Path to database
        days: Number of days to look back

    Returns:
        List of MCP server usage entries with tool counts and call totals
    """
    conn = get_connection(db_path)

    # Check if mcp_server column exists
    columns = conn.execute("PRAGMA table_info(activities)").fetchall()
    column_names = [col[1] for col in columns]
    if "mcp_server" not in column_names:
        conn.close()
        return []

    query = """
        SELECT
            mcp_server,
            COUNT(DISTINCT tool_name) as tool_count,
            COUNT(*) as total_calls,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
        FROM activities
        WHERE mcp_server IS NOT NULL
          AND mcp_server != ''
          AND timestamp >= date('now', ?)
        GROUP BY mcp_server
        ORDER BY total_calls DESC
    """
    cursor = conn.execute(query, (f'-{days} days',))
    result = [
        {
            "mcp_server": row["mcp_server"],
            "tool_count": row["tool_count"],
            "total_calls": row["total_calls"],
            "success_rate": round(row["success_rate"], 2) if row["success_rate"] else 1.0,
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return result


def get_activity_detail(db_path: str, activity_id: str) -> Optional[dict]:
    """Get full activity details including complete input/output.

    Args:
        db_path: Path to database
        activity_id: Activity ID

    Returns:
        Full activity details or None if not found
    """
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    # Get column names for safe access
    column_names = [description[0] for description in cursor.description]

    result = {
        "id": row["id"],
        "session_id": row["session_id"],
        "event_type": row["event_type"],
        "tool_name": row["tool_name"],
        "tool_input_full": row["tool_input"],
        "tool_output_full": row["tool_output"],
        "success": bool(row["success"]),
        "error_message": row["error_message"],
        "duration_ms": row["duration_ms"],
        "file_path": row["file_path"],
        "timestamp": row["timestamp"],
    }

    # Add command analytics fields if they exist
    if "command_name" in column_names:
        result["command_name"] = row["command_name"]
    if "command_scope" in column_names:
        result["command_scope"] = row["command_scope"]
    if "mcp_server" in column_names:
        result["mcp_server"] = row["mcp_server"]
    if "skill_name" in column_names:
        result["skill_name"] = row["skill_name"]

    # Add summary fields if they exist
    if "summary" in column_names:
        result["summary"] = row["summary"]
    if "summary_detail" in column_names:
        result["summary_detail"] = row["summary_detail"]

    conn.close()
    return result


def create_memory(
    db_path: str,
    content: str,
    memory_type: str = "other",
    context: Optional[str] = None,
    tags: Optional[list[str]] = None,
    importance_score: int = 50,
    related_memory_ids: Optional[list[str]] = None,
) -> str:
    """Create a new memory and return its ID.

    Args:
        db_path: Path to the database file
        content: Memory content
        memory_type: Type of memory (e.g., 'decision', 'solution', 'conversation')
        context: Additional context
        tags: List of tags
        importance_score: Importance score (1-100)
        related_memory_ids: IDs of related memories to create relationships with

    Returns:
        The ID of the created memory
    """
    import uuid

    conn = get_write_connection(db_path)

    # Generate ID
    memory_id = f"mem_{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()

    # Insert memory
    conn.execute(
        """
        INSERT INTO memories (id, content, context, type, status, importance_score, access_count, created_at, last_accessed, updated_at, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            memory_id,
            content,
            context,
            memory_type,
            "fresh",
            importance_score,
            0,
            now,
            now,
            now,
            json.dumps(tags) if tags else None,
        ),
    )

    # Create relationships if related_memory_ids provided
    if related_memory_ids:
        # Check if memory_relationships table exists
        table_check = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_relationships'"
        ).fetchone()

        if table_check:
            for related_id in related_memory_ids:
                try:
                    conn.execute(
                        """
                        INSERT INTO memory_relationships (source_memory_id, target_memory_id, relationship_type, strength)
                        VALUES (?, ?, ?, ?)
                        """,
                        (memory_id, related_id, "derived_from", 0.8),
                    )
                except Exception:
                    # Ignore if related memory doesn't exist
                    pass

    conn.commit()
    conn.close()

    return memory_id


# --- User Message Functions for Style Tab ---


def get_user_messages(
    db_path: str,
    session_id: Optional[str] = None,
    search: Optional[str] = None,
    has_code_blocks: Optional[bool] = None,
    has_questions: Optional[bool] = None,
    has_commands: Optional[bool] = None,
    tone_filter: Optional[str] = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Get user messages with filtering, sorting, and pagination.

    Args:
        db_path: Path to database
        session_id: Filter by session
        search: Search in content
        has_code_blocks: Filter messages with/without code blocks
        has_questions: Filter messages with/without questions
        has_commands: Filter messages with/without slash commands
        tone_filter: Filter by tone indicator (e.g., 'polite', 'urgent', 'technical')
        sort_by: Sort by column (timestamp, word_count, char_count)
        sort_order: 'asc' or 'desc'
        limit: Maximum results
        offset: Pagination offset

    Returns:
        List of user message dictionaries
    """
    conn = get_connection(db_path)

    # Check if user_messages table exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='user_messages'"
    ).fetchone()

    if not table_check:
        conn.close()
        return []

    query = "SELECT * FROM user_messages WHERE 1=1"
    params: list = []

    if session_id:
        query += " AND session_id = ?"
        params.append(session_id)

    if search:
        query += " AND content LIKE ?"
        params.append(f"%{search}%")

    if has_code_blocks is not None:
        query += " AND has_code_blocks = ?"
        params.append(1 if has_code_blocks else 0)

    if has_questions is not None:
        query += " AND has_questions = ?"
        params.append(1 if has_questions else 0)

    if has_commands is not None:
        query += " AND has_commands = ?"
        params.append(1 if has_commands else 0)

    if tone_filter:
        # Search within JSON array of tone_indicators
        query += " AND tone_indicators LIKE ?"
        params.append(f'%"{tone_filter}"%')

    # Sorting
    valid_sort_columns = ["timestamp", "word_count", "char_count", "line_count"]
    sort_by = sort_by if sort_by in valid_sort_columns else "timestamp"
    sort_order = "DESC" if sort_order.lower() == "desc" else "ASC"
    query += f" ORDER BY {sort_by} {sort_order}"

    # Pagination
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = conn.execute(query, params)
    messages = []

    for row in cursor.fetchall():
        # Parse tone_indicators from JSON
        tone_indicators = []
        if row["tone_indicators"]:
            try:
                tone_indicators = json.loads(row["tone_indicators"])
            except (json.JSONDecodeError, TypeError):
                pass

        # Get primary tone (first in the list) for frontend compatibility
        primary_tone = tone_indicators[0] if tone_indicators else None

        messages.append({
            "id": row["id"],
            "session_id": row["session_id"],
            "created_at": row["timestamp"],  # Frontend expects created_at
            "timestamp": row["timestamp"],   # Keep for backward compatibility
            "content": row["content"],
            "word_count": row["word_count"],
            "char_count": row["char_count"],
            "line_count": row["line_count"],
            "has_code_blocks": bool(row["has_code_blocks"]),
            "has_questions": bool(row["has_questions"]),
            "has_commands": bool(row["has_commands"]),
            "tone": primary_tone,            # Frontend expects single tone string
            "tone_indicators": tone_indicators,
            "project_path": row["project_path"],
        })

    conn.close()
    return messages


def get_user_message_count(
    db_path: str,
    session_id: Optional[str] = None,
) -> int:
    """Get total count of user messages.

    Args:
        db_path: Path to database
        session_id: Optional filter by session

    Returns:
        Count of user messages
    """
    conn = get_connection(db_path)

    # Check if user_messages table exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='user_messages'"
    ).fetchone()

    if not table_check:
        conn.close()
        return 0

    query = "SELECT COUNT(*) FROM user_messages"
    params = []

    if session_id:
        query += " WHERE session_id = ?"
        params.append(session_id)

    count = conn.execute(query, params).fetchone()[0]
    conn.close()
    return count


def delete_user_message(db_path: str, message_id: str) -> bool:
    """Delete a single user message.

    Args:
        db_path: Path to database
        message_id: Message ID to delete

    Returns:
        True if deleted, False if not found
    """
    conn = get_write_connection(db_path)

    cursor = conn.execute("DELETE FROM user_messages WHERE id = ?", (message_id,))
    conn.commit()

    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def delete_user_messages_bulk(db_path: str, message_ids: list[str]) -> int:
    """Delete multiple user messages.

    Args:
        db_path: Path to database
        message_ids: List of message IDs to delete

    Returns:
        Count of messages deleted
    """
    if not message_ids:
        return 0

    conn = get_write_connection(db_path)
    placeholders = ','.join('?' * len(message_ids))
    query = f"DELETE FROM user_messages WHERE id IN ({placeholders})"
    cursor = conn.execute(query, message_ids)
    conn.commit()

    count = cursor.rowcount
    conn.close()
    return count


def get_style_profile(db_path: str, project_path: Optional[str] = None) -> Optional[dict]:
    """Get user style profile.

    Args:
        db_path: Path to database
        project_path: Project-specific profile, or None for global

    Returns:
        Style profile dictionary or None if not found
    """
    conn = get_connection(db_path)

    # Check if user_style_profiles table exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='user_style_profiles'"
    ).fetchone()

    if not table_check:
        conn.close()
        return None

    if project_path:
        query = "SELECT * FROM user_style_profiles WHERE project_path = ? ORDER BY updated_at DESC LIMIT 1"
        cursor = conn.execute(query, (project_path,))
    else:
        query = "SELECT * FROM user_style_profiles WHERE project_path IS NULL ORDER BY updated_at DESC LIMIT 1"
        cursor = conn.execute(query)

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    # Parse JSON fields
    def parse_json_field(value):
        if not value:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    return {
        "id": row["id"],
        "project_path": row["project_path"],
        "total_messages": row["total_messages"],
        "avg_word_count": row["avg_word_count"],
        "avg_char_count": row["avg_char_count"],
        "common_phrases": parse_json_field(row["common_phrases"]),
        "vocabulary_richness": row["vocabulary_richness"],
        "formality_score": row["formality_score"],
        "question_frequency": row["question_frequency"],
        "command_frequency": row["command_frequency"],
        "code_block_frequency": row["code_block_frequency"],
        "punctuation_style": parse_json_field(row["punctuation_style"]),
        "greeting_patterns": parse_json_field(row["greeting_patterns"]),
        "instruction_style": parse_json_field(row["instruction_style"]),
        "sample_messages": parse_json_field(row["sample_messages"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def get_style_samples(db_path: str, limit: int = 10) -> list[dict]:
    """Get sample user messages for style analysis preview.

    Returns a diverse selection of messages showcasing different styles.

    Args:
        db_path: Path to database
        limit: Maximum samples to return

    Returns:
        List of sample messages with style indicators
    """
    conn = get_connection(db_path)

    # Check if user_messages table exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='user_messages'"
    ).fetchone()

    if not table_check:
        conn.close()
        return []

    # Get a diverse sample: some recent, some with code, some with questions
    samples = []

    # Recent messages
    cursor = conn.execute(
        "SELECT * FROM user_messages ORDER BY timestamp DESC LIMIT ?",
        (limit // 3,)
    )
    for row in cursor.fetchall():
        samples.append(_row_to_sample(row))

    # Messages with code blocks
    cursor = conn.execute(
        "SELECT * FROM user_messages WHERE has_code_blocks = 1 ORDER BY timestamp DESC LIMIT ?",
        (limit // 3,)
    )
    for row in cursor.fetchall():
        sample = _row_to_sample(row)
        if sample["id"] not in [s["id"] for s in samples]:
            samples.append(sample)

    # Longer messages (likely more substantive)
    cursor = conn.execute(
        "SELECT * FROM user_messages WHERE word_count > 20 ORDER BY word_count DESC LIMIT ?",
        (limit // 3,)
    )
    for row in cursor.fetchall():
        sample = _row_to_sample(row)
        if sample["id"] not in [s["id"] for s in samples]:
            samples.append(sample)

    conn.close()
    return samples[:limit]


def _row_to_sample(row) -> dict:
    """Convert a database row to a sample message dict."""
    tone_indicators = []
    if row["tone_indicators"]:
        try:
            tone_indicators = json.loads(row["tone_indicators"])
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "id": row["id"],
        "timestamp": row["timestamp"],
        "content_preview": row["content"][:200] + "..." if len(row["content"]) > 200 else row["content"],
        "word_count": row["word_count"],
        "has_code_blocks": bool(row["has_code_blocks"]),
        "has_questions": bool(row["has_questions"]),
        "tone_indicators": tone_indicators,
    }


def get_style_samples_by_category(db_path: str, samples_per_tone: int = 3) -> dict:
    """Get sample user messages grouped by style category.

    Maps tone_indicators to frontend categories:
    - professional: direct, polite, formal tones
    - casual: casual tones
    - technical: technical tones
    - creative: unique patterns, inquisitive tones

    Args:
        db_path: Path to database
        samples_per_tone: Max samples per category

    Returns:
        Dict with professional, casual, technical, creative lists
    """
    conn = get_connection(db_path)

    # Check if user_messages table exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='user_messages'"
    ).fetchone()

    if not table_check:
        conn.close()
        return {
            "professional": [],
            "casual": [],
            "technical": [],
            "creative": []
        }

    result = {
        "professional": [],
        "casual": [],
        "technical": [],
        "creative": []
    }

    # Mapping from tone_indicators to categories
    tone_to_category = {
        "direct": "professional",
        "polite": "professional",
        "formal": "professional",
        "casual": "casual",
        "technical": "technical",
        "inquisitive": "creative",
        "urgent": "professional",
    }

    # Get all messages with tone indicators
    cursor = conn.execute(
        """SELECT content, tone_indicators FROM user_messages
           WHERE tone_indicators IS NOT NULL AND tone_indicators != '[]'
           ORDER BY timestamp DESC LIMIT 200"""
    )

    for row in cursor.fetchall():
        content = row["content"]
        try:
            tones = json.loads(row["tone_indicators"]) if row["tone_indicators"] else []
        except (json.JSONDecodeError, TypeError):
            tones = []

        # Map to categories
        for tone in tones:
            category = tone_to_category.get(tone.lower(), "creative")
            if len(result[category]) < samples_per_tone:
                # Truncate content for preview
                preview = content[:200] + "..." if len(content) > 200 else content
                if preview not in result[category]:
                    result[category].append(preview)
                    break  # Only add to first matching category

    # Fill any empty categories with recent messages
    if any(len(v) == 0 for v in result.values()):
        cursor = conn.execute(
            "SELECT content FROM user_messages ORDER BY timestamp DESC LIMIT ?",
            (samples_per_tone * 4,)
        )
        fallback_messages = [
            row["content"][:200] + "..." if len(row["content"]) > 200 else row["content"]
            for row in cursor.fetchall()
        ]

        for category in result:
            if len(result[category]) == 0 and fallback_messages:
                # Take messages for empty categories
                for msg in fallback_messages[:samples_per_tone]:
                    if msg not in [m for v in result.values() for m in v]:
                        result[category].append(msg)

    conn.close()
    return result


def compute_style_profile_from_messages(db_path: str) -> Optional[dict]:
    """Compute a style profile from user_messages table.

    This is used when no pre-computed profile exists.

    Returns format expected by frontend StyleProfileCard:
    - total_messages: int
    - avg_word_count: float
    - primary_tone: str
    - question_percentage: float
    - tone_distribution: dict[str, int]
    - style_markers: list[str]
    """
    conn = get_connection(db_path)

    # Check if user_messages table exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='user_messages'"
    ).fetchone()

    if not table_check:
        conn.close()
        return None

    # Get total count and averages
    stats = conn.execute(
        """SELECT
           COUNT(*) as total,
           AVG(word_count) as avg_words,
           AVG(char_count) as avg_chars,
           SUM(CASE WHEN has_questions = 1 THEN 1 ELSE 0 END) as question_count
           FROM user_messages"""
    ).fetchone()

    if not stats or stats["total"] == 0:
        conn.close()
        return None

    total_messages = stats["total"]
    avg_word_count = stats["avg_words"] or 0
    question_percentage = (stats["question_count"] / total_messages * 100) if total_messages > 0 else 0

    # Compute tone distribution
    tone_distribution = {}
    cursor = conn.execute(
        "SELECT tone_indicators FROM user_messages WHERE tone_indicators IS NOT NULL AND tone_indicators != '[]'"
    )
    for row in cursor.fetchall():
        try:
            tones = json.loads(row["tone_indicators"]) if row["tone_indicators"] else []
            for tone in tones:
                tone_lower = tone.lower()
                tone_distribution[tone_lower] = tone_distribution.get(tone_lower, 0) + 1
        except (json.JSONDecodeError, TypeError):
            pass

    # Determine primary tone (most common)
    primary_tone = "direct"
    if tone_distribution:
        primary_tone = max(tone_distribution, key=tone_distribution.get)

    # Generate style markers based on the data
    style_markers = []

    if avg_word_count < 15:
        style_markers.append("Concise")
    elif avg_word_count > 40:
        style_markers.append("Detailed")
    else:
        style_markers.append("Balanced length")

    if question_percentage > 40:
        style_markers.append("Question-driven")
    elif question_percentage < 10:
        style_markers.append("Statement-focused")

    # Check for code usage
    code_stats = conn.execute(
        "SELECT SUM(CASE WHEN has_code_blocks = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as code_pct FROM user_messages"
    ).fetchone()
    if code_stats and code_stats["code_pct"] and code_stats["code_pct"] > 20:
        style_markers.append("Code-heavy")

    # Add primary tone to markers
    tone_labels = {
        "direct": "Direct",
        "polite": "Polite",
        "technical": "Technical",
        "casual": "Casual",
        "inquisitive": "Inquisitive",
        "urgent": "Urgent",
    }
    if primary_tone in tone_labels:
        style_markers.append(tone_labels[primary_tone])

    if not style_markers:
        style_markers.append("Building profile...")

    # Get sample messages to show the AI how the user actually writes
    sample_messages = []
    cursor = conn.execute(
        """SELECT content FROM user_messages
           WHERE length(content) > 20 AND length(content) < 500
           AND has_commands = 0
           ORDER BY timestamp DESC LIMIT 5"""
    )
    for row in cursor.fetchall():
        sample_messages.append(row["content"])

    conn.close()

    return {
        "totalMessages": total_messages,
        "avgWordCount": round(avg_word_count, 1),
        "primaryTone": primary_tone,
        "questionPercentage": round(question_percentage, 1),
        "toneDistribution": tone_distribution,
        "styleMarkers": style_markers,
        "sampleMessages": sample_messages,
    }


# --- Agent Query Functions ---


def get_agents(
    db_path: str,
    agent_type: Optional[str] = None,
    limit: int = 50,
    active_only: bool = False
) -> list[dict]:
    """Get agents with recent activity counts."""
    conn = get_connection(db_path)

    query = """
        SELECT
            a.*,
            COALESCE(recent.count, 0) as recent_activity_count,
            CASE WHEN a.last_seen > datetime('now', '-5 minutes') THEN 1 ELSE 0 END as is_active
        FROM agents a
        LEFT JOIN (
            SELECT agent_id, COUNT(*) as count
            FROM activities
            WHERE timestamp > datetime('now', '-1 hour')
            GROUP BY agent_id
        ) recent ON recent.agent_id = a.id
        WHERE 1=1
    """
    params = []

    if agent_type:
        query += " AND a.type = ?"
        params.append(agent_type)

    if active_only:
        query += " AND a.last_seen > datetime('now', '-5 minutes')"

    query += " ORDER BY a.last_seen DESC LIMIT ?"
    params.append(limit)

    cursor = conn.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_agent_by_id(db_path: str, agent_id: str) -> Optional[dict]:
    """Get single agent by ID."""
    conn = get_connection(db_path)

    cursor = conn.execute("""
        SELECT
            a.*,
            CASE WHEN a.last_seen > datetime('now', '-5 minutes') THEN 1 ELSE 0 END as is_active
        FROM agents a
        WHERE a.id = ?
    """, (agent_id,))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_agent_tool_breakdown(db_path: str, agent_id: str) -> list[dict]:
    """Get tool usage breakdown for an agent."""
    conn = get_connection(db_path)

    cursor = conn.execute("""
        SELECT
            tool_name,
            COUNT(*) as count,
            AVG(duration_ms) as avg_duration_ms,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
        FROM activities
        WHERE agent_id = ? AND tool_name IS NOT NULL
        GROUP BY tool_name
        ORDER BY count DESC
    """, (agent_id,))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_agent_files_touched(db_path: str, agent_id: str, limit: int = 50) -> list[str]:
    """Get list of files an agent has touched."""
    conn = get_connection(db_path)

    # Files from file_path column
    cursor = conn.execute("""
        SELECT DISTINCT file_path
        FROM activities
        WHERE agent_id = ?
          AND file_path IS NOT NULL
          AND file_path != ''
        LIMIT ?
    """, (agent_id, limit))

    files = [row[0] for row in cursor.fetchall()]
    conn.close()
    return files


def get_agent_parent(db_path: str, agent_id: str) -> Optional[str]:
    """Find which agent spawned this subagent (via Task tool)."""
    conn = get_connection(db_path)

    # Look for Task tool call that created this agent
    cursor = conn.execute("""
        SELECT agent_id
        FROM activities
        WHERE tool_name = 'Task'
          AND tool_output LIKE ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (f'%{agent_id}%',))

    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None
