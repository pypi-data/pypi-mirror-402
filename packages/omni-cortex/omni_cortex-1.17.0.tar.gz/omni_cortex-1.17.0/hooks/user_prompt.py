#!/usr/bin/env python3
"""UserPromptSubmit hook - captures user messages for style analysis.

This hook is called by Claude Code when the user submits a prompt.
It logs the user message to the Cortex database for later style analysis.

Hook configuration for settings.json:
{
    "hooks": {
        "UserPromptSubmit": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "python hooks/user_prompt.py"
                    }
                ]
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

# Import shared session management
from session_utils import get_or_create_session


def get_db_path() -> Path:
    """Get the database path for the current project."""
    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    return Path(project_path) / ".omni-cortex" / "cortex.db"


def ensure_database(db_path: Path) -> sqlite3.Connection:
    """Ensure database exists and has user_messages table."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))

    # Check if user_messages table exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_messages'")
    if cursor.fetchone() is None:
        # Apply minimal schema for user_messages
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS user_messages (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TEXT NOT NULL,
                content TEXT NOT NULL,
                word_count INTEGER,
                char_count INTEGER,
                line_count INTEGER,
                has_code_blocks INTEGER DEFAULT 0,
                has_questions INTEGER DEFAULT 0,
                has_commands INTEGER DEFAULT 0,
                tone_indicators TEXT,
                project_path TEXT,
                metadata TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_user_messages_timestamp ON user_messages(timestamp DESC);
        """)
        conn.commit()

    return conn


def generate_id() -> str:
    """Generate a unique message ID."""
    timestamp_ms = int(datetime.now().timestamp() * 1000)
    random_hex = os.urandom(4).hex()
    return f"msg_{timestamp_ms}_{random_hex}"


def analyze_message(content: str) -> dict:
    """Analyze message characteristics for style profiling."""
    # Basic counts
    word_count = len(content.split())
    char_count = len(content)
    line_count = len(content.splitlines()) or 1

    # Detect code blocks
    has_code_blocks = 1 if re.search(r'```[\s\S]*?```|`[^`]+`', content) else 0

    # Detect questions
    has_questions = 1 if re.search(r'\?|^(what|how|why|when|where|who|which|can|could|would|should|is|are|do|does|did)\b', content, re.IGNORECASE | re.MULTILINE) else 0

    # Detect slash commands
    has_commands = 1 if content.strip().startswith('/') else 0

    # Tone indicators
    tone_indicators = []

    # Urgency markers
    if re.search(r'\b(urgent|asap|immediately|quick|fast|hurry)\b', content, re.IGNORECASE):
        tone_indicators.append("urgent")

    # Polite markers
    if re.search(r'\b(please|thanks|thank you|appreciate|kindly)\b', content, re.IGNORECASE):
        tone_indicators.append("polite")

    # Direct/imperative
    if re.match(r'^(fix|add|remove|update|change|create|delete|run|test|check|show|list|find)\b', content.strip(), re.IGNORECASE):
        tone_indicators.append("direct")

    # Questioning/exploratory
    if has_questions:
        tone_indicators.append("inquisitive")

    # Technical
    if re.search(r'\b(function|class|method|variable|api|database|server|error|bug|issue)\b', content, re.IGNORECASE):
        tone_indicators.append("technical")

    # Casual
    if re.search(r'\b(hey|hi|yo|cool|awesome|great|nice)\b', content, re.IGNORECASE):
        tone_indicators.append("casual")

    return {
        "word_count": word_count,
        "char_count": char_count,
        "line_count": line_count,
        "has_code_blocks": has_code_blocks,
        "has_questions": has_questions,
        "has_commands": has_commands,
        "tone_indicators": json.dumps(tone_indicators),
    }


def main():
    """Process UserPromptSubmit hook."""
    try:
        # Read input from stdin
        import select
        if sys.platform != "win32":
            ready, _, _ = select.select([sys.stdin], [], [], 5.0)
            if not ready:
                print(json.dumps({}))
                return

        raw_input = sys.stdin.read()
        if not raw_input or not raw_input.strip():
            print(json.dumps({}))
            return

        input_data = json.loads(raw_input)

        # Extract user prompt
        prompt = input_data.get("prompt", "")
        if not prompt or not prompt.strip():
            print(json.dumps({}))
            return

        # Skip very short messages (likely just commands)
        if len(prompt.strip()) < 3:
            print(json.dumps({}))
            return

        project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

        # Initialize database
        db_path = get_db_path()
        conn = ensure_database(db_path)

        # Get or create session
        session_id = get_or_create_session(conn, project_path)

        # Analyze message
        analysis = analyze_message(prompt)

        # Generate message ID
        message_id = generate_id()

        # Insert message record
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_messages (
                id, session_id, timestamp, content, word_count, char_count,
                line_count, has_code_blocks, has_questions, has_commands,
                tone_indicators, project_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                session_id,
                datetime.now(timezone.utc).isoformat(),
                prompt,
                analysis["word_count"],
                analysis["char_count"],
                analysis["line_count"],
                analysis["has_code_blocks"],
                analysis["has_questions"],
                analysis["has_commands"],
                analysis["tone_indicators"],
                project_path,
            ),
        )
        conn.commit()
        conn.close()

        # Return empty response (don't modify prompt)
        print(json.dumps({}))

    except Exception as e:
        # Hooks should never block - log error but continue
        # Don't print system message to avoid polluting user experience
        print(json.dumps({}))

    sys.exit(0)


if __name__ == "__main__":
    main()
