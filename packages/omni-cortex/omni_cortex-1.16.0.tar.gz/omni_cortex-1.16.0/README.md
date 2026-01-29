# Omni Cortex MCP

A universal memory system for Claude Code that combines activity logging with intelligent knowledge storage.

## What Is This?

**For AI/ML experts:** A dual-layer context system with activity provenance, hybrid semantic search (FTS5 + embeddings), and temporal importance decay. Think of it as **Git + Elasticsearch + a knowledge graph for AI context**.

**For developers:** It gives Claude Code a persistent, searchable memory that auto-logs everything and gets smarter over time. Like a **senior developer's institutional knowledge**—searchable, organized, and always available.

**For everyone:** It makes your AI assistant actually remember things. No more re-explaining your project every session.

### Why Not Just Use CLAUDE.md or Basic Memory?

| Feature | Claude Code | CLAUDE.md | Basic MCP | Omni-Cortex |
|---------|:-----------:|:---------:|:---------:|:-----------:|
| Persists between sessions | ❌ | ✅ | ✅ | ✅ |
| Auto-logs all activity | ❌ | ❌ | ❌ | ✅ |
| Hybrid search (keyword + semantic) | ❌ | ❌ | ❌ | ✅ |
| Auto-categorizes memories | ❌ | ❌ | ❌ | ✅ |
| Importance decay + access boosting | ❌ | ❌ | ❌ | ✅ |
| Session history & context | ❌ | ❌ | ❌ | ✅ |
| Memory relationships | ❌ | ❌ | ❌ | ✅ |
| Cross-project search | ❌ | ❌ | ❌ | ✅ |
| Visual dashboard | ❌ | ❌ | ❌ | ✅ |

**The difference:** Basic solutions are like sticky notes. Omni-Cortex is like having a trusted long-term employee who remembers everything, files it automatically, and hands you exactly what you need.

## Features

- **Zero Configuration**: Works out of the box - just install and run setup
- **Dual-Layer Storage**: Activity logging (audit trail) + Knowledge store (memories)
- **18 MCP Tools**: Full-featured API for memory management, activity tracking, session continuity, and cross-project search
- **Semantic Search**: AI-powered search using sentence-transformers (optional)
- **Hybrid Search**: Combines keyword (FTS5) + semantic search for best results
- **Full-Text Search**: SQLite FTS5-powered keyword search with smart ranking
- **Auto-Categorization**: Automatic memory type detection and tag suggestions
- **Session Continuity**: "Last time you were working on..." context
- **Importance Decay**: Frequently accessed memories naturally surface
- **Auto Activity Logging**: Automatically logs all tool calls via hooks

## Getting Started (5 Minutes)

A step-by-step guide to get Omni Cortex running on your machine.

### Prerequisites

- **Python 3.10+** - Check with `python --version`
- **Claude Code CLI** - The Anthropic CLI tool
- **pip** - Python package manager (comes with Python)

### Step 1: Install the Package

**Option A: From PyPI (Recommended for most users)**
```bash
pip install omni-cortex
```

**Option B: From Source (For development/contributions)**
```bash
git clone https://github.com/AllCytes/Omni-Cortex.git
cd Omni-Cortex
pip install -e ".[semantic]"
```

**Expected output:**
```
Successfully installed omni-cortex-1.7.1
```

### Step 2: Run the Setup

```bash
omni-cortex-setup
```

This automatically:
- Adds Omni Cortex as an MCP server in `~/.claude.json`
- Configures hooks in `~/.claude/settings.json` for activity logging

**Expected output:**
```
✓ MCP server configured
✓ Hooks configured
Setup complete! Restart Claude Code to activate.
```

### Step 3: Restart Claude Code

Close and reopen your Claude Code terminal. This loads the new MCP configuration.

### Step 4: Verify It's Working

In Claude Code, try storing a memory:

```
Ask Claude: "Remember that the database uses SQLite for storage"
```

Claude should use the `cortex_remember` tool. Then verify:

```
Ask Claude: "What do you remember about the database?"
```

Claude should use `cortex_recall` and find your memory.

### Step 5: Start the Dashboard (Optional)

The web dashboard lets you browse and search memories visually.

```bash
# Start the dashboard (opens http://localhost:5173)
omni-cortex-dashboard
```

Or manually:
```bash
# Terminal 1: Backend (uses dashboard's own venv)
cd dashboard/backend
.venv/Scripts/python -m uvicorn main:app --host 127.0.0.1 --port 8765 --reload

# Terminal 2: Frontend
cd dashboard/frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

**Note:** The dashboard has its own virtual environment at `dashboard/backend/.venv` with FastAPI and other web dependencies. This is separate from the project root `.venv` which contains the MCP server package.

### Troubleshooting

<details>
<summary><b>❌ "omni-cortex-setup" command not found</b></summary>

**Cause:** pip installed to a location not in your PATH.

**Solution:**
```bash
# Find where pip installed it
python -m omni_cortex.setup

