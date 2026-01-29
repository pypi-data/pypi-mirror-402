"""Populate session data for dashboard demo.

Links activities to sessions by timestamp and generates summaries.
Also creates memory relationships based on content similarity.
"""

import sqlite3
import json
from datetime import datetime, timedelta, timezone
from collections import defaultdict

DB_PATH = ".omni-cortex/cortex.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def link_activities_to_sessions():
    """Link activities to sessions based on timestamps."""
    conn = get_connection()

    # Get all sessions ordered by start time
    sessions = conn.execute("""
        SELECT id, started_at, ended_at FROM sessions
        ORDER BY started_at ASC
    """).fetchall()

    if not sessions:
        print("No sessions found")
        conn.close()
        return

    print(f"Found {len(sessions)} sessions")

    # Create time ranges for each session
    session_ranges = []
    for i, s in enumerate(sessions):
        start = datetime.fromisoformat(s["started_at"].replace("+00:00", ""))
        # End is either the ended_at time, or the start of the next session, or now
        if s["ended_at"]:
            end = datetime.fromisoformat(s["ended_at"].replace("+00:00", ""))
        elif i + 1 < len(sessions):
            end = datetime.fromisoformat(sessions[i+1]["started_at"].replace("+00:00", ""))
        else:
            end = datetime.now(timezone.utc).replace(tzinfo=None)
        session_ranges.append((s["id"], start, end))

    # Get all activities without session_id
    activities = conn.execute("""
        SELECT id, timestamp FROM activities
        WHERE session_id IS NULL
    """).fetchall()

    print(f"Found {len(activities)} unlinked activities")

    # Link activities to sessions
    updates = defaultdict(list)
    for a in activities:
        ts = datetime.fromisoformat(a["timestamp"].replace("+00:00", ""))
        for session_id, start, end in session_ranges:
            if start <= ts <= end:
                updates[session_id].append(a["id"])
                break

    # Batch update
    for session_id, activity_ids in updates.items():
        placeholders = ",".join("?" * len(activity_ids))
        conn.execute(
            f"UPDATE activities SET session_id = ? WHERE id IN ({placeholders})",
            [session_id] + activity_ids
        )
        print(f"Linked {len(activity_ids)} activities to session {session_id[:20]}...")

    conn.commit()
    conn.close()
    print("Done linking activities to sessions")


def generate_session_summaries():
    """Generate summaries for sessions based on their activities."""
    conn = get_connection()

    # Get sessions with activity stats
    sessions = conn.execute("""
        SELECT s.id, s.started_at, s.ended_at,
               COUNT(a.id) as activity_count,
               GROUP_CONCAT(DISTINCT a.tool_name) as tools_used
        FROM sessions s
        LEFT JOIN activities a ON a.session_id = s.id
        GROUP BY s.id
        ORDER BY s.started_at DESC
    """).fetchall()

    for s in sessions:
        session_id = s["id"]
        activity_count = s["activity_count"]
        tools = s["tools_used"] or ""

        # Generate a summary based on tools used
        tool_list = [t for t in tools.split(",") if t][:5]  # Top 5 tools

        if activity_count == 0:
            summary = "Session with no recorded activity"
        elif "Edit" in tools or "Write" in tools:
            summary = f"Code editing session - {activity_count} operations using {', '.join(tool_list[:3])}"
        elif "Glob" in tools or "Grep" in tools:
            summary = f"Code exploration session - {activity_count} operations searching codebase"
        elif "Bash" in tools:
            summary = f"Command execution session - {activity_count} shell commands"
        else:
            summary = f"Development session - {activity_count} operations"

        # Update session summary
        conn.execute(
            "UPDATE sessions SET summary = ? WHERE id = ?",
            (summary, session_id)
        )
        print(f"Updated session {session_id[:20]}... with summary: {summary[:50]}...")

    # End old sessions that are still "ongoing"
    cutoff = (datetime.now() - timedelta(hours=1)).isoformat()
    conn.execute("""
        UPDATE sessions
        SET ended_at = datetime(started_at, '+1 hour')
        WHERE ended_at IS NULL AND started_at < ?
    """, (cutoff,))

    conn.commit()
    conn.close()
    print("Done generating session summaries")


