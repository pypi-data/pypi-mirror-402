"""Semantic search using vector embeddings."""

import logging
import sqlite3
from typing import Optional

import numpy as np

from ..models.memory import Memory, _row_to_memory
from ..embeddings.local import (
    generate_embedding,
    blob_to_vector,
    DEFAULT_MODEL_NAME,
)
from ..config import load_config

logger = logging.getLogger(__name__)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        a: First vector
        b: Second vector

    Returns:
        Similarity score between -1 and 1
    """
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


def semantic_search(
    conn: sqlite3.Connection,
    query: str,
    type_filter: Optional[str] = None,
    tags_filter: Optional[list[str]] = None,
    status_filter: Optional[str] = None,
    min_importance: Optional[int] = None,
    include_archived: bool = False,
    limit: int = 10,
    similarity_threshold: float = 0.3,
    model_name: str = DEFAULT_MODEL_NAME,
) -> list[tuple[Memory, float]]:
    """Search memories using semantic similarity.

    Args:
        conn: Database connection
        query: Search query string
        type_filter: Filter by memory type
        tags_filter: Filter by tags
        status_filter: Filter by status
        min_importance: Minimum importance score
        include_archived: Include archived memories
        limit: Maximum results
        similarity_threshold: Minimum similarity score
        model_name: Embedding model to use

    Returns:
        List of (Memory, similarity_score) tuples
    """
    # Check if embeddings are enabled - skip semantic search if disabled
    config = load_config()
    if not config.embedding_enabled:
        logger.debug("Embeddings disabled, skipping semantic search")
        return []

    # Generate embedding for query
    try:
        query_embedding = generate_embedding(query, model_name)
    except ImportError:
        logger.warning("sentence-transformers not available, cannot perform semantic search")
        return []
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return []

    # Build WHERE conditions for filtering
    where_conditions = []
    params: list = []

    # Only search memories with embeddings
    where_conditions.append("m.has_embedding = 1")

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

    where_sql = "WHERE " + " AND ".join(where_conditions)

    # Get all matching memories with their embeddings
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT m.*, e.vector
        FROM memories m
        JOIN embeddings e ON m.id = e.memory_id
        {where_sql}
        """,
        params,
    )

    # Calculate similarity scores
    results = []
    for row in cursor.fetchall():
        memory_embedding = blob_to_vector(row["vector"])
        similarity = cosine_similarity(query_embedding, memory_embedding)

        # Apply threshold
        if similarity >= similarity_threshold:
            memory = _row_to_memory(row)
            results.append((memory, similarity))

    # Sort by similarity (highest first)
    results.sort(key=lambda x: x[1], reverse=True)

    # Limit results
    return results[:limit]


def find_similar_memories(
    conn: sqlite3.Connection,
    memory_id: str,
    limit: int = 10,
    similarity_threshold: float = 0.5,
    exclude_ids: Optional[list[str]] = None,
) -> list[tuple[Memory, float]]:
    """Find memories similar to a given memory.

    Args:
        conn: Database connection
        memory_id: ID of the source memory
        limit: Maximum results
        similarity_threshold: Minimum similarity score
        exclude_ids: Memory IDs to exclude

    Returns:
        List of (Memory, similarity_score) tuples
    """
    # Get the source memory's embedding
    cursor = conn.cursor()
    cursor.execute(
        "SELECT vector FROM embeddings WHERE memory_id = ?",
        (memory_id,),
    )
    row = cursor.fetchone()

    if not row:
        logger.warning(f"No embedding found for memory {memory_id}")
        return []

    source_embedding = blob_to_vector(row["vector"])

    # Build exclusion list
    exclude_set = set(exclude_ids or [])
    exclude_set.add(memory_id)  # Always exclude the source

    # Get all other embeddings
    cursor.execute(
        """
        SELECT m.*, e.vector
        FROM memories m
        JOIN embeddings e ON m.id = e.memory_id
        WHERE m.has_embedding = 1 AND m.status != 'archived'
        """
    )

    results = []
    for row in cursor.fetchall():
        if row["id"] in exclude_set:
            continue

        memory_embedding = blob_to_vector(row["vector"])
        similarity = cosine_similarity(source_embedding, memory_embedding)

        if similarity >= similarity_threshold:
            memory = _row_to_memory(row)
            results.append((memory, similarity))

    # Sort by similarity
    results.sort(key=lambda x: x[1], reverse=True)

    return results[:limit]


def get_embedding_coverage(conn: sqlite3.Connection) -> dict:
    """Get statistics about embedding coverage.

    Returns:
        Dict with total_memories, with_embeddings, without_embeddings, coverage_pct
    """
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM memories")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM memories WHERE has_embedding = 1")
    with_embeddings = cursor.fetchone()[0]

    without_embeddings = total - with_embeddings
    coverage_pct = (with_embeddings / total * 100) if total > 0 else 0.0

    return {
        "total_memories": total,
        "with_embeddings": with_embeddings,
        "without_embeddings": without_embeddings,
        "coverage_pct": round(coverage_pct, 1),
    }
