"""Database schema definitions for Omni Cortex."""

SCHEMA_VERSION = "1.0"

# Main schema SQL
SCHEMA_SQL = """
-- ============================================
-- OMNI CORTEX MCP DATABASE SCHEMA v1.0
-- ============================================

-- Sessions Table
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,                          -- sess_{timestamp}_{random}
    project_path TEXT NOT NULL,
    started_at TEXT NOT NULL,                     -- ISO 8601
    ended_at TEXT,
    summary TEXT,
    tags TEXT,                                    -- JSON array
    metadata TEXT                                 -- JSON object
);

-- Agents Table
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,                          -- Agent ID from Claude Code
    name TEXT,
    type TEXT NOT NULL DEFAULT 'main',            -- main, subagent, tool
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    total_activities INTEGER DEFAULT 0,
    metadata TEXT
);

-- Activities Table (Layer 1)
CREATE TABLE IF NOT EXISTS activities (
    id TEXT PRIMARY KEY,                          -- act_{timestamp}_{random}
    session_id TEXT,
    agent_id TEXT,
    timestamp TEXT NOT NULL,                      -- ISO 8601 with timezone
    event_type TEXT NOT NULL,                     -- pre_tool_use, post_tool_use, etc.
    tool_name TEXT,
    tool_input TEXT,                              -- JSON (truncated to 10KB)
    tool_output TEXT,                             -- JSON (truncated to 10KB)
    duration_ms INTEGER,
    success INTEGER DEFAULT 1,
    error_message TEXT,
    project_path TEXT,
    file_path TEXT,
    metadata TEXT,
    -- Command analytics columns (v1.1)
    command_name TEXT,
    command_scope TEXT,
    mcp_server TEXT,
    skill_name TEXT,
    -- Natural language summaries (v1.2)
    summary TEXT,
    summary_detail TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Memories Table (Layer 2)
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,                          -- mem_{timestamp}_{random}
    content TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'general',
    tags TEXT,                                    -- JSON array
    context TEXT,

    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_accessed TEXT NOT NULL,
    last_verified TEXT,

    -- Usage
    access_count INTEGER DEFAULT 0,

    -- Importance/Decay
    importance_score REAL DEFAULT 50.0,           -- 0-100
    manual_importance INTEGER,                    -- User override

    -- Freshness
    status TEXT DEFAULT 'fresh',                  -- fresh, needs_review, outdated, archived

    -- Attribution
    source_session_id TEXT,
    source_agent_id TEXT,
    source_activity_id TEXT,

    -- Project
    project_path TEXT,
    file_context TEXT,                            -- JSON array

    -- Embedding
    has_embedding INTEGER DEFAULT 0,

    metadata TEXT,

    FOREIGN KEY (source_session_id) REFERENCES sessions(id),
    FOREIGN KEY (source_agent_id) REFERENCES agents(id),
    FOREIGN KEY (source_activity_id) REFERENCES activities(id)
);

-- FTS5 for Full-Text Search
CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    content, context, tags,
    content=memories,
    content_rowid=rowid,
    tokenize='porter unicode61'
);

-- Triggers to keep FTS in sync with memories table
CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, content, context, tags)
    VALUES (NEW.rowid, NEW.content, NEW.context, NEW.tags);
END;

CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content, context, tags)
    VALUES ('delete', OLD.rowid, OLD.content, OLD.context, OLD.tags);
END;

CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content, context, tags)
    VALUES ('delete', OLD.rowid, OLD.content, OLD.context, OLD.tags);
    INSERT INTO memories_fts(rowid, content, context, tags)
    VALUES (NEW.rowid, NEW.content, NEW.context, NEW.tags);
END;

-- Memory Relationships
CREATE TABLE IF NOT EXISTS memory_relationships (
    id TEXT PRIMARY KEY,
    source_memory_id TEXT NOT NULL,
    target_memory_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,              -- related_to, supersedes, derived_from, contradicts
    strength REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (source_memory_id) REFERENCES memories(id) ON DELETE CASCADE,
    FOREIGN KEY (target_memory_id) REFERENCES memories(id) ON DELETE CASCADE,
    UNIQUE(source_memory_id, target_memory_id, relationship_type)
);

-- Activity-Memory Links
CREATE TABLE IF NOT EXISTS activity_memory_links (
    activity_id TEXT NOT NULL,
    memory_id TEXT NOT NULL,
    link_type TEXT NOT NULL,                      -- created, accessed, updated, referenced
    created_at TEXT NOT NULL,
    PRIMARY KEY (activity_id, memory_id, link_type),
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

-- Embeddings
CREATE TABLE IF NOT EXISTS embeddings (
    id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL UNIQUE,
    model_name TEXT NOT NULL,                     -- 'all-MiniLM-L6-v2'
    vector BLOB NOT NULL,                         -- float32 array
    dimensions INTEGER NOT NULL,                  -- 384
    created_at TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

-- Session Summaries
CREATE TABLE IF NOT EXISTS session_summaries (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    key_learnings TEXT,                           -- JSON array
    key_decisions TEXT,                           -- JSON array
    key_errors TEXT,                              -- JSON array
    files_modified TEXT,                          -- JSON array
    tools_used TEXT,                              -- JSON object
    total_activities INTEGER DEFAULT 0,
    total_memories_created INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Configuration
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Schema Migrations
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_activities_session ON activities(session_id);
CREATE INDEX IF NOT EXISTS idx_activities_agent ON activities(agent_id);
CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_activities_tool ON activities(tool_name);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(status);
CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project_path);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_memories_accessed ON memories(last_accessed DESC);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_relationships_source ON memory_relationships(source_memory_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON memory_relationships(target_memory_id);
"""


def get_schema_sql() -> str:
    """Get the complete schema SQL."""
    return SCHEMA_SQL
