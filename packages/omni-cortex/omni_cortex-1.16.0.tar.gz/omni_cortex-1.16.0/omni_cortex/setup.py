#!/usr/bin/env python3
"""Omni Cortex MCP Setup Module.

This module automatically configures Omni Cortex MCP for Claude Code:
1. Adds the MCP server to ~/.claude.json
2. Configures activity logging hooks in Claude's settings.json

Usage:
    python -m omni_cortex.setup
    # or after pip install:
    omni-cortex-setup
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
    return Path(__file__).parent.parent.parent


def get_hooks_dir() -> Path:
    """Get the hooks directory.

    Checks multiple locations for hooks:
    1. Development: <project>/hooks/
    2. Installed: <site-packages>/../share/omni-cortex/hooks/
    3. Installed: <prefix>/share/omni-cortex/hooks/
    """
    # Try development location
    package_dir = get_package_dir()
    hooks_dir = package_dir / "hooks"
    if hooks_dir.exists():
        return hooks_dir

    # Try relative to package
    import omni_cortex
    pkg_path = Path(omni_cortex.__file__).parent

    # Check various installed locations
    candidates = [
        pkg_path.parent.parent / "hooks",
        pkg_path.parent.parent / "share" / "omni-cortex" / "hooks",
        Path(sys.prefix) / "share" / "omni-cortex" / "hooks",
        Path(sys.base_prefix) / "share" / "omni-cortex" / "hooks",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Fall back to package dir even if it doesn't exist
    return package_dir / "hooks"


def setup_mcp_server() -> bool:
    """Add Omni Cortex MCP server to Claude's config."""
    config_path = get_claude_config_path()

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

    print(f"  Added MCP server to {config_path}")
    return True


def setup_hooks() -> bool:
    """Configure activity logging hooks in Claude's settings.json."""
    settings_path = get_claude_settings_path()
    hooks_dir = get_hooks_dir()

    if not hooks_dir.exists():
        print(f"  Warning: hooks directory not found at {hooks_dir}")
        print("  Skipping hooks configuration.")
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

    # Helper to check if hook already exists (handles both old and new format)
    def hook_exists(hook_list, script_name):
        for h in hook_list:
            # Check old format
            cmd = str(h.get("command", ""))
            if "omni-cortex" in cmd or script_name in cmd:
                return True
            # Check new format (matcher + hooks array)
            if "hooks" in h:
                for inner_hook in h.get("hooks", []):
                    inner_cmd = str(inner_hook.get("command", ""))
                    if "omni-cortex" in inner_cmd or script_name in inner_cmd:
                        return True
        return False

    # Configure hooks (new format with matcher and hooks array)
    hooks_config = {
        "PreToolUse": ("pre_tool_use.py", f'"{python_exe}" "{hooks_dir / "pre_tool_use.py"}"'),
        "PostToolUse": ("post_tool_use.py", f'"{python_exe}" "{hooks_dir / "post_tool_use.py"}"'),
        "Stop": ("stop.py", f'"{python_exe}" "{hooks_dir / "stop.py"}"'),
    }

    for hook_name, (script_name, command) in hooks_config.items():
        if hook_name not in settings["hooks"]:
            settings["hooks"][hook_name] = []

        if not hook_exists(settings["hooks"][hook_name], script_name):
            # New format: matcher + hooks array
            settings["hooks"][hook_name].append({
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": command,
                    }
                ]
            })

    # Write settings
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"  Configured hooks in {settings_path}")
    return True


def uninstall() -> bool:
    """Remove Omni Cortex from Claude's configuration."""
    config_path = get_claude_config_path()
    settings_path = get_claude_settings_path()

    # Remove from MCP servers
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)

        if "mcpServers" in config and "omni-cortex" in config["mcpServers"]:
            del config["mcpServers"]["omni-cortex"]
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            print(f"  Removed MCP server from {config_path}")

    # Remove hooks
    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)

        if "hooks" in settings:
            for hook_name in ["PreToolUse", "PostToolUse", "Stop"]:
                if hook_name in settings["hooks"]:
                    settings["hooks"][hook_name] = [
                        h for h in settings["hooks"][hook_name]
                        if "omni-cortex" not in str(h.get("command", ""))
                        and "pre_tool_use" not in str(h.get("command", ""))
                        and "post_tool_use" not in str(h.get("command", ""))
                        and "stop.py" not in str(h.get("command", ""))
                    ]

            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=2)
            print(f"  Removed hooks from {settings_path}")

    return True


def main():
    """Run the setup process."""
    args = sys.argv[1:]

    if "--uninstall" in args or "uninstall" in args:
        print("=" * 50)
        print("Omni Cortex MCP Uninstall")
        print("=" * 50)
        print()
        uninstall()
        print()
        print("Uninstall complete. Restart Claude Code.")
        return

    print("=" * 50)
    print("Omni Cortex MCP Setup")
    print("=" * 50)
    print()

    # Step 1: Setup MCP server
    print("Step 1: Configuring MCP server...")
    setup_mcp_server()

    print()

    # Step 2: Setup hooks
    print("Step 2: Configuring activity hooks...")
    setup_hooks()

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
    print("  pip install sentence-transformers")
    print()
    print("To uninstall: omni-cortex-setup --uninstall")
    print("=" * 50)


if __name__ == "__main__":
    main()
