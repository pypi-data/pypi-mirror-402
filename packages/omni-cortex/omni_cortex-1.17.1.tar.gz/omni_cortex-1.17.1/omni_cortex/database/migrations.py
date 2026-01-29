"""Database migration management for Omni Cortex."""

import sqlite3
from typing import Optional
from pathlib import Path

from .schema import SCHEMA_VERSION, get_schema_sql
from .connection import get_connection
from ..utils.timestamps import now_iso


# Migration definitions: version -> SQL
MIGRATIONS: dict[str, str] = {
    # Command analytics columns for slash command/skill tracking
    "1.1": """
        -- Add command analytics columns to activities table
        ALTER TABLE activities ADD COLUMN command_name TEXT;
        ALTER TABLE activities ADD COLUMN command_scope TEXT;
        ALTER TABLE activities ADD COLUMN mcp_server TEXT;
        ALTER TABLE activities ADD COLUMN skill_name TEXT;

        -- Create indexes for new columns
        CREATE INDEX IF NOT EXISTS idx_activities_command ON activities(command_name);
        CREATE INDEX IF NOT EXISTS idx_activities_mcp ON activities(mcp_server);
        CREATE INDEX IF NOT EXISTS idx_activities_skill ON activities(skill_name);
    """,
    # Natural language summary columns for activity display
    "1.2": """
        -- Add natural language summary columns to activities table
        ALTER TABLE activities ADD COLUMN summary TEXT;
        ALTER TABLE activities ADD COLUMN summary_detail TEXT;
    """,
    # Duration tracking columns for concrete time analysis
    "1.3": """
        -- Add duration tracking to sessions table
        ALTER TABLE sessions ADD COLUMN duration_ms INTEGER;

        -- Add duration tracking to session_summaries table
        ALTER TABLE session_summaries ADD COLUMN duration_ms INTEGER;
        ALTER TABLE session_summaries ADD COLUMN tool_duration_breakdown TEXT;

        -- Create index for duration queries
        CREATE INDEX IF NOT EXISTS idx_activities_duration ON activities(duration_ms);
        CREATE INDEX IF NOT EXISTS idx_sessions_duration ON sessions(duration_ms);
    """,
    # User message tracking for style analysis
    "1.4": """
        -- User messages table for tracking all user prompts
        CREATE TABLE IF NOT EXISTS user_messages (
            id TEXT PRIMARY KEY,                          -- msg_{timestamp}_{random}
            session_id TEXT,
            timestamp TEXT NOT NULL,                      -- ISO 8601
            content TEXT NOT NULL,                        -- The full user message
            word_count INTEGER,
            char_count INTEGER,
            line_count INTEGER,
            has_code_blocks INTEGER DEFAULT 0,
            has_questions INTEGER DEFAULT 0,
            has_commands INTEGER DEFAULT 0,               -- Starts with /
            tone_indicators TEXT,                         -- JSON: detected tone markers
            project_path TEXT,
            metadata TEXT,                                -- JSON for extensibility
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        -- User style profile for aggregated style analysis
        CREATE TABLE IF NOT EXISTS user_style_profiles (
            id TEXT PRIMARY KEY,                          -- profile_{timestamp}_{random}
            project_path TEXT,                            -- NULL for global profile
            total_messages INTEGER DEFAULT 0,
            avg_word_count REAL,
            avg_char_count REAL,
            common_phrases TEXT,                          -- JSON array of frequent phrases
            vocabulary_richness REAL,                     -- Type-token ratio
            formality_score REAL,                         -- 0-100 scale
            question_frequency REAL,                      -- % of messages with questions
            command_frequency REAL,                       -- % of messages starting with /
            code_block_frequency REAL,                    -- % with code blocks
            punctuation_style TEXT,                       -- JSON: punctuation patterns
            greeting_patterns TEXT,                       -- JSON: how user starts conversations
            instruction_style TEXT,                       -- JSON: how user gives instructions
            sample_messages TEXT,                         -- JSON array of representative samples
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata TEXT
        );

        -- Indexes for user message queries
        CREATE INDEX IF NOT EXISTS idx_user_messages_session ON user_messages(session_id);
        CREATE INDEX IF NOT EXISTS idx_user_messages_timestamp ON user_messages(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_user_messages_project ON user_messages(project_path);
        CREATE INDEX IF NOT EXISTS idx_user_style_project ON user_style_profiles(project_path);
    """,
}


def get_current_version(conn: sqlite3.Connection) -> Optional[str]:
    """Get the current schema version from the database."""
    try:
        cursor = conn.execute(
            "SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return None


def strip_sql_comments(sql: str) -> str:
    """Strip SQL comments from a statement while preserving inline comments in strings."""
    import re
    lines = sql.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove line comments (-- ...) but only if not inside a string
        # Simple approach: just strip everything after -- if not in CREATE TABLE definition
        # For CREATE TABLE, we need to keep the structure
        stripped = line.strip()
        if stripped.startswith('--'):
            continue  # Skip pure comment lines
        # Keep lines that have SQL content (even if they have trailing comments)
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)


def apply_migration(conn: sqlite3.Connection, version: str, sql: str) -> None:
    """Apply a single migration.

    Handles ALTER TABLE ADD COLUMN gracefully - if column exists, skips it.
    """
    # First, strip pure comment lines from the SQL
    sql = strip_sql_comments(sql)

    # Split into individual statements and apply each
    for statement in sql.strip().split(';'):
        statement = statement.strip()
        if not statement:
            continue

        # Skip if the remaining statement is just whitespace or pure comments
        non_comment_content = '\n'.join(
            line for line in statement.split('\n')
            if line.strip() and not line.strip().startswith('--')
        ).strip()
        if not non_comment_content:
            continue

        try:
            conn.execute(statement)
            conn.commit()  # Commit each statement so next one sees the change
        except sqlite3.OperationalError as e:
            error_msg = str(e).lower()
            # Ignore "duplicate column" errors - column already exists
            if "duplicate column" in error_msg:
                continue
            # Ignore "index already exists" errors
            if "already exists" in error_msg:
                continue
            # Ignore "no such column" for indexes on columns that may not exist yet
            # (will be created in a later migration)
            if "no such column" in error_msg and "CREATE INDEX" in statement.upper():
                continue
            # Ignore "table already exists" errors
            if "already exists" in error_msg:
                continue
            raise

    conn.execute(
        "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
        (version, now_iso())
    )
    conn.commit()


def migrate(db_path: Optional[Path] = None, is_global: bool = False) -> str:
    """Run all pending migrations.

    Returns:
        The final schema version
    """
    conn = get_connection(db_path, is_global)
    current = get_current_version(conn)

    if current is None:
        # Fresh database - apply full schema
        conn.executescript(get_schema_sql())
        conn.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION, now_iso())
        )
        conn.commit()
        return SCHEMA_VERSION

    # Apply pending migrations in order
    versions = sorted(MIGRATIONS.keys())
    for version in versions:
        if version > current:
            apply_migration(conn, version, MIGRATIONS[version])
            current = version

    return current


def needs_migration(conn: sqlite3.Connection) -> bool:
    """Check if database needs migration."""
    current = get_current_version(conn)
    if current is None:
        return True
    return any(v > current for v in MIGRATIONS.keys())
