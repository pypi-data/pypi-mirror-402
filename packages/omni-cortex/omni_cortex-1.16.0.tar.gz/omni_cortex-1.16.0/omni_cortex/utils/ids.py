"""ID generation utilities for Omni Cortex."""

import os
import time
from typing import Literal


IdPrefix = Literal["mem", "act", "sess", "rel", "emb", "sum"]


def generate_id(prefix: IdPrefix) -> str:
    """Generate a unique ID with timestamp and random suffix.

    Format: {prefix}_{timestamp_ms}_{random_hex}

    Args:
        prefix: One of mem, act, sess, rel, emb, sum

    Returns:
        Unique ID string
    """
    timestamp_ms = int(time.time() * 1000)
    random_hex = os.urandom(4).hex()
    return f"{prefix}_{timestamp_ms}_{random_hex}"


def generate_memory_id() -> str:
    """Generate a memory ID."""
    return generate_id("mem")


def generate_activity_id() -> str:
    """Generate an activity ID."""
    return generate_id("act")


def generate_session_id() -> str:
    """Generate a session ID."""
    return generate_id("sess")


def generate_relationship_id() -> str:
    """Generate a relationship ID."""
    return generate_id("rel")


def generate_embedding_id() -> str:
    """Generate an embedding ID."""
    return generate_id("emb")


def generate_summary_id() -> str:
    """Generate a session summary ID."""
    return generate_id("sum")


def parse_id_timestamp(id_str: str) -> int:
    """Extract timestamp from an ID.

    Args:
        id_str: ID string in format prefix_timestamp_random

    Returns:
        Timestamp in milliseconds
    """
    try:
        parts = id_str.split("_")
        if len(parts) >= 2:
            return int(parts[1])
    except (ValueError, IndexError):
        pass
    return 0
