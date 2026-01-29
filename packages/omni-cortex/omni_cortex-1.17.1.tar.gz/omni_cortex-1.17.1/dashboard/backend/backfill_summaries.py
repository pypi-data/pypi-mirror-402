"""Backfill utility for generating activity summaries.

This module provides functions to retroactively generate natural language
summaries for existing activity records that don't have them.
"""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Optional

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from database import get_write_connection, ensure_migrations


def generate_activity_summary(
    tool_name: Optional[str],
    tool_input: Optional[str],
    success: bool,
    file_path: Optional[str],
    event_type: str,
) -> tuple[str, str]:
    """Generate natural language summary for an activity.

    Returns:
        tuple of (short_summary, detailed_summary)
    """
    short = ""
    detail = ""

    # Parse tool input if available
    input_data = {}
    if tool_input:
        try:
            input_data = json.loads(tool_input)
        except (json.JSONDecodeError, TypeError):
            pass

    # Generate summaries based on tool type
    if tool_name == "Read":
        path = input_data.get("file_path", file_path or "unknown file")
        filename = Path(path).name if path else "file"
        short = f"Read file: {filename}"
        detail = f"Reading contents of {path}"

    elif tool_name == "Write":
        path = input_data.get("file_path", file_path or "unknown file")
        filename = Path(path).name if path else "file"
        short = f"Write file: {filename}"
        detail = f"Writing/creating file at {path}"

    elif tool_name == "Edit":
        path = input_data.get("file_path", file_path or "unknown file")
        filename = Path(path).name if path else "file"
        short = f"Edit file: {filename}"
        detail = f"Editing {path} - replacing text content"

    elif tool_name == "Bash":
        cmd = input_data.get("command", "")[:50]
        short = f"Run command: {cmd}..."
        detail = f"Executing bash command: {input_data.get('command', 'unknown')}"

    elif tool_name == "Grep":
        pattern = input_data.get("pattern", "")
        short = f"Search for: {pattern[:30]}"
        detail = f"Searching codebase for pattern: {pattern}"

    elif tool_name == "Glob":
        pattern = input_data.get("pattern", "")
        short = f"Find files: {pattern[:30]}"
        detail = f"Finding files matching pattern: {pattern}"

    elif tool_name == "Skill":
        skill = input_data.get("skill", "unknown")
        short = f"Run skill: /{skill}"
        detail = f"Executing slash command /{skill}"

    elif tool_name == "Task":
        desc = input_data.get("description", "task")
        short = f"Spawn agent: {desc[:30]}"
        detail = f"Launching sub-agent for: {input_data.get('prompt', desc)[:100]}"

    elif tool_name == "WebSearch":
        query = input_data.get("query", "")
        short = f"Web search: {query[:30]}"
        detail = f"Searching the web for: {query}"

    elif tool_name == "WebFetch":
        url = input_data.get("url", "")
        short = f"Fetch URL: {url[:40]}"
        detail = f"Fetching content from: {url}"

    elif tool_name == "TodoWrite":
        todos = input_data.get("todos", [])
        count = len(todos) if isinstance(todos, list) else 0
        short = f"Update todo list: {count} items"
        detail = f"Managing task list with {count} items"

    elif tool_name == "AskUserQuestion":
        questions = input_data.get("questions", [])
        count = len(questions) if isinstance(questions, list) else 1
        short = f"Ask user: {count} question(s)"
        detail = f"Prompting user for input with {count} question(s)"

    elif tool_name and tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        server = parts[1] if len(parts) > 1 else "unknown"
        tool = parts[2] if len(parts) > 2 else tool_name
        short = f"MCP call: {server}/{tool}"
        detail = f"Calling {tool} tool from MCP server {server}"

    elif tool_name == "cortex_remember" or (tool_name and "remember" in tool_name.lower()):
        params = input_data.get("params", {})
        content = params.get("content", "") if isinstance(params, dict) else ""
        short = f"Store memory: {content[:30]}..." if content else "Store memory"
        detail = f"Saving to memory system: {content[:100]}" if content else "Saving to memory system"

    elif tool_name == "cortex_recall" or (tool_name and "recall" in tool_name.lower()):
        params = input_data.get("params", {})
        query = params.get("query", "") if isinstance(params, dict) else ""
        short = f"Recall: {query[:30]}" if query else "Recall memories"
        detail = f"Searching memories for: {query}" if query else "Retrieving memories"

    elif tool_name == "NotebookEdit":
        path = input_data.get("notebook_path", "")
        filename = Path(path).name if path else "notebook"
        short = f"Edit notebook: {filename}"
        detail = f"Editing Jupyter notebook {path}"

    else:
        short = f"{event_type}: {tool_name or 'unknown'}"
        detail = f"Activity type {event_type} with tool {tool_name}"

    # Add status suffix for failures
    if not success:
        short = f"[FAILED] {short}"
        detail = f"[FAILED] {detail}"

    return short, detail


