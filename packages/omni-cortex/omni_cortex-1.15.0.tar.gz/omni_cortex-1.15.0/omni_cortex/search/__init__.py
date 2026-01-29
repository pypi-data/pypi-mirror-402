"""Search functionality for Omni Cortex."""

from .keyword import keyword_search
from .ranking import calculate_relevance_score, rank_memories, normalize_scores
from .semantic import semantic_search, find_similar_memories, get_embedding_coverage
from .hybrid import hybrid_search, search

__all__ = [
    # Keyword search
    "keyword_search",
    # Semantic search
    "semantic_search",
    "find_similar_memories",
    "get_embedding_coverage",
    # Hybrid search
    "hybrid_search",
    "search",
    # Ranking
    "calculate_relevance_score",
    "rank_memories",
    "normalize_scores",
]
