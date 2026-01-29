#!/usr/bin/env python3
r"""
Import memories from Ken You Remember (memories.json) into Omni Cortex.

This script:
1. Finds all memories.json files in a given root directory
2. Creates/initializes a .omni-cortex database in each project folder
3. Imports memories with proper tagging and categorization
4. Syncs all imported memories to the global index

Usage:
    python import_ken_memories.py D:\           # Import from all of D:\
    python import_ken_memories.py D:\Projects   # Import from specific folder
    python import_ken_memories.py --dry-run D:\ # Preview without importing
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from omni_cortex.database.connection import init_database
from omni_cortex.database.sync import sync_memory_to_global
from omni_cortex.models.memory import create_memory, MemoryCreate
from omni_cortex.categorization.auto_type import detect_memory_type
from omni_cortex.categorization.auto_tags import suggest_tags
from omni_cortex.utils.ids import generate_id


def find_memories_files(root: Path) -> list[Path]:
    """Find all memories.json files under the root directory."""
    memories_files = []
    for mem_file in root.rglob("memories.json"):
        # Skip recycle bin and node_modules
        path_str = str(mem_file).lower()
        if "$recycle" in path_str or "node_modules" in path_str:
            continue
        memories_files.append(mem_file)
    return sorted(memories_files)


def load_ken_memories(file_path: Path) -> list[dict]:
    """Load memories from a Ken You Remember memories.json file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Ken You Remember uses a simple list format
        if isinstance(data, list):
            return data
        # Or might be wrapped in a 'memories' key
        elif isinstance(data, dict) and "memories" in data:
            return data["memories"]
        else:
            return []
    except (json.JSONDecodeError, IOError) as e:
        print(f"  Warning: Could not read {file_path}: {e}")
        return []


def convert_ken_memory(ken_mem: dict, project_path: Path) -> dict | None:
    """Convert a Ken You Remember memory to Omni Cortex format."""
    # Ken You Remember format:
    # {
    #   "id": "mem_xxx",
    #   "content": "...",
    #   "context": "...",
    #   "tags": [...],
    #   "createdAt": "ISO timestamp",
    #   "lastAccessedAt": "ISO timestamp"
    # }

    content = ken_mem.get("content", "")
    if not content or not content.strip():
        return None

    context = ken_mem.get("context", "")
    tags = ken_mem.get("tags", [])
    created_at = ken_mem.get("createdAt", datetime.utcnow().isoformat() + "Z")

    # Ensure tags is a list
    if isinstance(tags, str):
        tags = [tags]
    elif not isinstance(tags, list):
        tags = []

    # Add import tag to track source
    if "imported-from-ken" not in tags:
        tags.append("imported-from-ken")

    # Auto-detect type if not present
    memory_type = detect_memory_type(content)

    # Auto-suggest additional tags
    suggested = suggest_tags(content)
    for tag in suggested:
        if tag not in tags:
            tags.append(tag)

    return {
        "content": content,
        "context": context or f"Imported from Ken You Remember ({project_path.name})",
        "tags": tags,
        "type": memory_type,
        "created_at": created_at,
        "importance": ken_mem.get("importance", 50),
    }


def import_to_project(memories_file: Path, dry_run: bool = False) -> tuple[int, int]:
    """
    Import memories from a memories.json file to its project's Omni Cortex database.

    Returns (imported_count, skipped_count)
    """
    project_path = memories_file.parent
    cortex_dir = project_path / ".omni-cortex"
    db_path = cortex_dir / "cortex.db"

    # Load Ken memories
    ken_memories = load_ken_memories(memories_file)
    if not ken_memories:
        return 0, 0

    print(f"\n[DIR] {project_path}")
    print(f"   Found {len(ken_memories)} memories in memories.json")

    if dry_run:
        valid_count = sum(1 for m in ken_memories if m.get("content", "").strip())
        print(f"   Would import: {valid_count} memories")
        return valid_count, len(ken_memories) - valid_count

    # Initialize database
    cortex_dir.mkdir(exist_ok=True)
    conn = init_database(db_path=db_path)

    # Check for existing memories to avoid duplicates
    cursor = conn.execute("SELECT content FROM memories")
    existing_contents = {row[0] for row in cursor.fetchall()}

    imported = 0
    skipped = 0

    for ken_mem in ken_memories:
        cortex_mem = convert_ken_memory(ken_mem, project_path)
        if not cortex_mem:
            skipped += 1
            continue

        # Skip duplicates
        if cortex_mem["content"] in existing_contents:
            skipped += 1
            continue

        # Create memory in local database
        try:
            memory_data = MemoryCreate(
                content=cortex_mem["content"],
                context=cortex_mem["context"],
                tags=cortex_mem["tags"],
                type=cortex_mem["type"],
                importance=cortex_mem["importance"],
            )
            memory = create_memory(
                conn=conn,
                data=memory_data,
                project_path=str(project_path),
            )

            # Sync to global index
            try:
                from omni_cortex.utils.timestamps import now_iso
                sync_memory_to_global(
                    memory_id=memory.id,
                    content=memory.content,
                    memory_type=memory.type,
                    tags=memory.tags,
                    context=memory.context,
                    importance_score=memory.importance_score,
                    status=memory.status,
                    project_path=str(project_path),
                    created_at=memory.created_at,
                    updated_at=memory.updated_at,
                )
            except Exception as e:
                # Global sync failure shouldn't stop import
                pass

            imported += 1
            existing_contents.add(cortex_mem["content"])
        except Exception as e:
            print(f"   Error importing memory: {e}")
            skipped += 1

    print(f"   [OK] Imported: {imported}, Skipped: {skipped}")
    return imported, skipped


def main():
    parser = argparse.ArgumentParser(
        description="Import Ken You Remember memories into Omni Cortex"
    )
    parser.add_argument(
        "root",
        type=Path,
        help="Root directory to search for memories.json files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be imported without making changes"
    )
    args = parser.parse_args()

    if not args.root.exists():
        print(f"Error: {args.root} does not exist")
        sys.exit(1)

    print("=" * 60)
    print("Ken You Remember -> Omni Cortex Memory Import")
    print("=" * 60)

    if args.dry_run:
        print("[DRY-RUN] DRY RUN MODE - No changes will be made\n")

    # Ensure global database exists
    if not args.dry_run:
        init_database(is_global=True)

    # Find all memories.json files
    memories_files = find_memories_files(args.root)
    print(f"Found {len(memories_files)} memories.json files to process")

    total_imported = 0
    total_skipped = 0

    for mem_file in memories_files:
        imported, skipped = import_to_project(mem_file, args.dry_run)
        total_imported += imported
        total_skipped += skipped

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total memories imported: {total_imported}")
    print(f"Total memories skipped:  {total_skipped}")

    if args.dry_run:
        print("\n[TIP] Run without --dry-run to perform the actual import")
    else:
        print("\n[OK] Import complete! Memories are now in Omni Cortex.")
        print("   - Each project has its own .omni-cortex/cortex.db")
        print("   - All memories synced to global ~/.omni-cortex/global.db")


if __name__ == "__main__":
    main()
