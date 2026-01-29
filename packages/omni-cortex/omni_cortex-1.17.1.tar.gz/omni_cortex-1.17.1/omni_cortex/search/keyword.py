"""Keyword search using SQLite FTS5."""

import sqlite3
from typing import Optional

from ..models.memory import Memory, _row_to_memory


def keyword_search(
    conn: sqlite3.Connection,
    query: str,
    type_filter: Optional[str] = None,
    tags_filter: Optional[list[str]] = None,
    status_filter: Optional[str] = None,
    min_importance: Optional[int] = None,
    include_archived: bool = False,
    limit: int = 10,
) -> list[tuple[Memory, float]]:
    """Search memories using FTS5 keyword search.

    Args:
        conn: Database connection
        query: Search query string
        type_filter: Filter by memory type
        tags_filter: Filter by tags
        status_filter: Filter by status
        min_importance: Minimum importance score
        include_archived: Include archived memories
        limit: Maximum results

    Returns:
        List of (Memory, score) tuples
    """
    # Build the FTS query
    # Escape special FTS5 characters
    fts_query = _escape_fts_query(query)

    # Build WHERE conditions for the join
    where_conditions = []
    params: list = [fts_query]

    if type_filter:
        where_conditions.append("m.type = ?")
        params.append(type_filter)

    if status_filter:
        where_conditions.append("m.status = ?")
        params.append(status_filter)
    elif not include_archived:
        where_conditions.append("m.status != 'archived'")

    if min_importance is not None:
        where_conditions.append("m.importance_score >= ?")
        params.append(min_importance)

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

    cursor = conn.cursor()

    # Use FTS5 with bm25 ranking
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

        results = []
        for row in cursor.fetchall():
            # bm25 returns negative scores (more negative = better match)
            # Convert to positive scores for our ranking
            score = -row["score"]
            memory = _row_to_memory(row)
            results.append((memory, score))

        return results

    except sqlite3.OperationalError as e:
        # If FTS query fails, fall back to LIKE search
        if "fts5" in str(e).lower() or "match" in str(e).lower():
            return _fallback_like_search(
                conn, query, type_filter, tags_filter, status_filter,
                min_importance, include_archived, limit
            )
        raise


def _escape_fts_query(query: str) -> str:
    """Escape special characters for FTS5 query.

    Args:
        query: Raw search query

    Returns:
        Escaped FTS5 query
    """
    # Remove FTS5 special characters that could cause syntax errors
    special_chars = ['"', "'", "(", ")", "*", ":", "^", "-", "+"]
    escaped = query
    for char in special_chars:
        escaped = escaped.replace(char, " ")

    # Clean up whitespace
    words = escaped.split()

    # Handle empty query
    if not words:
        return '""'

    # For simple queries, just use OR matching
    if len(words) == 1:
        return f'"{words[0]}"'

    # For multi-word queries, match any word
    return " OR ".join(f'"{word}"' for word in words)


def _fallback_like_search(
    conn: sqlite3.Connection,
    query: str,
    type_filter: Optional[str],
    tags_filter: Optional[list[str]],
    status_filter: Optional[str],
    min_importance: Optional[int],
    include_archived: bool,
    limit: int,
) -> list[tuple[Memory, float]]:
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

    if status_filter:
        where_conditions.append("status = ?")
        params.append(status_filter)
    elif not include_archived:
        where_conditions.append("status != 'archived'")

    if min_importance is not None:
        where_conditions.append("importance_score >= ?")
        params.append(min_importance)

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
        ORDER BY importance_score DESC, last_accessed DESC
        LIMIT ?
        """,
        params,
    )

    results = []
    for row in cursor.fetchall():
        memory = _row_to_memory(row)
        # Calculate a simple score based on word matches
        content = (memory.content + " " + (memory.context or "")).lower()
        score = sum(1 for word in words if word in content)
        results.append((memory, float(score)))

    return results
