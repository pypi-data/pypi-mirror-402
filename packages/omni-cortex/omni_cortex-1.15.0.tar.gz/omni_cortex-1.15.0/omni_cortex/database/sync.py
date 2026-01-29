"""Global index synchronization for cross-project memory search.

This module handles syncing memories from project-local databases to the
global database at ~/.omni-cortex/global.db, enabling cross-project search.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional

from .connection import get_connection, init_database
from ..config import get_global_db_path, get_project_path, load_config
from ..utils.timestamps import now_iso

logger = logging.getLogger(__name__)


def sync_memory_to_global(
    memory_id: str,
    content: str,
    memory_type: str,
    tags: list[str],
    context: Optional[str],
    importance_score: float,
    status: str,
    project_path: str,
    created_at: str,
    updated_at: str,
) -> bool:
    """Sync a single memory to the global index.

    Args:
        memory_id: The memory ID
        content: Memory content
        memory_type: Memory type
        tags: List of tags
        context: Optional context
        importance_score: Importance score
        status: Memory status
        project_path: Source project path
        created_at: Creation timestamp
        updated_at: Update timestamp

    Returns:
        True if synced successfully
    """
    config = load_config()
    if not config.global_sync_enabled:
        return False

    try:
        global_conn = init_database(is_global=True)

        cursor = global_conn.cursor()

        # Upsert the memory to global index
        cursor.execute(
            """
            INSERT INTO memories (
                id, content, type, tags, context,
                created_at, updated_at, last_accessed,
                access_count, importance_score, status,
                project_path, has_embedding
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 0)
            ON CONFLICT(id) DO UPDATE SET
                content = excluded.content,
                type = excluded.type,
                tags = excluded.tags,
                context = excluded.context,
                updated_at = excluded.updated_at,
                importance_score = excluded.importance_score,
                status = excluded.status
            """,
            (
                memory_id,
                content,
                memory_type,
                json.dumps(tags),
                context,
                created_at,
                updated_at,
                now_iso(),
                importance_score,
                status,
                project_path,
            ),
        )

        global_conn.commit()
        logger.debug(f"Synced memory {memory_id} to global index")
        return True

    except Exception as e:
        logger.warning(f"Failed to sync memory {memory_id} to global: {e}")
        return False


def delete_memory_from_global(memory_id: str) -> bool:
    """Remove a memory from the global index.

    Args:
        memory_id: The memory ID to remove

    Returns:
        True if removed successfully
    """
    config = load_config()
    if not config.global_sync_enabled:
        return False

    try:
        global_conn = init_database(is_global=True)
        cursor = global_conn.cursor()

        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        global_conn.commit()

        if cursor.rowcount > 0:
            logger.debug(f"Removed memory {memory_id} from global index")
            return True
        return False

    except Exception as e:
        logger.warning(f"Failed to remove memory {memory_id} from global: {e}")
        return False


def search_global_memories(
    query: str,
    type_filter: Optional[str] = None,
    tags_filter: Optional[list[str]] = None,
    project_filter: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """Search memories across all projects via global index.

    Args:
        query: Search query
        type_filter: Filter by memory type
        tags_filter: Filter by tags
        project_filter: Filter by project path (substring match)
        limit: Maximum results

    Returns:
        List of memory dicts with project_path included
    """
    try:
        global_conn = init_database(is_global=True)
        cursor = global_conn.cursor()

        # Escape FTS5 special characters
        fts_query = _escape_fts_query(query)

        # Build WHERE conditions
        where_conditions = []
        params: list = [fts_query]

        if type_filter:
            where_conditions.append("m.type = ?")
            params.append(type_filter)

        if project_filter:
            where_conditions.append("m.project_path LIKE ?")
            params.append(f"%{project_filter}%")

        where_conditions.append("m.status != 'archived'")

        if tags_filter:
            tag_conditions = []
            for tag in tags_filter:
                tag_conditions.append("m.tags LIKE ?")
                params.append(f'%"{tag}"%')
            where_conditions.append(f"({' OR '.join(tag_conditions)})")

        where_sql = ""
        if where_conditions:
            where_sql = "AND " + " AND ".join(where_conditions)

        params.append(limit)

        try:
            cursor.execute(
                f"""
                SELECT m.*, bm25(memories_fts) as score
                FROM memories_fts fts
                JOIN memories m ON fts.rowid = m.rowid
                WHERE memories_fts MATCH ?
                {where_sql}
                ORDER BY score
                LIMIT ?
                """,
                params,
            )
        except sqlite3.OperationalError:
            # Fallback to LIKE search if FTS fails
            return _fallback_global_search(
                global_conn, query, type_filter, tags_filter, project_filter, limit
            )

        results = []
        for row in cursor.fetchall():
            tags = row["tags"]
            if tags and isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except json.JSONDecodeError:
                    tags = []

            results.append({
                "id": row["id"],
                "content": row["content"],
                "type": row["type"],
                "tags": tags,
                "context": row["context"],
                "importance_score": row["importance_score"],
                "status": row["status"],
                "project_path": row["project_path"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "score": -row["score"],  # bm25 returns negative scores
            })

        return results

    except Exception as e:
        logger.error(f"Global search failed: {e}")
        return []


def _escape_fts_query(query: str) -> str:
    """Escape special characters for FTS5 query."""
    special_chars = ['"', "'", "(", ")", "*", ":", "^", "-", "+"]
    escaped = query
    for char in special_chars:
        escaped = escaped.replace(char, " ")

    words = escaped.split()
    if not words:
        return '""'

    if len(words) == 1:
        return f'"{words[0]}"'

    return " OR ".join(f'"{word}"' for word in words)


def _fallback_global_search(
    conn: sqlite3.Connection,
    query: str,
    type_filter: Optional[str],
    tags_filter: Optional[list[str]],
    project_filter: Optional[str],
    limit: int,
) -> list[dict]:
    """Fallback to LIKE search if FTS5 fails."""
    words = query.lower().split()
    if not words:
        return []

    where_conditions = []
    params: list = []

    # Match any word in content or context
    word_conditions = []
    for word in words:
        word_conditions.append("(LOWER(content) LIKE ? OR LOWER(context) LIKE ?)")
        params.extend([f"%{word}%", f"%{word}%"])
    where_conditions.append(f"({' OR '.join(word_conditions)})")

    if type_filter:
        where_conditions.append("type = ?")
        params.append(type_filter)

    if project_filter:
        where_conditions.append("project_path LIKE ?")
        params.append(f"%{project_filter}%")

    where_conditions.append("status != 'archived'")

    if tags_filter:
        tag_conds = []
        for tag in tags_filter:
            tag_conds.append("tags LIKE ?")
            params.append(f'%"{tag}"%')
        where_conditions.append(f"({' OR '.join(tag_conds)})")

    params.append(limit)

    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT *
        FROM memories
        WHERE {' AND '.join(where_conditions)}
        ORDER BY importance_score DESC, updated_at DESC
        LIMIT ?
        """,
        params,
    )

    results = []
    for row in cursor.fetchall():
        tags = row["tags"]
        if tags and isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except json.JSONDecodeError:
                tags = []

        content = (row["content"] + " " + (row["context"] or "")).lower()
        score = sum(1 for word in words if word in content)

        results.append({
            "id": row["id"],
            "content": row["content"],
            "type": row["type"],
            "tags": tags,
            "context": row["context"],
            "importance_score": row["importance_score"],
            "status": row["status"],
            "project_path": row["project_path"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "score": float(score),
        })

    return results


def get_global_stats() -> dict:
    """Get statistics from the global index.

    Returns:
        Dict with counts by project, type, etc.
    """
    try:
        global_conn = init_database(is_global=True)
        cursor = global_conn.cursor()

        stats = {}

        # Total memories
        cursor.execute("SELECT COUNT(*) FROM memories")
        stats["total_memories"] = cursor.fetchone()[0]

        # By project
        cursor.execute("""
            SELECT project_path, COUNT(*) as cnt
            FROM memories
            GROUP BY project_path
            ORDER BY cnt DESC
        """)
        stats["by_project"] = {row["project_path"]: row["cnt"] for row in cursor.fetchall()}

        # By type
        cursor.execute("""
            SELECT type, COUNT(*) as cnt
            FROM memories
            GROUP BY type
            ORDER BY cnt DESC
        """)
        stats["by_type"] = {row["type"]: row["cnt"] for row in cursor.fetchall()}

        return stats

    except Exception as e:
        logger.error(f"Failed to get global stats: {e}")
        return {"error": str(e)}


def sync_all_project_memories() -> int:
    """Sync all memories from current project to global index.

    Returns:
        Number of memories synced
    """
    config = load_config()
    if not config.global_sync_enabled:
        return 0

    try:
        project_conn = init_database()
        project_path = str(get_project_path())

        cursor = project_conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE status != 'archived'")

        count = 0
        for row in cursor.fetchall():
            tags = row["tags"]
            if tags and isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except json.JSONDecodeError:
                    tags = []
            else:
                tags = []

            synced = sync_memory_to_global(
                memory_id=row["id"],
                content=row["content"],
                memory_type=row["type"],
                tags=tags,
                context=row["context"],
                importance_score=row["importance_score"],
                status=row["status"],
                project_path=project_path,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            if synced:
                count += 1

        logger.info(f"Synced {count} memories to global index")
        return count

    except Exception as e:
        logger.error(f"Failed to sync project memories: {e}")
        return 0