def backfill_activity_summaries(db_path: str) -> int:
    """Generate summaries for activities that don't have them.

    Args:
        db_path: Path to the SQLite database

    Returns:
        Number of activities updated
    """
    # First ensure migrations are applied
    ensure_migrations(db_path)

    conn = get_write_connection(db_path)

    # Check if summary column exists
    columns = conn.execute("PRAGMA table_info(activities)").fetchall()
    column_names = {col[1] for col in columns}

    if "summary" not in column_names:
        print(f"[Backfill] Summary column not found in {db_path}, skipping")
        conn.close()
        return 0

    cursor = conn.execute("""
        SELECT id, tool_name, tool_input, success, file_path, event_type
        FROM activities
        WHERE summary IS NULL OR summary = ''
    """)

    count = 0
    for row in cursor.fetchall():
        short, detail = generate_activity_summary(
            row["tool_name"],
            row["tool_input"],
            bool(row["success"]),
            row["file_path"],
            row["event_type"],
        )

        conn.execute(
            """
            UPDATE activities
            SET summary = ?, summary_detail = ?
            WHERE id = ?
            """,
            (short, detail, row["id"]),
        )
        count += 1

        if count % 100 == 0:
            conn.commit()
            print(f"[Backfill] Processed {count} activities...")

    conn.commit()
    conn.close()
    return count


def backfill_mcp_servers(db_path: str) -> int:
    """Extract and populate mcp_server for existing activities.

    Args:
        db_path: Path to the SQLite database

    Returns:
        Number of activities updated
    """
    # First ensure migrations are applied
    ensure_migrations(db_path)

    conn = get_write_connection(db_path)

    # Check if mcp_server column exists
    columns = conn.execute("PRAGMA table_info(activities)").fetchall()
    column_names = {col[1] for col in columns}

    if "mcp_server" not in column_names:
        print(f"[Backfill] mcp_server column not found in {db_path}, skipping")
        conn.close()
        return 0

    cursor = conn.execute("""
        SELECT id, tool_name FROM activities
        WHERE tool_name LIKE 'mcp__%'
          AND (mcp_server IS NULL OR mcp_server = '')
    """)

    count = 0
    for row in cursor.fetchall():
        parts = row["tool_name"].split("__")
        if len(parts) >= 2:
            server = parts[1]
            conn.execute(
                "UPDATE activities SET mcp_server = ? WHERE id = ?",
                (server, row["id"]),
            )
            count += 1

    conn.commit()
    conn.close()
    return count


def backfill_all(db_path: str) -> dict:
    """Run all backfill operations on a database.

    Args:
        db_path: Path to the SQLite database

    Returns:
        Dictionary with counts of updated records
    """
    print(f"[Backfill] Starting backfill for {db_path}")

    results = {
        "summaries": backfill_activity_summaries(db_path),
        "mcp_servers": backfill_mcp_servers(db_path),
    }

    print(f"[Backfill] Complete: {results['summaries']} summaries, {results['mcp_servers']} MCP servers")
    return results


if __name__ == "__main__":
    # Allow running from command line with database path as argument
    if len(sys.argv) < 2:
        print("Usage: python backfill_summaries.py <path-to-database>")
        sys.exit(1)

    db_path = sys.argv[1]
    if not Path(db_path).exists():
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    results = backfill_all(db_path)
    print(f"Backfill complete: {results}")
