"""Project configuration manager for user preferences."""

import json
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class RegisteredProject(BaseModel):
    """A manually registered project."""

    path: str
    display_name: Optional[str] = None
    added_at: datetime


class RecentProject(BaseModel):
    """A recently accessed project."""

    path: str
    last_accessed: datetime


class ProjectConfig(BaseModel):
    """User project configuration."""

    version: int = 1
    scan_directories: list[str] = []
    registered_projects: list[RegisteredProject] = []
    favorites: list[str] = []
    recent: list[RecentProject] = []


CONFIG_PATH = Path.home() / ".omni-cortex" / "projects.json"


def get_default_scan_dirs() -> list[str]:
    """Return platform-appropriate default scan directories."""
    home = Path.home()

    dirs = [
        str(home / "projects"),
        str(home / "Projects"),
        str(home / "code"),
        str(home / "Code"),
        str(home / "dev"),
        str(home / "workspace"),
    ]

    if platform.system() == "Windows":
        dirs.insert(0, "D:/Projects")

    return [d for d in dirs if Path(d).exists()]


def load_config() -> ProjectConfig:
    """Load config from disk, creating defaults if missing."""
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return ProjectConfig(**data)
        except Exception:
            pass

    # Create default config
    config = ProjectConfig(scan_directories=get_default_scan_dirs())
    save_config(config)
    return config


def save_config(config: ProjectConfig) -> None:
    """Save config to disk."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(config.model_dump_json(indent=2), encoding="utf-8")


def add_registered_project(path: str, display_name: Optional[str] = None) -> bool:
    """Register a new project by path."""
    config = load_config()

    # Validate path has cortex.db
    db_path = Path(path) / ".omni-cortex" / "cortex.db"
    if not db_path.exists():
        return False

    # Check if already registered
    if any(p.path == path for p in config.registered_projects):
        return False

    config.registered_projects.append(
        RegisteredProject(path=path, display_name=display_name, added_at=datetime.now())
    )
    save_config(config)
    return True


def remove_registered_project(path: str) -> bool:
    """Remove a registered project."""
    config = load_config()
    original_len = len(config.registered_projects)
    config.registered_projects = [
        p for p in config.registered_projects if p.path != path
    ]

    if len(config.registered_projects) < original_len:
        save_config(config)
        return True
    return False


def toggle_favorite(path: str) -> bool:
    """Toggle favorite status for a project. Returns new favorite status."""
    config = load_config()

    if path in config.favorites:
        config.favorites.remove(path)
        is_favorite = False
    else:
        config.favorites.append(path)
        is_favorite = True

    save_config(config)
    return is_favorite


def update_recent(path: str) -> None:
    """Update recent projects list."""
    config = load_config()

    # Remove if already in list
    config.recent = [r for r in config.recent if r.path != path]

    # Add to front
    config.recent.insert(0, RecentProject(path=path, last_accessed=datetime.now()))

    # Keep only last 10
    config.recent = config.recent[:10]

    save_config(config)


def add_scan_directory(directory: str) -> bool:
    """Add a directory to scan list."""
    config = load_config()

    # Expand user path
    expanded = str(Path(directory).expanduser())

    if not Path(expanded).is_dir():
        return False

    if expanded not in config.scan_directories:
        config.scan_directories.append(expanded)
        save_config(config)
        return True
    return False


def remove_scan_directory(directory: str) -> bool:
    """Remove a directory from scan list."""
    config = load_config()

    if directory in config.scan_directories:
        config.scan_directories.remove(directory)
        save_config(config)
        return True
    return False
