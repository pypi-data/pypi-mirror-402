"""Scanner to discover all omni-cortex databases on the system."""

import sqlite3
from datetime import datetime
from pathlib import Path

from models import ProjectInfo
from project_config import load_config


def get_global_db_path() -> Path:
    """Get path to the global index database."""
    return Path.home() / ".omni-cortex" / "global.db"


def get_memory_count(db_path: Path) -> int:
    """Get the number of memories in a database."""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM memories")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def get_projects_from_global_db() -> list[str]:
    """Get unique project paths from the global index."""
    global_path = get_global_db_path()
    if not global_path.exists():
        return []

    try:
        conn = sqlite3.connect(str(global_path))
        cursor = conn.execute("SELECT DISTINCT source_project FROM global_memories")
        paths = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        return paths
    except Exception:
        return []


def scan_directory_for_cortex(base_dir: Path) -> list[Path]:
    """Scan a directory for .omni-cortex/cortex.db files."""
    found = []
    try:
        for item in base_dir.iterdir():
            if item.is_dir():
                cortex_dir = item / ".omni-cortex"
                cortex_db = cortex_dir / "cortex.db"
                if cortex_db.exists():
                    found.append(cortex_db)
    except PermissionError:
        pass
    return found


def scan_projects() -> list[ProjectInfo]:
    """
    Scan for all omni-cortex databases.

    Returns list of ProjectInfo with name, path, db_path, last_modified, memory_count.
    """
    projects: list[ProjectInfo] = []
    seen_paths: set[str] = set()

    # Load user config
    config = load_config()

    # 1. Add global index if exists
    global_path = get_global_db_path()
    if global_path.exists():
        stat = global_path.stat()
        global_project_path = str(global_path.parent)
        projects.append(
            ProjectInfo(
                name="Global Index",
                path=global_project_path,
                db_path=str(global_path),
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                memory_count=get_memory_count(global_path),
                is_global=True,
                is_favorite=global_project_path in config.favorites,
            )
        )
        seen_paths.add(str(global_path))

    # 2. Use CONFIGURABLE scan directories
    for scan_dir in config.scan_directories:
        scan_path = Path(scan_dir).expanduser()
        if scan_path.exists():
            for db_path in scan_directory_for_cortex(scan_path):
                if str(db_path) not in seen_paths:
                    project_dir = db_path.parent.parent
                    stat = db_path.stat()
                    project_path = str(project_dir)
                    projects.append(
                        ProjectInfo(
                            name=project_dir.name,
                            path=project_path,
                            db_path=str(db_path),
                            last_modified=datetime.fromtimestamp(stat.st_mtime),
                            memory_count=get_memory_count(db_path),
                            is_global=False,
                            is_favorite=project_path in config.favorites,
                        )
                    )
                    seen_paths.add(str(db_path))

    # 3. Add REGISTERED projects (manual additions)
    for reg in config.registered_projects:
        db_path = Path(reg.path) / ".omni-cortex" / "cortex.db"
        if db_path.exists() and str(db_path) not in seen_paths:
            stat = db_path.stat()
            projects.append(
                ProjectInfo(
                    name=Path(reg.path).name,
                    path=reg.path,
                    db_path=str(db_path),
                    last_modified=datetime.fromtimestamp(stat.st_mtime),
                    memory_count=get_memory_count(db_path),
                    is_global=False,
                    is_favorite=reg.path in config.favorites,
                    is_registered=True,
                    display_name=reg.display_name,
                )
            )
            seen_paths.add(str(db_path))

    # 4. Add paths from global db that we haven't seen
    for project_path in get_projects_from_global_db():
        db_path = Path(project_path) / ".omni-cortex" / "cortex.db"
        if db_path.exists() and str(db_path) not in seen_paths:
            stat = db_path.stat()
            projects.append(
                ProjectInfo(
                    name=Path(project_path).name,
                    path=project_path,
                    db_path=str(db_path),
                    last_modified=datetime.fromtimestamp(stat.st_mtime),
                    memory_count=get_memory_count(db_path),
                    is_global=False,
                    is_favorite=project_path in config.favorites,
                )
            )
            seen_paths.add(str(db_path))

    # Sort: favorites first, then by last_modified (most recent first), with global always first
    projects.sort(
        key=lambda p: (
            not p.is_global,
            not p.is_favorite,
            -(p.last_modified.timestamp() if p.last_modified else 0),
        )
    )

    return projects


if __name__ == "__main__":
    # Test the scanner
    for project in scan_projects():
        print(f"{project.name}: {project.db_path} ({project.memory_count} memories)")
