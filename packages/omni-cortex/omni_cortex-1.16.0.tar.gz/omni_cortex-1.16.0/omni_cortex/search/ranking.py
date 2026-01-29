"""Multi-factor relevance ranking for search results."""

import math
from datetime import datetime, timezone
from typing import Optional

from ..models.memory import Memory
from ..utils.timestamps import parse_iso


def calculate_relevance_score(
    memory: Memory,
    keyword_score: float = 0.0,
    semantic_score: float = 0.0,
    query: Optional[str] = None,
) -> float:
    """Calculate multi-factor relevance score for a memory.

    Scoring factors:
    - Keyword match score (40%)
    - Semantic similarity score (40%)
    - Access frequency (log scale, max +20)
    - Recency (exponential decay, max +15)
    - Freshness status bonus/penalty
    - Importance score (0-15)

    Args:
        memory: Memory object to score
        keyword_score: Score from keyword search (0-1 normalized)
        semantic_score: Score from semantic search (0-1 normalized)
        query: Optional query string for additional matching

    Returns:
        Combined relevance score (higher = more relevant)
    """
    score = 0.0

    # Base scores from search (40% each, max 80 combined)
    # Normalize to 0-40 range
    score += min(40.0, keyword_score * 40.0)
    score += min(40.0, semantic_score * 40.0)

    # Access frequency bonus (log scale, max +20)
    # More frequently accessed memories are likely more useful
    access_count = memory.access_count or 0
    access_bonus = min(20.0, math.log1p(access_count) * 5.0)
    score += access_bonus

    # Recency bonus (exponential decay over 30 days, max +15)
    # Recently accessed memories are more relevant
    last_accessed = parse_iso(memory.last_accessed)
    now = datetime.now(timezone.utc)
    days_since_access = (now - last_accessed).days

    recency_bonus = max(0.0, 15.0 * math.exp(-days_since_access / 30.0))
    score += recency_bonus

    # Freshness status bonus/penalty
    freshness_bonus = {
        "fresh": 10.0,
        "needs_review": 0.0,
        "outdated": -10.0,
        "archived": -30.0,
    }
    score += freshness_bonus.get(memory.status, 0.0)

    # Importance score contribution (0-100 scaled to 0-15)
    importance = memory.importance_score or 50.0
    score += importance * 0.15

    # Exact phrase match bonus (if query provided)
    if query and query.lower() in memory.content.lower():
        score += 10.0

    return score


def rank_memories(
    memories_with_scores: list[tuple[Memory, float, float]],
    query: Optional[str] = None,
) -> list[tuple[Memory, float]]:
    """Rank memories by combined relevance score.

    Args:
        memories_with_scores: List of (Memory, keyword_score, semantic_score) tuples
        query: Optional query string

    Returns:
        List of (Memory, final_score) tuples, sorted by score descending
    """
    results = []

    for memory, keyword_score, semantic_score in memories_with_scores:
        final_score = calculate_relevance_score(
            memory,
            keyword_score=keyword_score,
            semantic_score=semantic_score,
            query=query,
        )
        results.append((memory, final_score))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)

    return results


def normalize_scores(scores: list[float]) -> list[float]:
    """Normalize a list of scores to 0-1 range.

    Args:
        scores: List of raw scores

    Returns:
        List of normalized scores
    """
    if not scores:
        return []

    min_score = min(scores)
    max_score = max(scores)
    range_score = max_score - min_score

    if range_score == 0:
        return [1.0] * len(scores)

    return [(s - min_score) / range_score for s in scores]
