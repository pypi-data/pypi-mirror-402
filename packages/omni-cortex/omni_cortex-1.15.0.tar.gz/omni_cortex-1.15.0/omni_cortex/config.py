"""Configuration management for Omni Cortex."""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import yaml


@dataclass
class CortexConfig:
    """Configuration settings for Omni Cortex."""

    # Database
    schema_version: str = "1.0"

    # Embedding (disabled by default - model loading can be slow)
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_enabled: bool = False

    # Decay
    decay_rate_per_day: float = 0.5
    freshness_review_days: int = 30

    # Output
    max_output_truncation: int = 10000
    max_tool_input_size: int = 10000

    # Session
    auto_provide_context: bool = True
    context_depth: int = 3

    # Search (default to keyword since embeddings are disabled by default)
    default_search_mode: str = "keyword"

    # Global
    global_sync_enabled: bool = True
    api_fallback_enabled: bool = False
    api_key: str = ""


def get_project_path() -> Path:
    """Get the current project path from environment or cwd."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))


def get_project_db_dir() -> Path:
    """Get the project-local .omni-cortex directory."""
    return get_project_path() / ".omni-cortex"


def get_project_db_path() -> Path:
    """Get the path to the project database."""
    return get_project_db_dir() / "cortex.db"


def get_global_db_dir() -> Path:
    """Get the global ~/.omni-cortex directory."""
    return Path.home() / ".omni-cortex"


def get_global_db_path() -> Path:
    """Get the path to the global database."""
    return get_global_db_dir() / "global.db"


def get_session_id() -> Optional[str]:
    """Get the current session ID from environment."""
    return os.environ.get("CLAUDE_SESSION_ID")


def load_config(project_path: Optional[Path] = None) -> CortexConfig:
    """Load configuration from project and global config files.

    Priority: project config > global config > defaults
    """
    config = CortexConfig()

    # Load global config
    global_config_path = get_global_db_dir() / "config.yaml"
    if global_config_path.exists():
        try:
            with open(global_config_path, "r") as f:
                global_cfg = yaml.safe_load(f) or {}
                _apply_config(config, global_cfg)
        except Exception:
            pass

    # Load project config
    if project_path is None:
        project_path = get_project_path()
    project_config_path = project_path / ".omni-cortex" / "config.yaml"
    if project_config_path.exists():
        try:
            with open(project_config_path, "r") as f:
                project_cfg = yaml.safe_load(f) or {}
                _apply_config(config, project_cfg)
        except Exception:
            pass

    return config


def _apply_config(config: CortexConfig, data: dict) -> None:
    """Apply configuration data to config object."""
    for key, value in data.items():
        if hasattr(config, key) and value is not None:
            setattr(config, key, value)


def save_config(config: CortexConfig, project: bool = True) -> None:
    """Save configuration to file.

    Args:
        config: Configuration to save
        project: If True, save to project config; otherwise global
    """
    if project:
        config_dir = get_project_db_dir()
    else:
        config_dir = get_global_db_dir()

    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"

    data = {
        "schema_version": config.schema_version,
        "embedding_model": config.embedding_model,
        "embedding_enabled": config.embedding_enabled,
        "decay_rate_per_day": config.decay_rate_per_day,
        "freshness_review_days": config.freshness_review_days,
        "max_output_truncation": config.max_output_truncation,
        "auto_provide_context": config.auto_provide_context,
        "context_depth": config.context_depth,
        "default_search_mode": config.default_search_mode,
        "global_sync_enabled": config.global_sync_enabled,
    }

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
