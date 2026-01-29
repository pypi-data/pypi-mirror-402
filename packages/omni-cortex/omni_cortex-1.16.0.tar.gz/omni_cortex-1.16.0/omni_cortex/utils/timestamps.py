"""Timestamp utilities for Omni Cortex."""

from datetime import datetime, timezone, timedelta
from typing import Optional


def now_iso() -> str:
    """Get current time as ISO 8601 string with timezone.

    Returns:
        ISO 8601 formatted timestamp with UTC timezone
    """
    return datetime.now(timezone.utc).isoformat()


def parse_iso(iso_string: str) -> datetime:
    """Parse an ISO 8601 string to datetime.

    Args:
        iso_string: ISO 8601 formatted string

    Returns:
        datetime object with timezone info
    """
    # Handle various ISO formats
    dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def format_relative_time(dt: datetime | str) -> str:
    """Format a datetime as relative time (e.g., '2 hours ago').

    Args:
        dt: datetime object or ISO string

    Returns:
        Human-readable relative time string
    """
    if isinstance(dt, str):
        dt = parse_iso(dt)

    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    diff = now - dt

    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif diff < timedelta(days=30):
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif diff < timedelta(days=365):
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"


def format_duration(ms: int) -> str:
    """Format milliseconds as human-readable duration.

    Args:
        ms: Duration in milliseconds

    Returns:
        Human-readable duration string
    """
    if ms < 1000:
        return f"{ms}ms"
    elif ms < 60000:
        seconds = ms / 1000
        return f"{seconds:.1f}s"
    elif ms < 3600000:
        minutes = ms / 60000
        return f"{minutes:.1f}m"
    else:
        hours = ms / 3600000
        return f"{hours:.1f}h"


def days_since(dt: datetime | str) -> int:
    """Calculate days since a given datetime.

    Args:
        dt: datetime object or ISO string

    Returns:
        Number of days since the datetime
    """
    if isinstance(dt, str):
        dt = parse_iso(dt)

    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return (now - dt).days


def hours_since(dt: datetime | str) -> float:
    """Calculate hours since a given datetime.

    Args:
        dt: datetime object or ISO string

    Returns:
        Number of hours since the datetime
    """
    if isinstance(dt, str):
        dt = parse_iso(dt)

    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return (now - dt).total_seconds() / 3600
