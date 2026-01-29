"""Hybrid search combining keyword and semantic search."""

import logging
import sqlite3
from typing import Optional

from ..models.memory import Memory
from .keyword import keyword_search
from .semantic import semantic_search
from .ranking import normalize_scores

logger = logging.getLogger(__name__)


def hybrid_search(
    conn: sqlite3.Connection,
    query: str,
    type_filter: Optional[str] = None,
    tags_filter: Optional[list[str]] = None,
    status_filter: Optional[str] = None,
    min_importance: Optional[int] = None,
    include_archived: bool = False,
    limit: int = 10,
    keyword_weight: float = 0.4,
    semantic_weight: float = 0.6,
) -> list[tuple[Memory, float, float]]:
    """Search memories using combined keyword and semantic search.

    The hybrid approach uses both methods and combines their scores:
    - Keyword search finds exact/fuzzy matches
    - Semantic search finds conceptually similar content
    - Results are merged and re-ranked using weighted scores

    Args:
        conn: Database connection
        query: Search query string
        type_filter: Filter by memory type
        tags_filter: Filter by tags
        status_filter: Filter by status
        min_importance: Minimum importance score
        include_archived: Include archived memories
        limit: Maximum results
        keyword_weight: Weight for keyword scores (0-1)
        semantic_weight: Weight for semantic scores (0-1)

    Returns:
        List of (Memory, keyword_score, semantic_score) tuples
    """
    # Normalize weights
    total_weight = keyword_weight + semantic_weight
    if total_weight > 0:
        keyword_weight = keyword_weight / total_weight
        semantic_weight = semantic_weight / total_weight

    # Perform keyword search (get more than limit for merging)
    search_limit = min(limit * 3, 100)

    keyword_results = keyword_search(
        conn,
        query=query,
        type_filter=type_filter,
        tags_filter=tags_filter,
        status_filter=status_filter,
        min_importance=min_importance,
        include_archived=include_archived,
        limit=search_limit,
    )

    # Perform semantic search
    semantic_results = []
    try:
        semantic_results = semantic_search(
            conn,
            query=query,
            type_filter=type_filter,
            tags_filter=tags_filter,
            status_filter=status_filter,
            min_importance=min_importance,
            include_archived=include_archived,
            limit=search_limit,
            similarity_threshold=0.2,  # Lower threshold for hybrid
        )
    except Exception as e:
        logger.warning(f"Semantic search failed, using keyword only: {e}")

    # Build score dictionaries
    keyword_scores: dict[str, tuple[Memory, float]] = {}
    for memory, score in keyword_results:
        keyword_scores[memory.id] = (memory, score)

    semantic_scores: dict[str, tuple[Memory, float]] = {}
    for memory, score in semantic_results:
        semantic_scores[memory.id] = (memory, score)

    # Get all unique memory IDs
    all_ids = set(keyword_scores.keys()) | set(semantic_scores.keys())

    if not all_ids:
        return []

    # Normalize keyword scores to 0-1 range
    if keyword_scores:
        kw_score_values = [s for _, s in keyword_scores.values()]
        kw_normalized = normalize_scores(kw_score_values)
        kw_norm_map = dict(zip(keyword_scores.keys(), kw_normalized))
    else:
        kw_norm_map = {}

    # Semantic scores are already 0-1 (cosine similarity)
    sem_norm_map = {mid: score for mid, (_, score) in semantic_scores.items()}

    # Combine scores
    combined_results: list[tuple[Memory, float, float]] = []

    for memory_id in all_ids:
        # Get memory object (prefer from keyword results for consistency)
        if memory_id in keyword_scores:
            memory = keyword_scores[memory_id][0]
        else:
            memory = semantic_scores[memory_id][0]

        # Get normalized scores (0 if not in that result set)
        kw_score = kw_norm_map.get(memory_id, 0.0)
        sem_score = sem_norm_map.get(memory_id, 0.0)

        combined_results.append((memory, kw_score, sem_score))

    # Sort by weighted combined score
    def combined_score(item: tuple[Memory, float, float]) -> float:
        _, kw, sem = item
        return (kw * keyword_weight) + (sem * semantic_weight)

    combined_results.sort(key=combined_score, reverse=True)

    return combined_results[:limit]


def search(
    conn: sqlite3.Connection,
    query: str,
    mode: str = "keyword",
    type_filter: Optional[str] = None,
    tags_filter: Optional[list[str]] = None,
    status_filter: Optional[str] = None,
    min_importance: Optional[int] = None,
    include_archived: bool = False,
    limit: int = 10,
) -> list[tuple[Memory, float, float]]:
    """Unified search function supporting all modes.

    Args:
        conn: Database connection
        query: Search query string
        mode: Search mode - "keyword", "semantic", or "hybrid"
        type_filter: Filter by memory type
        tags_filter: Filter by tags
        status_filter: Filter by status
        min_importance: Minimum importance score
        include_archived: Include archived memories
        limit: Maximum results

    Returns:
        List of (Memory, keyword_score, semantic_score) tuples
    """
    common_args = {
        "conn": conn,
        "query": query,
        "type_filter": type_filter,
        "tags_filter": tags_filter,
        "status_filter": status_filter,
        "min_importance": min_importance,
        "include_archived": include_archived,
        "limit": limit,
    }

    if mode == "keyword":
        results = keyword_search(**common_args)
        # Convert to unified format (keyword_score, semantic_score=0)
        return [(memory, score, 0.0) for memory, score in results]

    elif mode == "semantic":
        try:
            results = semantic_search(**common_args, similarity_threshold=0.3)
            # Convert to unified format (keyword_score=0, semantic_score)
            return [(memory, 0.0, score) for memory, score in results]
        except Exception as e:
            logger.warning(f"Semantic search failed, falling back to keyword: {e}")
            results = keyword_search(**common_args)
            return [(memory, score, 0.0) for memory, score in results]

    elif mode == "hybrid":
        return hybrid_search(**common_args)

    else:
        logger.warning(f"Unknown search mode '{mode}', using keyword")
        results = keyword_search(**common_args)
        return [(memory, score, 0.0) for memory, score in results]
