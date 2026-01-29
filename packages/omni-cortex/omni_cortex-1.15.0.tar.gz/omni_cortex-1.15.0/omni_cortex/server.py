#!/usr/bin/env python3
"""Omni Cortex MCP Server - Universal Memory System for Claude Code.

This server provides a dual-layer memory system combining:
- Activity logging (audit trail of all tool calls and decisions)
- Knowledge storage (distilled insights, solutions, and learnings)

Features:
- 15 tools across 4 categories: Activities, Memories, Sessions, Utilities
- Full-text search with FTS5
- Auto-categorization and smart tagging
- Multi-factor relevance ranking
- Session continuity ("Last time you were working on...")
- Importance decay over time
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from mcp.server.fastmcp import FastMCP

from .database.connection import init_database, close_all_connections
from .tools.memories import register_memory_tools
from .tools.activities import register_activity_tools
from .tools.sessions import register_session_tools
from .tools.utilities import register_utility_tools


@asynccontextmanager
async def lifespan(mcp: FastMCP) -> AsyncGenerator[dict, None]:
    """Manage server lifecycle - initialize and cleanup resources."""
    # Initialize database on startup
    try:
        init_database()
        init_database(is_global=True)
    except Exception as e:
        print(f"Warning: Failed to initialize database: {e}")

    yield {}

    # Cleanup on shutdown
    close_all_connections()


# Create the MCP server
mcp = FastMCP(
    "omni_cortex",
    lifespan=lifespan,
)

# Register all tools
register_memory_tools(mcp)
register_activity_tools(mcp)
register_session_tools(mcp)
register_utility_tools(mcp)


# === MCP Resources ===

@mcp.resource("cortex://stats")
async def get_stats() -> str:
    """Get statistics about the Cortex database."""
    try:
        conn = init_database()
        cursor = conn.cursor()

        stats = {}

        # Count memories
        cursor.execute("SELECT COUNT(*) FROM memories")
        stats["total_memories"] = cursor.fetchone()[0]

        # Count by type
        cursor.execute("""
            SELECT type, COUNT(*) as cnt
            FROM memories
            GROUP BY type
            ORDER BY cnt DESC
        """)
        stats["memories_by_type"] = {row["type"]: row["cnt"] for row in cursor.fetchall()}

        # Count by status
        cursor.execute("""
            SELECT status, COUNT(*) as cnt
            FROM memories
            GROUP BY status
        """)
        stats["memories_by_status"] = {row["status"]: row["cnt"] for row in cursor.fetchall()}

        # Count activities
        cursor.execute("SELECT COUNT(*) FROM activities")
        stats["total_activities"] = cursor.fetchone()[0]

        # Count sessions
        cursor.execute("SELECT COUNT(*) FROM sessions")
        stats["total_sessions"] = cursor.fetchone()[0]

        import json
        return json.dumps(stats, indent=2)

    except Exception as e:
        return f"Error getting stats: {e}"


@mcp.resource("cortex://types")
async def get_memory_types() -> str:
    """Get available memory types with descriptions."""
    types = {
        "general": "General information or notes",
        "warning": "Warnings, cautions, things to avoid",
        "tip": "Tips, tricks, best practices",
        "config": "Configuration, settings, environment variables",
        "troubleshooting": "Problem solving, debugging guides",
        "code": "Code snippets, functions, algorithms",
        "error": "Errors, exceptions, failure cases",
        "solution": "Solutions to problems, fixes",
        "command": "CLI commands, terminal operations",
        "concept": "Definitions, explanations, concepts",
        "decision": "Decisions made, architectural choices",
    }
    import json
    return json.dumps(types, indent=2)


@mcp.resource("cortex://config")
async def get_config() -> str:
    """Get current Cortex configuration."""
    from .config import load_config

    config = load_config()
    import json
    return json.dumps({
        "schema_version": config.schema_version,
        "embedding_model": config.embedding_model,
        "embedding_enabled": config.embedding_enabled,
        "decay_rate_per_day": config.decay_rate_per_day,
        "freshness_review_days": config.freshness_review_days,
        "auto_provide_context": config.auto_provide_context,
        "context_depth": config.context_depth,
        "default_search_mode": config.default_search_mode,
        "global_sync_enabled": config.global_sync_enabled,
    }, indent=2)


@mcp.resource("cortex://tags")
async def get_tags() -> str:
    """Get all tags used in memories with usage counts."""
    try:
        conn = init_database()
        cursor = conn.cursor()

        # Query all memories and extract tags
        cursor.execute("SELECT tags FROM memories WHERE tags IS NOT NULL")

        import json
        tag_counts: dict[str, int] = {}

        for row in cursor.fetchall():
            tags_json = row["tags"]
            if tags_json:
                try:
                    tags = json.loads(tags_json)
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                except json.JSONDecodeError:
                    pass

        # Sort by count descending
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

        return json.dumps({
            "total_unique_tags": len(sorted_tags),
            "tags": [{"name": name, "count": count} for name, count in sorted_tags],
        }, indent=2)

    except Exception as e:
        return f"Error getting tags: {e}"


@mcp.resource("cortex://sessions/recent")
async def get_recent_sessions_resource() -> str:
    """Get recent sessions with summaries."""
    try:
        conn = init_database()
        from .models.session import get_recent_sessions, get_session_summary

        sessions = get_recent_sessions(conn, limit=10)

        import json
        result = []

        for session in sessions:
            session_data = {
                "id": session.id,
                "project_path": session.project_path,
                "started_at": session.started_at,
                "ended_at": session.ended_at,
                "summary": session.summary,
            }

            # Get summary if available
            summary = get_session_summary(conn, session.id)
            if summary:
                session_data["stats"] = {
                    "total_activities": summary.total_activities,
                    "memories_created": summary.total_memories_created,
                    "tools_used": summary.tools_used,
                    "key_learnings": summary.key_learnings,
                }

            result.append(session_data)

        return json.dumps({
            "total_sessions": len(result),
            "sessions": result,
        }, indent=2)

    except Exception as e:
        return f"Error getting recent sessions: {e}"


@mcp.resource("cortex://status")
async def get_cli_status() -> str:
    """Get current session status for CLI display.

    Provides real-time status information that can be used for:
    - Session timer display
    - Activity counts
    - Tool usage statistics
    - Memory creation stats

    This resource is designed to support future CLI status bar integration.
    """
    try:
        import json
        from datetime import datetime, timezone
        conn = init_database()
        cursor = conn.cursor()

        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session": None,
            "activity_summary": {},
            "memory_summary": {},
            "tool_stats": {},
        }

        # Get current/most recent session
        cursor.execute("""
            SELECT id, started_at, ended_at, duration_ms
            FROM sessions
            ORDER BY started_at DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            session_id = row["id"]
            started_at = row["started_at"]
            ended_at = row["ended_at"]
            duration_ms = row["duration_ms"]

            # Calculate session duration
            if started_at:
                try:
                    start_time = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)
                    elapsed_seconds = (now - start_time).total_seconds()
                    elapsed_minutes = int(elapsed_seconds / 60)
                    elapsed_hours = int(elapsed_minutes / 60)
                except Exception:
                    elapsed_seconds = 0
                    elapsed_minutes = 0
                    elapsed_hours = 0
            else:
                elapsed_seconds = elapsed_minutes = elapsed_hours = 0

            status["session"] = {
                "id": session_id,
                "started_at": started_at,
                "ended_at": ended_at,
                "is_active": ended_at is None,
                "elapsed_seconds": int(elapsed_seconds),
                "elapsed_minutes": elapsed_minutes,
                "elapsed_hours": elapsed_hours,
                "elapsed_display": f"{elapsed_hours}h {elapsed_minutes % 60}m" if elapsed_hours > 0 else f"{elapsed_minutes}m",
                "recorded_duration_ms": duration_ms,
            }

            # Get activity count for this session
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM activities
                WHERE session_id = ?
            """, (session_id,))
            activity_count = cursor.fetchone()["count"]

            # Get tool breakdown for this session
            cursor.execute("""
                SELECT tool_name, COUNT(*) as count, SUM(duration_ms) as total_ms
                FROM activities
                WHERE session_id = ? AND tool_name IS NOT NULL
                GROUP BY tool_name
                ORDER BY count DESC
                LIMIT 10
            """, (session_id,))
            tool_stats = {}
            for tool_row in cursor.fetchall():
                tool_stats[tool_row["tool_name"]] = {
                    "count": tool_row["count"],
                    "total_ms": tool_row["total_ms"],
                }

            status["activity_summary"] = {
                "session_activity_count": activity_count,
                "top_tools": tool_stats,
            }

            # Get memories created in this session
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM memories
                WHERE source_session_id = ?
            """, (session_id,))
            memories_created = cursor.fetchone()["count"]

            status["memory_summary"] = {
                "session_memories_created": memories_created,
            }

        # Get all-time totals
        cursor.execute("SELECT COUNT(*) FROM activities")
        status["totals"] = {
            "all_activities": cursor.fetchone()[0],
        }
        cursor.execute("SELECT COUNT(*) FROM memories")
        status["totals"]["all_memories"] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sessions")
        status["totals"]["all_sessions"] = cursor.fetchone()[0]

        # Get user message count if table exists
        try:
            cursor.execute("SELECT COUNT(*) FROM user_messages")
            status["totals"]["all_user_messages"] = cursor.fetchone()[0]
        except Exception:
            status["totals"]["all_user_messages"] = 0

        return json.dumps(status, indent=2)

    except Exception as e:
        import json
        return json.dumps({"error": str(e)})


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
