#!/usr/bin/env python3
"""Stop hook - logs session end when Claude Code stops.

This hook is called when Claude Code exits or the session ends.
It finalizes the session and generates a summary.

Hook configuration for settings.json:
{
    "hooks": {
        "Stop": [
            {
                "type": "command",
                "command": "python hooks/stop.py"
            }
        ]
    }
}
"""

import json
import sys
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def get_db_path() -> Path:
    """Get the database path for the current project."""
    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    return Path(project_path) / ".omni-cortex" / "cortex.db"


def generate_id(prefix: str) -> str:
    """Generate a unique ID."""
    timestamp_ms = int(datetime.now().timestamp() * 1000)
    random_hex = os.urandom(4).hex()
    return f"{prefix}_{timestamp_ms}_{random_hex}"


def main():
    """Process Stop hook."""
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)

        db_path = get_db_path()

        # Only process if database exists
        if not db_path.exists():
            print(json.dumps({}))
            return

        session_id = os.environ.get("CLAUDE_SESSION_ID")
        if not session_id:
            print(json.dumps({}))
            return

        now = datetime.now(timezone.utc).isoformat()

        # Connect to database
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if session exists
        cursor.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
        if not cursor.fetchone():
            print(json.dumps({}))
            conn.close()
            return

        # Get session start time for duration calculation
        cursor.execute("SELECT started_at FROM sessions WHERE id = ?", (session_id,))
        session_row = cursor.fetchone()
        session_duration_ms = None

        if session_row and session_row["started_at"]:
            try:
                started_at = session_row["started_at"]
                started_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                ended_dt = datetime.now(timezone.utc)
                session_duration_ms = int((ended_dt - started_dt).total_seconds() * 1000)
            except (ValueError, TypeError):
                pass

        # End the session with duration
        cursor.execute(
            "UPDATE sessions SET ended_at = ?, duration_ms = ? WHERE id = ? AND ended_at IS NULL",
            (now, session_duration_ms, session_id),
        )

        # Gather session statistics
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM activities WHERE session_id = ?",
            (session_id,),
        )
        total_activities = cursor.fetchone()["cnt"]

        cursor.execute(
            "SELECT COUNT(*) as cnt FROM memories WHERE source_session_id = ?",
            (session_id,),
        )
        total_memories = cursor.fetchone()["cnt"]

        # Get tools used
        cursor.execute(
            """
            SELECT tool_name, COUNT(*) as cnt
            FROM activities
            WHERE session_id = ? AND tool_name IS NOT NULL
            GROUP BY tool_name
            """,
            (session_id,),
        )
        tools_used = {row["tool_name"]: row["cnt"] for row in cursor.fetchall()}

        # Get files modified
        cursor.execute(
            """
            SELECT DISTINCT file_path
            FROM activities
            WHERE session_id = ? AND file_path IS NOT NULL
            """,
            (session_id,),
        )
        files_modified = [row["file_path"] for row in cursor.fetchall()]

        # Get errors
        cursor.execute(
            """
            SELECT error_message
            FROM activities
            WHERE session_id = ? AND success = 0 AND error_message IS NOT NULL
            LIMIT 10
            """,
            (session_id,),
        )
        key_errors = [row["error_message"] for row in cursor.fetchall()]

        # Create or update summary
        cursor.execute(
            "SELECT id FROM session_summaries WHERE session_id = ?",
            (session_id,),
        )
        existing = cursor.fetchone()

        # Calculate tool duration breakdown from activities
        cursor.execute(
            """
            SELECT tool_name, SUM(duration_ms) as total_ms, COUNT(*) as cnt
            FROM activities
            WHERE session_id = ? AND tool_name IS NOT NULL AND duration_ms IS NOT NULL
            GROUP BY tool_name
            """,
            (session_id,),
        )
        tool_duration_breakdown = {
            row["tool_name"]: {"total_ms": row["total_ms"], "count": row["cnt"]}
            for row in cursor.fetchall()
        }

        if existing:
            cursor.execute(
                """
                UPDATE session_summaries
                SET key_errors = ?, files_modified = ?, tools_used = ?,
                    total_activities = ?, total_memories_created = ?,
                    duration_ms = ?, tool_duration_breakdown = ?
                WHERE session_id = ?
                """,
                (
                    json.dumps(key_errors) if key_errors else None,
                    json.dumps(files_modified) if files_modified else None,
                    json.dumps(tools_used) if tools_used else None,
                    total_activities,
                    total_memories,
                    session_duration_ms,
                    json.dumps(tool_duration_breakdown) if tool_duration_breakdown else None,
                    session_id,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO session_summaries (
                    id, session_id, key_errors, files_modified, tools_used,
                    total_activities, total_memories_created, created_at,
                    duration_ms, tool_duration_breakdown
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    generate_id("sum"),
                    session_id,
                    json.dumps(key_errors) if key_errors else None,
                    json.dumps(files_modified) if files_modified else None,
                    json.dumps(tools_used) if tools_used else None,
                    total_activities,
                    total_memories,
                    now,
                    session_duration_ms,
                    json.dumps(tool_duration_breakdown) if tool_duration_breakdown else None,
                ),
            )

        conn.commit()
        conn.close()

        print(json.dumps({}))

    except Exception as e:
        # Hooks should never block
        print(json.dumps({"systemMessage": f"Cortex stop: {e}"}))

    sys.exit(0)


if __name__ == "__main__":
    main()
