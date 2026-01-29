#!/usr/bin/env python3
"""SubagentStop hook - logs when a subagent completes.

This hook is called when a subagent (spawned by the Task tool) finishes.
It logs the subagent completion and any results.

Hook configuration for settings.json:
{
    "hooks": {
        "SubagentStop": [
            {
                "type": "command",
                "command": "python hooks/subagent_stop.py"
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


def generate_id() -> str:
    """Generate a unique activity ID."""
    timestamp_ms = int(datetime.now().timestamp() * 1000)
    random_hex = os.urandom(4).hex()
    return f"act_{timestamp_ms}_{random_hex}"


def truncate(text: str, max_length: int = 10000) -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 20] + "\n... [truncated]"


def main():
    """Process SubagentStop hook."""
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)

        db_path = get_db_path()

        # Only log if database exists
        if not db_path.exists():
            print(json.dumps({}))
            return

        # Extract data from hook input
        subagent_id = input_data.get("subagent_id")
        subagent_type = input_data.get("subagent_type", "subagent")
        result = input_data.get("result", {})

        session_id = os.environ.get("CLAUDE_SESSION_ID")
        project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
        now = datetime.now(timezone.utc).isoformat()

        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Log the subagent completion as an activity
        cursor.execute(
            """
            INSERT INTO activities (
                id, session_id, agent_id, timestamp, event_type,
                tool_name, tool_output, success, project_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                generate_id(),
                session_id,
                subagent_id,
                now,
                "subagent_stop",
                f"subagent_{subagent_type}",
                truncate(json.dumps(result, default=str)),
                1,
                project_path,
            ),
        )

        # Update or create agent record
        cursor.execute(
            """
            INSERT INTO agents (id, name, type, first_seen, last_seen, total_activities)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(id) DO UPDATE SET
                last_seen = ?,
                total_activities = total_activities + 1
            """,
            (subagent_id, None, "subagent", now, now, now),
        )

        conn.commit()
        conn.close()

        print(json.dumps({}))

    except Exception as e:
        # Hooks should never block
        print(json.dumps({"systemMessage": f"Cortex subagent_stop: {e}"}))

    sys.exit(0)


if __name__ == "__main__":
    main()
