"""Importance decay algorithm for memories."""

import math
from datetime import datetime, timezone
from typing import Optional

from ..utils.timestamps import parse_iso


def calculate_decayed_importance(
    base_importance: float,
    last_accessed: str,
    access_count: int,
    manual_importance: Optional[int] = None,
    decay_rate: float = 0.5,
) -> float:
    """Calculate the decayed importance score for a memory.

    The decay formula:
    - Starts from base importance (typically 50 or user-set value)
    - Decays linearly by decay_rate points per day since last access
    - Gains back importance from access frequency (log scale)
    - Manual importance overrides all calculations

    Args:
        base_importance: Original importance score (0-100)
        last_accessed: ISO timestamp of last access
        access_count: Number of times memory was accessed
        manual_importance: User-set importance (overrides calculation)
        decay_rate: Points to decay per day (default 0.5)

    Returns:
        Current importance score (0-100)
    """
    # Manual importance always wins
    if manual_importance is not None:
        return float(manual_importance)

    # Calculate days since last access
    last_dt = parse_iso(last_accessed)
    now = datetime.now(timezone.utc)
    days = (now - last_dt).days

    # Apply decay
    decayed = base_importance - (days * decay_rate)

    # Access boost: frequently used memories resist decay
    # log1p(10) ≈ 2.4, so 10 accesses = +12 importance
    access_boost = math.log1p(access_count) * 5.0

    # Calculate final score
    final = decayed + access_boost

    # Clamp to 0-100
    return max(0.0, min(100.0, final))


def should_mark_for_review(
    last_verified: Optional[str],
    review_days: int = 30,
) -> bool:
    """Check if a memory should be marked for review.

    Args:
        last_verified: ISO timestamp of last verification, or None
        review_days: Days threshold for review

    Returns:
        True if memory should be reviewed
    """
    if last_verified is None:
        return False  # Never verified, use created_at logic elsewhere

    verified_dt = parse_iso(last_verified)
    now = datetime.now(timezone.utc)
    days = (now - verified_dt).days

    return days >= review_days


def get_freshness_status(
    created_at: str,
    last_verified: Optional[str],
    current_status: str,
    review_days: int = 30,
) -> str:
    """Determine the freshness status for a memory.

    Args:
        created_at: ISO timestamp of creation
        last_verified: ISO timestamp of last verification
        current_status: Current status value
        review_days: Days threshold for review

    Returns:
        New status: fresh, needs_review, outdated, or archived
    """
    # Archived stays archived until explicitly changed
    if current_status == "archived":
        return "archived"

    # Outdated stays outdated until verified
    if current_status == "outdated":
        return "outdated"

    # Check if needs review
    reference_date = last_verified or created_at
    reference_dt = parse_iso(reference_date)
    now = datetime.now(timezone.utc)
    days = (now - reference_dt).days

    if days >= review_days * 2:
        return "outdated"
    elif days >= review_days:
        return "needs_review"

    return "fresh"


def apply_decay_to_memory(
    importance_score: float,
    last_accessed: str,
    access_count: int,
    manual_importance: Optional[int],
    decay_rate: float = 0.5,
) -> float:
    """Apply decay calculation to a memory's importance.

    This is a convenience function that wraps calculate_decayed_importance.

    Args:
        importance_score: Current stored importance
        last_accessed: Last access timestamp
        access_count: Access count
        manual_importance: Manual override if any
        decay_rate: Decay rate

    Returns:
        Updated importance score
    """
    return calculate_decayed_importance(
        base_importance=importance_score,
        last_accessed=last_accessed,
        access_count=access_count,
        manual_importance=manual_importance,
        decay_rate=decay_rate,
    )
