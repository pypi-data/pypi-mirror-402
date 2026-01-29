"""Utility tools for Omni Cortex MCP."""

import json
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from mcp.server.fastmcp import FastMCP

from ..database.connection import init_database
from ..database.sync import search_global_memories, get_global_stats, sync_all_project_memories
from ..models.memory import list_memories, update_memory, MemoryUpdate
from ..utils.timestamps import now_iso


# === Input Models ===

class ListTagsInput(BaseModel):
    """Input for listing tags."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    min_count: int = Field(1, description="Minimum usage count", ge=1)
    limit: int = Field(50, description="Maximum tags to return", ge=1, le=200)


class ReviewMemoriesInput(BaseModel):
    """Input for reviewing memories."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    action: str = Field(
        ..., description="Action: list, mark_fresh, mark_outdated, mark_archived"
    )
    days_threshold: int = Field(30, description="Review memories older than this", ge=1)
    memory_ids: Optional[list[str]] = Field(None, description="Memory IDs to update (for mark actions)")
    limit: int = Field(20, description="Maximum memories to list", ge=1, le=100)


class ExportInput(BaseModel):
    """Input for exporting data."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    format: str = Field("markdown", description="Export format: markdown, json, sqlite")
    include_activities: bool = Field(True, description="Include activities")
    include_memories: bool = Field(True, description="Include memories")
    since: Optional[str] = Field(None, description="Export data since this date (ISO 8601)")
    output_path: Optional[str] = Field(None, description="File path to save export")


class GlobalSearchInput(BaseModel):
    """Input for global cross-project search."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    query: str = Field(..., description="Search query", min_length=1)
    type_filter: Optional[str] = Field(None, description="Filter by memory type")
    tags_filter: Optional[list[str]] = Field(None, description="Filter by tags")
    project_filter: Optional[str] = Field(None, description="Filter by project path (substring match)")
    limit: int = Field(20, description="Maximum results", ge=1, le=100)


