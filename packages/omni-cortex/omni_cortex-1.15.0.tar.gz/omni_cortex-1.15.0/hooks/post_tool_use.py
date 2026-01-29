#!/usr/bin/env python3
"""PostToolUse hook - logs tool result after execution.

This hook is called by Claude Code after each tool completes.
It logs the tool output, duration, and success/error status.

Hook configuration for settings.json:
{
    "hooks": {
        "PostToolUse": [
            {
                "type": "command",
                "command": "python hooks/post_tool_use.py"
            }
        ]
    }
}
"""

import json
import re
import sys
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

# Import shared session management
from session_utils import get_or_create_session


# === Tool Timing Management ===
# Read tool start timestamps and calculate duration

def get_timing_file_path() -> Path:
    """Get the path to the tool timing file."""
    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    return Path(project_path) / ".omni-cortex" / "tool_timing.json"


def load_timing_data() -> dict:
    """Load current timing data from file."""
    timing_file = get_timing_file_path()
    if not timing_file.exists():
        return {}
    try:
        with open(timing_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_timing_data(data: dict) -> None:
    """Save timing data to file."""
    timing_file = get_timing_file_path()
    timing_file.parent.mkdir(parents=True, exist_ok=True)
    with open(timing_file, "w") as f:
        json.dump(data, f)


def get_tool_duration(tool_name: str, agent_id: str = None) -> Tuple[Optional[int], Optional[str]]:
    """Get the duration for a tool execution and clean up.

    Args:
        tool_name: Name of the tool that finished
        agent_id: Optional agent ID

    Returns:
        Tuple of (duration_ms, activity_id) or (None, None) if not found
    """
    timing_data = load_timing_data()
    key = f"{tool_name}_{agent_id or 'main'}"

    if key not in timing_data:
        return None, None

    entry = timing_data[key]
    start_time_ms = entry.get("start_time_ms")
    activity_id = entry.get("activity_id")

    if not start_time_ms:
        return None, activity_id

    # Calculate duration
    end_time_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    duration_ms = end_time_ms - start_time_ms

    # Remove the entry (tool call complete)
    del timing_data[key]
    save_timing_data(timing_data)

    return duration_ms, activity_id


# Patterns for sensitive field names that should be redacted
SENSITIVE_FIELD_PATTERNS = [
    r'(?i)(api[_-]?key|apikey)',
    r'(?i)(password|passwd|pwd)',
    r'(?i)(secret|token|credential)',
    r'(?i)(auth[_-]?token|access[_-]?token)',
    r'(?i)(private[_-]?key|ssh[_-]?key)',
]


def redact_sensitive_fields(data: dict) -> dict:
    """Redact sensitive fields from a dictionary for safe logging.

    Recursively processes nested dicts and lists.
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        # Check if key matches sensitive patterns
        is_sensitive = any(
            re.search(pattern, str(key))
            for pattern in SENSITIVE_FIELD_PATTERNS
        )

        if is_sensitive:
            result[key] = '[REDACTED]'
        elif isinstance(value, dict):
            result[key] = redact_sensitive_fields(value)
        elif isinstance(value, list):
            result[key] = [
                redact_sensitive_fields(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


def get_db_path() -> Path:
    """Get the database path for the current project."""
    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    return Path(project_path) / ".omni-cortex" / "cortex.db"


def ensure_database(db_path: Path) -> sqlite3.Connection:
    """Ensure database exists and is initialized.

    Auto-creates the database and schema if it doesn't exist.
    This enables 'out of the box' functionality.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))

    # Check if schema exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities'")
    if cursor.fetchone() is None:
        # Apply minimal schema for activities (full schema applied by MCP)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS activities (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                agent_id TEXT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                tool_name TEXT,
                tool_input TEXT,
                tool_output TEXT,
                duration_ms INTEGER,
                success INTEGER DEFAULT 1,
                error_message TEXT,
                project_path TEXT,
                file_path TEXT,
                metadata TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_activities_tool ON activities(tool_name);
        """)
        conn.commit()

    return conn


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


def extract_skill_info(tool_input: dict, project_path: str) -> tuple:
    """Extract skill name and scope from Skill tool input.

    Returns:
        Tuple of (skill_name, command_scope)
    """
    try:
        skill_name = tool_input.get("skill", "")
        if not skill_name:
            return None, None

        # Determine scope by checking file locations
        project_cmd = Path(project_path) / ".claude" / "commands" / f"{skill_name}.md"
        if project_cmd.exists():
            return skill_name, "project"

        universal_cmd = Path.home() / ".claude" / "commands" / f"{skill_name}.md"
        if universal_cmd.exists():
            return skill_name, "universal"

        return skill_name, "unknown"
    except Exception:
        return None, None


def extract_mcp_server(tool_name: str) -> str:
    """Extract MCP server name from tool name pattern mcp__servername__toolname."""
    if not tool_name or not tool_name.startswith("mcp__"):
        return None

    parts = tool_name.split("__")
    if len(parts) >= 3:
        return parts[1]
    return None


def ensure_analytics_columns(conn: sqlite3.Connection) -> None:
    """Ensure command analytics columns exist in activities table."""
    cursor = conn.cursor()
    columns = cursor.execute("PRAGMA table_info(activities)").fetchall()
    column_names = [col[1] for col in columns]

    new_columns = [
        ("command_name", "TEXT"),
        ("command_scope", "TEXT"),
        ("mcp_server", "TEXT"),
        ("skill_name", "TEXT"),
        ("summary", "TEXT"),
        ("summary_detail", "TEXT"),
    ]

    for col_name, col_type in new_columns:
        if col_name not in column_names:
            cursor.execute(f"ALTER TABLE activities ADD COLUMN {col_name} {col_type}")

    conn.commit()


def generate_summary(tool_name: str, tool_input: dict, success: bool) -> tuple:
    """Generate short and detailed summaries for an activity.

    Returns:
        Tuple of (summary, summary_detail)
    """
    if not tool_name:
        return None, None

    input_data = tool_input if isinstance(tool_input, dict) else {}
    short = ""
    detail = ""

    if tool_name == "Read":
        path = input_data.get("file_path", "unknown")
        filename = Path(path).name if path else "file"
        short = f"Read file: {filename}"
        detail = f"Reading contents of {path}"

    elif tool_name == "Write":
        path = input_data.get("file_path", "unknown")
        filename = Path(path).name if path else "file"
        short = f"Write file: {filename}"
        detail = f"Writing/creating file at {path}"

    elif tool_name == "Edit":
        path = input_data.get("file_path", "unknown")
        filename = Path(path).name if path else "file"
        short = f"Edit file: {filename}"
        detail = f"Editing {path}"

    elif tool_name == "Bash":
        cmd = str(input_data.get("command", ""))[:50]
        short = f"Run: {cmd}..."
        detail = f"Executing: {input_data.get('command', 'unknown')}"

    elif tool_name == "Grep":
        pattern = input_data.get("pattern", "")
        short = f"Search: {pattern[:30]}"
        detail = f"Searching for pattern: {pattern}"

    elif tool_name == "Glob":
        pattern = input_data.get("pattern", "")
        short = f"Find files: {pattern[:30]}"
        detail = f"Finding files matching: {pattern}"

    elif tool_name == "Skill":
        skill = input_data.get("skill", "unknown")
        short = f"Run skill: /{skill}"
        detail = f"Executing slash command /{skill}"

    elif tool_name == "Task":
        desc = input_data.get("description", "task")
        short = f"Spawn agent: {desc[:30]}"
        detail = f"Launching sub-agent: {desc}"

    elif tool_name == "TodoWrite":
        todos = input_data.get("todos", [])
        count = len(todos) if isinstance(todos, list) else 0
        short = f"Update todo: {count} items"
        detail = f"Managing task list with {count} items"

    elif tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        server = parts[1] if len(parts) > 1 else "unknown"
        tool = parts[2] if len(parts) > 2 else tool_name
        short = f"MCP: {server}/{tool}"
        detail = f"Calling {tool} from MCP server {server}"

    else:
        short = f"Tool: {tool_name}"
        detail = f"Using tool {tool_name}"

    if not success:
        short = f"[FAILED] {short}"
        detail = f"[FAILED] {detail}"

    return short, detail


def main():
    """Process PostToolUse hook."""
    try:
        # Read all input at once (more reliable than json.load on stdin)
        raw_input = sys.stdin.read()
        if not raw_input or not raw_input.strip():
            print(json.dumps({}))
            return

        input_data = json.loads(raw_input)

        # Extract data from hook input
        # Note: Claude Code uses 'tool_response' not 'tool_output'
        tool_name = input_data.get("tool_name")
        tool_input = input_data.get("tool_input", {})
        tool_response = input_data.get("tool_response", {})  # Correct field name
        agent_id = input_data.get("agent_id")

        # Determine success/error from response content
        # Claude Code doesn't send 'is_error' - we must detect from response
        is_error = False
        error_message = None

        if isinstance(tool_response, dict):
            # Check for explicit error field
            if "error" in tool_response:
                is_error = True
                error_message = str(tool_response.get("error", ""))[:500]

            # For Bash: check stderr or error patterns in stdout
            elif tool_name == "Bash":
                stderr = tool_response.get("stderr", "")
                stdout = tool_response.get("stdout", "")

                # Check stderr for content (excluding common non-errors)
                if stderr and stderr.strip():
                    # Filter out common non-error stderr output
                    stderr_lower = stderr.lower()
                    non_error_patterns = ["warning:", "note:", "info:"]
                    if not any(p in stderr_lower for p in non_error_patterns):
                        is_error = True
                        error_message = stderr[:500]

                # Check stdout for common error patterns
                if not is_error and stdout:
                    error_patterns = [
                        "command not found",
                        "No such file or directory",
                        "Permission denied",
                        "fatal:",
                        "error:",
                        "Error:",
                        "FAILED",
                        "Cannot find",
                        "not recognized",
                        "Exit code 1",
                    ]
                    stdout_check = stdout[:1000]  # Check first 1000 chars
                    for pattern in error_patterns:
                        if pattern in stdout_check:
                            is_error = True
                            error_message = f"Error pattern detected: {pattern}"
                            break

            # For Read: check for file errors
            elif tool_name == "Read":
                if "error" in str(tool_response).lower():
                    is_error = True
                    error_message = "File read error"

        # Legacy fallback: also check tool_output for backwards compatibility
        tool_output = tool_response if tool_response else input_data.get("tool_output", {})

        # Skip logging our own tools to prevent recursion
        # MCP tools are named like "mcp__omni-cortex__cortex_remember"
        if tool_name and ("cortex_" in tool_name or "omni-cortex" in tool_name):
            print(json.dumps({}))
            return

        project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

        # Auto-initialize database (creates if not exists)
        db_path = get_db_path()
        conn = ensure_database(db_path)

        # Ensure analytics columns exist
        ensure_analytics_columns(conn)

        # Get or create session (auto-manages session lifecycle)
        session_id = get_or_create_session(conn, project_path)

        # Redact sensitive fields before logging
        safe_input = redact_sensitive_fields(tool_input) if isinstance(tool_input, dict) else tool_input
        safe_output = redact_sensitive_fields(tool_response) if isinstance(tool_response, dict) else tool_response

        # Extract command analytics
        skill_name = None
        command_scope = None
        mcp_server = None

        # Extract skill info from Skill tool calls
        if tool_name == "Skill" and isinstance(tool_input, dict):
            skill_name, command_scope = extract_skill_info(tool_input, project_path)

        # Extract MCP server from tool name (mcp__servername__toolname pattern)
        if tool_name and tool_name.startswith("mcp__"):
            mcp_server = extract_mcp_server(tool_name)

        # Generate summary for activity
        summary = None
        summary_detail = None
        try:
            summary, summary_detail = generate_summary(tool_name, safe_input, not is_error)
        except Exception:
            pass

        # Get tool duration from pre_tool_use timing data
        duration_ms, _ = get_tool_duration(tool_name, agent_id)

        # Insert activity record with analytics columns and duration
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO activities (
                id, session_id, agent_id, timestamp, event_type,
                tool_name, tool_input, tool_output, duration_ms, success, error_message, project_path,
                skill_name, command_scope, mcp_server, summary, summary_detail
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                generate_id(),
                session_id,
                agent_id,
                datetime.now(timezone.utc).isoformat(),
                "post_tool_use",
                tool_name,
                truncate(json.dumps(safe_input, default=str)),
                truncate(json.dumps(safe_output, default=str)),
                duration_ms,
                0 if is_error else 1,
                error_message,
                project_path,
                skill_name,
                command_scope,
                mcp_server,
                summary,
                summary_detail,
            ),
        )
        conn.commit()
        conn.close()

        # Return empty response (no modification)
        print(json.dumps({}))

    except Exception as e:
        # Hooks should never block - log error but continue
        print(json.dumps({"systemMessage": f"Cortex post_tool_use: {e}"}))

    sys.exit(0)


if __name__ == "__main__":
    main()