# Or add Python scripts to PATH (Windows)
# Add %APPDATA%\Python\Python3x\Scripts to your PATH

# On macOS/Linux, ensure ~/.local/bin is in PATH
export PATH="$HOME/.local/bin:$PATH"
```
</details>

<details>
<summary><b>❌ Claude doesn't see cortex_* tools</b></summary>

**Cause:** MCP server not configured or Claude Code not restarted.

**Solution:**
1. Check `~/.claude.json` contains the `omni-cortex` MCP server entry
2. Fully close and reopen Claude Code (not just the terminal)
3. Run `omni-cortex-setup` again if needed
</details>

<details>
<summary><b>❌ "ModuleNotFoundError: No module named 'omni_cortex'"</b></summary>

**Cause:** Python environment mismatch.

**Solution:**
```bash
# Ensure you're using the same Python that pip used
which python  # or `where python` on Windows
pip show omni-cortex  # Check if installed

# Reinstall if needed
pip install --force-reinstall omni-cortex
```
</details>

<details>
<summary><b>❌ Dashboard won't start</b></summary>

**Cause:** Missing dependencies or port conflict.

**Solution:**
```bash
# Install backend dependencies
cd dashboard/backend
pip install -e .

# Check if port 8765 is in use
# Windows: netstat -ano | findstr :8765
# macOS/Linux: lsof -i :8765

# Use a different port if needed
uvicorn main:app --port 8766
```
</details>

<details>
<summary><b>❌ Semantic search not working</b></summary>

**Cause:** Semantic extras not installed.

**Solution:**
```bash
pip install omni-cortex[semantic]
```

First search will download the embedding model (~100MB).
</details>

---

## Installation (Detailed)

### Quick Install (Recommended)

```bash
# Install the package
pip install omni-cortex

# Run automatic setup (configures MCP server + hooks)
omni-cortex-setup
```

That's it! Omni Cortex will now:
- Automatically log all Claude Code tool calls
- Provide memory tools (cortex_remember, cortex_recall, etc.)
- Create a per-project database at `.omni-cortex/cortex.db`

### With Semantic Search

For AI-powered semantic search capabilities:

```bash
pip install omni-cortex[semantic]
omni-cortex-setup
```

### From Source

```bash
git clone https://github.com/AllCytes/Omni-Cortex.git
cd omni-cortex
pip install -e ".[semantic]"
python -m omni_cortex.setup
```

### Manual Configuration

If you prefer manual setup, add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "omni-cortex": {
      "command": "python",
      "args": ["-m", "omni_cortex.server"]
    }
  }
}
```

And optionally configure hooks in `~/.claude/settings.json` for activity logging:

```json
{
  "hooks": {
    "PreToolUse": [{
      "type": "command",
      "command": "python -m omni_cortex.hooks.pre_tool_use"
    }],
    "PostToolUse": [{
      "type": "command",
      "command": "python -m omni_cortex.hooks.post_tool_use"
    }]
  }
}
```

### Uninstall

```bash
omni-cortex-setup --uninstall
pip uninstall omni-cortex
```

## Tools

### Memory Tools (6)

| Tool | Description |
|------|-------------|
| `cortex_remember` | Store information with auto-categorization |
| `cortex_recall` | Search memories (modes: keyword, semantic, hybrid) |
| `cortex_list_memories` | List memories with filters and pagination |
| `cortex_update_memory` | Update memory content, tags, or status |
| `cortex_forget` | Delete a memory |
| `cortex_link_memories` | Create relationships between memories |

### Activity Tools (3)

| Tool | Description |
|------|-------------|
| `cortex_log_activity` | Manually log an activity |
| `cortex_get_activities` | Query the activity log |
| `cortex_get_timeline` | Get a chronological timeline |

### Session Tools (3)

| Tool | Description |
|------|-------------|
| `cortex_start_session` | Start a new session with context |
| `cortex_end_session` | End session and generate summary |
| `cortex_get_session_context` | Get context from previous sessions |

### Utility Tools (3)

| Tool | Description |
|------|-------------|
| `cortex_list_tags` | List all tags with usage counts |
| `cortex_review_memories` | Review and update memory freshness |
| `cortex_export` | Export data to markdown or JSON |

### Global Tools (3)

| Tool | Description |
|------|-------------|
| `cortex_global_search` | Search memories across all projects |
| `cortex_global_stats` | Get global index statistics |
| `cortex_sync_to_global` | Manually sync to global index |

