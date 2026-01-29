#!/usr/bin/env python3
"""Omni Cortex MCP Setup Script.

This script automatically configures Omni Cortex MCP for Claude Code:
1. Adds the MCP server to ~/.claude.json
2. Configures activity logging hooks in Claude's settings.json

Usage:
    python -m omni_cortex.setup
    # or
    python scripts/setup.py
"""

import json
import os
import sys
from pathlib import Path


def get_claude_config_path() -> Path:
    """Get the path to Claude's config file."""
    home = Path.home()
    return home / ".claude.json"


def get_claude_settings_path() -> Path:
    """Get the path to Claude Code's settings.json."""
    home = Path.home()

    # Check common locations
    if sys.platform == "win32":
        paths = [
            home / ".claude" / "settings.json",
            home / "AppData" / "Roaming" / "Claude" / "settings.json",
        ]
    else:
        paths = [
            home / ".claude" / "settings.json",
            home / ".config" / "claude" / "settings.json",
        ]

    for path in paths:
        if path.exists():
            return path

    # Default to .claude/settings.json
    return home / ".claude" / "settings.json"


def get_package_dir() -> Path:
    """Get the directory where omni-cortex is installed."""
    # Try to find the package
    try:
        import omni_cortex
        return Path(omni_cortex.__file__).parent.parent.parent
    except ImportError:
        # Fall back to script location
        return Path(__file__).parent.parent


def setup_mcp_server():
    """Add Omni Cortex MCP server to Claude's config."""
    config_path = get_claude_config_path()
    package_dir = get_package_dir()

    # Read existing config or create new
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        config = {}

    # Ensure mcpServers exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Add omni-cortex server
    config["mcpServers"]["omni-cortex"] = {
        "command": sys.executable,
        "args": ["-m", "omni_cortex.server"],
    }

    # Write config
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Added MCP server to {config_path}")
    return True


def setup_hooks():
    """Configure activity logging hooks in Claude's settings.json."""
    settings_path = get_claude_settings_path()
    package_dir = get_package_dir()

    # Find hooks directory
    hooks_dir = package_dir / "hooks"
    if not hooks_dir.exists():
        # Try relative to script
        hooks_dir = Path(__file__).parent.parent / "hooks"

    if not hooks_dir.exists():
        print(f"Warning: hooks directory not found at {hooks_dir}")
        return False

    # Read existing settings or create new
    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)
    else:
        settings = {}

    # Ensure hooks section exists
    if "hooks" not in settings:
        settings["hooks"] = {}

    # Get Python executable
    python_exe = sys.executable

    # Configure PreToolUse hook
    pre_tool_hook = {
        "type": "command",
        "command": f"{python_exe} {hooks_dir / 'pre_tool_use.py'}",
    }

    # Configure PostToolUse hook
    post_tool_hook = {
        "type": "command",
        "command": f"{python_exe} {hooks_dir / 'post_tool_use.py'}",
    }

    # Configure Stop hook
    stop_hook = {
        "type": "command",
        "command": f"{python_exe} {hooks_dir / 'stop.py'}",
    }

    # Add hooks (preserve existing hooks)
    if "PreToolUse" not in settings["hooks"]:
        settings["hooks"]["PreToolUse"] = []
    if not any("omni-cortex" in str(h.get("command", "")) or "pre_tool_use" in str(h.get("command", ""))
               for h in settings["hooks"]["PreToolUse"]):
        settings["hooks"]["PreToolUse"].append(pre_tool_hook)

    if "PostToolUse" not in settings["hooks"]:
        settings["hooks"]["PostToolUse"] = []
    if not any("omni-cortex" in str(h.get("command", "")) or "post_tool_use" in str(h.get("command", ""))
               for h in settings["hooks"]["PostToolUse"]):
        settings["hooks"]["PostToolUse"].append(post_tool_hook)

    if "Stop" not in settings["hooks"]:
        settings["hooks"]["Stop"] = []
    if not any("omni-cortex" in str(h.get("command", "")) or "stop.py" in str(h.get("command", ""))
               for h in settings["hooks"]["Stop"]):
        settings["hooks"]["Stop"].append(stop_hook)

    # Write settings
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"Configured hooks in {settings_path}")
    return True


def main():
    """Run the setup process."""
    print("=" * 50)
    print("Omni Cortex MCP Setup")
    print("=" * 50)
    print()

    # Step 1: Setup MCP server
    print("Step 1: Configuring MCP server...")
    if setup_mcp_server():
        print("  MCP server configured.")
    else:
        print("  Failed to configure MCP server.")

    print()

    # Step 2: Setup hooks
    print("Step 2: Configuring activity hooks...")
    if setup_hooks():
        print("  Hooks configured.")
    else:
        print("  Failed to configure hooks.")

    print()
    print("=" * 50)
    print("Setup complete!")
    print()
    print("Omni Cortex MCP is now ready to use.")
    print("Restart Claude Code for changes to take effect.")
    print()
    print("The MCP will automatically:")
    print("  - Log all tool calls to .omni-cortex/cortex.db")
    print("  - Provide cortex_remember/cortex_recall tools")
    print("  - Track sessions and activities")
    print()
    print("For semantic search, install:")
    print("  pip install omni-cortex[semantic]")
    print("=" * 50)


if __name__ == "__main__":
    main()