class GlobalSyncInput(BaseModel):
    """Input for syncing to global index."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    full_sync: bool = Field(False, description="Sync all project memories to global index")


VALID_ACTIONS = ["list", "mark_fresh", "mark_outdated", "mark_archived"]


def register_utility_tools(mcp: FastMCP) -> None:
    """Register all utility tools with the MCP server."""

    @mcp.tool(
        name="cortex_list_tags",
        annotations={
            "title": "List Tags",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_list_tags(params: ListTagsInput) -> str:
        """List all tags used in memories with usage counts.

        Args:
            params: ListTagsInput with filters

        Returns:
            List of tags and their usage counts
        """
        try:
            conn = init_database()
            cursor = conn.cursor()

            # Query to extract and count tags
            cursor.execute("""
                SELECT tags FROM memories
                WHERE tags IS NOT NULL AND tags != '[]'
            """)

            tag_counts: dict[str, int] = {}
            for row in cursor.fetchall():
                tags = row["tags"]
                if tags:
                    if isinstance(tags, str):
                        tags = json.loads(tags)
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Filter by min_count and sort
            filtered = [
                (tag, count)
                for tag, count in tag_counts.items()
                if count >= params.min_count
            ]
            filtered.sort(key=lambda x: x[1], reverse=True)
            filtered = filtered[:params.limit]

            if not filtered:
                return "No tags found."

            lines = ["# Tags", ""]
            for tag, count in filtered:
                lines.append(f"- **{tag}**: {count} memories")

            return "\n".join(lines)

        except Exception as e:
            return f"Error listing tags: {e}"

    @mcp.tool(
        name="cortex_review_memories",
        annotations={
            "title": "Review Memories",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_review_memories(params: ReviewMemoriesInput) -> str:
        """Review and update memory freshness status.

        Actions:
        - list: Show memories that need review
        - mark_fresh: Mark memories as verified/fresh
        - mark_outdated: Mark memories as outdated
        - mark_archived: Archive memories

        Args:
            params: ReviewMemoriesInput with action and options

        Returns:
            Results of the review action
        """
        try:
            if params.action not in VALID_ACTIONS:
                return f"Invalid action: {params.action}. Valid: {', '.join(VALID_ACTIONS)}"

            conn = init_database()

            if params.action == "list":
                # Find memories that need review
                memories, total = list_memories(
                    conn,
                    status_filter="needs_review",
                    limit=params.limit,
                )

                if not memories:
                    # Also check for memories not accessed recently
                    memories, total = list_memories(
                        conn,
                        sort_by="last_accessed",
                        sort_order="asc",
                        limit=params.limit,
                    )

                if not memories:
                    return "No memories need review."

                lines = [f"# Memories for Review ({len(memories)})", ""]
                for mem in memories:
                    lines.append(f"## {mem.id}")
                    lines.append(f"Type: {mem.type} | Status: {mem.status}")
                    lines.append(f"Last accessed: {mem.last_accessed}")
                    lines.append(f"Content: {mem.content[:100]}...")
                    lines.append("")

                return "\n".join(lines)

            else:
                # Update memories
                if not params.memory_ids:
                    return "No memory IDs provided for update."

                status_map = {
                    "mark_fresh": "fresh",
                    "mark_outdated": "outdated",
                    "mark_archived": "archived",
                }
                new_status = status_map[params.action]

                updated = 0
                for memory_id in params.memory_ids:
                    result = update_memory(
                        conn,
                        memory_id,
                        MemoryUpdate(
                            status=new_status,
                        ),
                    )
                    if result:
                        updated += 1

                return f"Updated {updated} memories to status: {new_status}"

        except Exception as e:
            return f"Error reviewing memories: {e}"

    @mcp.tool(
        name="cortex_export",
        annotations={
            "title": "Export Data",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_export(params: ExportInput) -> str:
        """Export memories and activities to various formats.

        Args:
            params: ExportInput with format and filters

        Returns:
            Exported data or confirmation of file save
        """
        try:
            conn = init_database()

            # SQLite dump format
            if params.format == "sqlite":
                if not params.output_path:
                    return "SQLite export requires output_path parameter."

                from ..config import get_project_db_path
                import shutil

                source_path = get_project_db_path()
                if not source_path.exists():
                    return f"Database not found: {source_path}"

                # Ensure all data is flushed to disk (checkpoint WAL)
                try:
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                except Exception:
                    pass  # May fail if not in WAL mode

                # Copy the database file
                shutil.copy2(source_path, params.output_path)

                # Also copy WAL and SHM files if they exist
                for suffix in ["-wal", "-shm"]:
                    wal_path = source_path.parent / (source_path.name + suffix)
                    if wal_path.exists():
                        shutil.copy2(wal_path, params.output_path + suffix)

                return f"SQLite database exported to: {params.output_path}"

            data = {
                "exported_at": now_iso(),
                "format": params.format,
            }

            if params.include_memories:
                memories, _ = list_memories(conn, limit=1000)
                data["memories"] = [m.model_dump() for m in memories]

            if params.include_activities:
                from ..models.activity import get_activities
                activities, _ = get_activities(conn, since=params.since, limit=1000)
                data["activities"] = [a.model_dump() for a in activities]

            if params.format == "json":
                output = json.dumps(data, indent=2, default=str)
            else:
                # Markdown format
                lines = [
                    "# Omni Cortex Export",
                    f"Exported: {data['exported_at']}",
                    "",
                ]

                if params.include_memories and data.get("memories"):
                    lines.append("## Memories")
                    lines.append("")
                    for mem in data["memories"]:
                        lines.append(f"### [{mem['type']}] {mem['id']}")
                        lines.append(f"**Content:** {mem['content']}")
                        if mem.get("context"):
                            lines.append(f"**Context:** {mem['context']}")
                        if mem.get("tags"):
                            lines.append(f"**Tags:** {', '.join(mem['tags'])}")
                        lines.append(f"**Created:** {mem['created_at']}")
                        lines.append("")

                if params.include_activities and data.get("activities"):
                    lines.append("## Activities")
                    lines.append("")
                    for act in data["activities"][:50]:  # Limit for readability
                        lines.append(f"- **{act['event_type']}** ({act['timestamp']})")
                        if act.get("tool_name"):
                            lines.append(f"  Tool: {act['tool_name']}")
                        lines.append("")

                output = "\n".join(lines)

            if params.output_path:
                with open(params.output_path, "w", encoding="utf-8") as f:
                    f.write(output)
                return f"Exported to: {params.output_path}"

            # Truncate if too long
            if len(output) > 10000:
                output = output[:10000] + "\n\n... [truncated]"

            return output

        except Exception as e:
            return f"Error exporting data: {e}"

    @mcp.tool(
        name="cortex_global_search",
        annotations={
            "title": "Search Global Index",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_global_search(params: GlobalSearchInput) -> str:
        """Search memories across all projects via global index.

        This tool searches the global index at ~/.omni-cortex/global.db
        which contains memories from all projects that have global_sync_enabled.

        Args:
            params: GlobalSearchInput with query and filters

        Returns:
            Matching memories from all projects
        """
        try:
            results = search_global_memories(
                query=params.query,
                type_filter=params.type_filter,
                tags_filter=params.tags_filter,
                project_filter=params.project_filter,
                limit=params.limit,
            )

            if not results:
                return f"No memories found in global index for: {params.query}"

            lines = [f"# Global Search Results ({len(results)})", ""]

            # Group by project
            by_project: dict[str, list] = {}
            for mem in results:
                project = mem.get("project_path", "unknown")
                if project not in by_project:
                    by_project[project] = []
                by_project[project].append(mem)

            for project, memories in by_project.items():
                lines.append(f"## Project: {project}")
                lines.append("")

                for mem in memories:
                    lines.append(f"### [{mem['type']}] {mem['id']}")
                    lines.append(f"{mem['content'][:200]}...")
                    if mem.get("tags"):
                        lines.append(f"**Tags:** {', '.join(mem['tags'])}")
                    lines.append(f"**Score:** {mem.get('score', 0):.2f}")
                    lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return f"Error searching global index: {e}"

    @mcp.tool(
        name="cortex_global_stats",
        annotations={
            "title": "Global Index Stats",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_global_stats() -> str:
        """Get statistics from the global memory index.

        Shows total memories, breakdown by project and type.

        Returns:
            Statistics about the global index
        """
        try:
            stats = get_global_stats()

            if "error" in stats:
                return f"Error: {stats['error']}"

            lines = [
                "# Global Index Statistics",
                "",
                f"**Total Memories:** {stats.get('total_memories', 0)}",
                "",
            ]

            if stats.get("by_project"):
                lines.append("## By Project")
                for project, count in stats["by_project"].items():
                    lines.append(f"- {project}: {count}")
                lines.append("")

            if stats.get("by_type"):
                lines.append("## By Type")
                for mem_type, count in stats["by_type"].items():
                    lines.append(f"- {mem_type}: {count}")

            return "\n".join(lines)

        except Exception as e:
            return f"Error getting global stats: {e}"

    @mcp.tool(
        name="cortex_sync_to_global",
        annotations={
            "title": "Sync to Global Index",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_sync_to_global(params: GlobalSyncInput) -> str:
        """Sync project memories to the global index.

        This manually triggers a sync of all project memories to the
        global index. Normally this happens automatically on create/update.

        Args:
            params: GlobalSyncInput with sync options

        Returns:
            Number of memories synced
        """
        try:
            if params.full_sync:
                count = sync_all_project_memories()
                return f"Synced {count} memories to global index."
            else:
                return "Set full_sync=true to sync all project memories to global index."

        except Exception as e:
            return f"Error syncing to global: {e}"