## Memory Types

Memories are automatically categorized into:

- `general` - General notes and information
- `warning` - Cautions, things to avoid
- `tip` - Tips, tricks, best practices
- `config` - Configuration and settings
- `troubleshooting` - Debugging and problem-solving
- `code` - Code snippets and algorithms
- `error` - Error messages and failures
- `solution` - Solutions to problems
- `command` - CLI commands
- `concept` - Definitions and explanations
- `decision` - Architectural decisions

## Storage

- **Per-project**: `.omni-cortex/cortex.db` in your project directory
- **Global**: `~/.omni-cortex/global.db` for cross-project search

## Configuration

Create `.omni-cortex/config.yaml` in your project:

```yaml
schema_version: "1.0"
embedding_enabled: true
decay_rate_per_day: 0.5
freshness_review_days: 30
auto_provide_context: true
context_depth: 3
```

## Web Dashboard

A visual interface for browsing, searching, and managing your memories.

![Dashboard Preview](docs/images/dashboard-preview.png)

### Features
- **Memory Browser**: View, search, filter, and edit memories
- **Ask AI**: Chat with your memories using Gemini
- **Real-time Updates**: WebSocket-based live sync
- **Statistics**: Memory counts, types, tags distribution
- **Project Switcher**: Switch between project databases

### Quick Start

```bash
# Backend (requires Python 3.10+)
cd dashboard/backend
pip install -e .
uvicorn main:app --host 0.0.0.0 --port 8765 --reload

# Frontend (requires Node.js 18+)
cd dashboard/frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

### Ask AI Setup (Optional)

To enable the "Ask AI" chat feature, set your Gemini API key:

```bash
export GEMINI_API_KEY=your_api_key_here
```

See [dashboard/README.md](dashboard/README.md) for full documentation.

## Documentation

- [Tool Reference](docs/TOOLS.md) - Complete documentation for all 18 tools with examples
- [Configuration Guide](docs/CONFIGURATION.md) - Configuration options and troubleshooting
- **Teaching Materials** (PDF):
  - `docs/OmniCortex_QuickStart.pdf` - 3-page quick start guide
  - `docs/OmniCortex_FeatureComparison.pdf` - Comparison with basic memory MCPs
  - `docs/OmniCortex_Philosophy.pdf` - Design principles and inspiration
  - `docs/OmniCortex_CommandReference.pdf` - All tools with parameters

### Regenerating PDFs

To regenerate the teaching material PDFs:

```bash
# Requires reportlab
pip install reportlab

# Generate all 4 PDFs
python docs/create_pdfs.py
```

The PDFs use a light theme with blue/purple/green accents. Edit `docs/create_pdfs.py` to customize colors or content.

## Development

### Quick Setup (with Claude Code)

If you're using Claude Code, just run:

```bash
/dev-setup
```

This will guide you through setting up the development environment.

### Manual Setup

```bash
# Clone and install in editable mode
git clone https://github.com/AllCytes/Omni-Cortex.git
cd Omni-Cortex
pip install -e .

# Dashboard backend has its own venv (already included in repo)
# If missing, set it up:
cd dashboard/backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt  # Windows
# .venv/bin/pip install -r requirements.txt    # macOS/Linux
cd ../frontend && npm install
cd ../..

# Verify installation
omni-cortex --help
omni-cortex-dashboard --help
```

**Important**: Always use `pip install -e .` (editable mode) so changes are immediately reflected without reinstalling.

### Project Structure

```
omni-cortex/
├── .venv/                       # Project root venv (omni-cortex MCP package)
├── src/omni_cortex/             # MCP server source code
├── dashboard/
│   ├── backend/
│   │   ├── .venv/               # Dashboard backend venv (FastAPI, uvicorn)
│   │   ├── main.py              # FastAPI application
│   │   └── database.py          # Database queries
│   └── frontend/                # Vue 3 + Vite frontend
├── adws/                        # Agentic Development Workflows
├── specs/                       # Implementation plans
│   ├── todo/                    # Plans waiting to be built
│   └── done/                    # Completed plans
└── tests/                       # Unit tests
```

**Why two venvs?** The dashboard is a standalone web application that can be packaged/deployed separately from the MCP server. They have different dependencies (MCP server needs `mcp`, dashboard needs `fastapi`).

### Running Tests

```bash
pytest

# With coverage
pytest --cov=src/omni_cortex
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full development guidelines.

## Security

Omni Cortex v1.0.3 has been security reviewed:
- All SQL queries use parameterized statements
- Input validation via Pydantic models
- Model name validation prevents code injection
- YAML loading uses `safe_load()`

## License

MIT