def create_memory_relationships():
    """Create relationships between memories based on content similarity and tags."""
    conn = get_connection()

    # Get all memories with their tags
    memories = conn.execute("""
        SELECT id, content, type, tags FROM memories
    """).fetchall()

    print(f"Found {len(memories)} memories")

    # Group memories by type for "related_to" relationships
    by_type = defaultdict(list)
    for m in memories:
        by_type[m["type"]].append(m)

    relationships = []
    existing = set()

    # Check existing relationships
    existing_rels = conn.execute("""
        SELECT source_memory_id, target_memory_id FROM memory_relationships
    """).fetchall()
    for r in existing_rels:
        existing.add((r["source_memory_id"], r["target_memory_id"]))
        existing.add((r["target_memory_id"], r["source_memory_id"]))

    # Create relationships between memories of the same type
    for mem_type, mems in by_type.items():
        if len(mems) < 2:
            continue

        # Connect memories of the same type
        for i, m1 in enumerate(mems):
            for m2 in mems[i+1:i+3]:  # Connect to next 2 memories of same type
                if (m1["id"], m2["id"]) not in existing:
                    relationships.append({
                        "source": m1["id"],
                        "target": m2["id"],
                        "type": "related_to",
                        "strength": 0.7
                    })
                    existing.add((m1["id"], m2["id"]))

    # Create relationships based on shared tags
    tag_to_memories = defaultdict(list)
    for m in memories:
        if m["tags"]:
            try:
                tags = json.loads(m["tags"])
                for tag in tags:
                    tag_to_memories[tag].append(m["id"])
            except json.JSONDecodeError:
                pass

    for tag, mem_ids in tag_to_memories.items():
        if len(mem_ids) >= 2:
            for i, mid1 in enumerate(mem_ids[:5]):  # Limit to prevent too many
                for mid2 in mem_ids[i+1:i+2]:
                    if (mid1, mid2) not in existing:
                        relationships.append({
                            "source": mid1,
                            "target": mid2,
                            "type": "related_to",
                            "strength": 0.8
                        })
                        existing.add((mid1, mid2))

    # Create some derived_from relationships for solution->decision pairs
    solutions = [m for m in memories if m["type"] == "solution"]
    decisions = [m for m in memories if m["type"] == "decision"]

    for sol in solutions[:5]:
        for dec in decisions[:3]:
            if (sol["id"], dec["id"]) not in existing:
                relationships.append({
                    "source": sol["id"],
                    "target": dec["id"],
                    "type": "derived_from",
                    "strength": 0.6
                })
                existing.add((sol["id"], dec["id"]))
                break

    # Insert new relationships
    import time
    for i, rel in enumerate(relationships):
        # Use unique ID with counter to avoid collisions
        rel_id = f"rel_{int(time.time()*1000)}_{i:04d}"
        try:
            conn.execute("""
                INSERT INTO memory_relationships (id, source_memory_id, target_memory_id, relationship_type, strength, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (rel_id, rel["source"], rel["target"], rel["type"], rel["strength"]))
        except sqlite3.IntegrityError:
            # Skip duplicates
            pass
        time.sleep(0.001)  # Ensure unique timestamps

    conn.commit()
    conn.close()
    print(f"Created {len(relationships)} new relationships")


if __name__ == "__main__":
    print("=== Populating Session Data ===\n")

    print("Step 1: Linking activities to sessions...")
    link_activities_to_sessions()
    print()

    print("Step 2: Generating session summaries...")
    generate_session_summaries()
    print()

    print("Step 3: Creating memory relationships...")
    create_memory_relationships()
    print()

    print("=== Done ===")
