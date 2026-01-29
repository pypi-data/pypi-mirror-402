"""Memory storage tools for Omni Cortex MCP."""

import json
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from mcp.server.fastmcp import FastMCP

from ..database.connection import get_connection, init_database
from ..config import get_project_path, get_session_id
from ..models.memory import (
    MemoryCreate,
    MemoryUpdate,
    Memory,
    create_memory,
    get_memory,
    update_memory,
    delete_memory,
    list_memories,
    touch_memory,
)
from ..models.relationship import create_relationship, get_relationships, VALID_RELATIONSHIP_TYPES
from ..search.hybrid import search
from ..search.ranking import calculate_relevance_score
from ..utils.formatting import format_memory_markdown, format_memories_list_markdown, detect_injection_patterns
from ..embeddings import generate_and_store_embedding, is_model_available
from ..config import load_config
from ..database.sync import sync_memory_to_global, delete_memory_from_global


# === Input Models ===

class RememberInput(BaseModel):
    """Input for storing a new memory."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    content: str = Field(..., description="The information to remember", min_length=1)
    context: Optional[str] = Field(None, description="Additional context about the memory")
    tags: Optional[list[str]] = Field(
        default_factory=list, description="Tags for categorization"
    )
    type: Optional[str] = Field(
        None, description="Memory type (auto-detected if not specified)"
    )
    importance: Optional[int] = Field(
        None, description="Importance score 1-100", ge=1, le=100
    )
    related_activity_id: Optional[str] = Field(
        None, description="ID of related activity"
    )
    related_memory_ids: Optional[list[str]] = Field(
        default_factory=list, description="IDs of related memories"
    )


class RecallInput(BaseModel):
    """Input for searching memories."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    query: str = Field(..., description="Search query", min_length=1)
    search_mode: str = Field(
        "keyword",
        description="Search mode: keyword, semantic, or hybrid",
    )
    type_filter: Optional[str] = Field(None, description="Filter by memory type")
    tags_filter: Optional[list[str]] = Field(None, description="Filter by tags")
    status_filter: Optional[str] = Field(None, description="Filter by status")
    min_importance: Optional[int] = Field(None, description="Minimum importance", ge=0, le=100)
    include_archived: bool = Field(False, description="Include archived memories")
    limit: int = Field(10, description="Maximum results", ge=1, le=50)


class ListMemoriesInput(BaseModel):
    """Input for listing memories."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    type_filter: Optional[str] = Field(None, description="Filter by memory type")
    tags_filter: Optional[list[str]] = Field(None, description="Filter by tags")
    status_filter: Optional[str] = Field(None, description="Filter by status")
    sort_by: str = Field(
        "last_accessed",
        description="Sort by: last_accessed, created_at, importance_score",
    )
    sort_order: str = Field("desc", description="Sort order: asc or desc")
    limit: int = Field(20, description="Maximum results", ge=1, le=100)
    offset: int = Field(0, description="Pagination offset", ge=0)


class UpdateMemoryInput(BaseModel):
    """Input for updating a memory."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    id: str = Field(..., description="Memory ID to update")
    content: Optional[str] = Field(None, description="New content")
    context: Optional[str] = Field(None, description="New context")
    tags: Optional[list[str]] = Field(None, description="Replace all tags")
    add_tags: Optional[list[str]] = Field(None, description="Tags to add")
    remove_tags: Optional[list[str]] = Field(None, description="Tags to remove")
    status: Optional[str] = Field(None, description="New status")
    importance: Optional[int] = Field(None, description="New importance", ge=1, le=100)


class ForgetInput(BaseModel):
    """Input for deleting a memory."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    id: str = Field(..., description="Memory ID to delete")
    confirm: bool = Field(..., description="Must be true to confirm deletion")


class LinkMemoriesInput(BaseModel):
    """Input for linking two memories."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    source_id: str = Field(..., description="Source memory ID")
    target_id: str = Field(..., description="Target memory ID")
    relationship_type: str = Field(
        ..., description="Type: related_to, supersedes, derived_from, contradicts"
    )
    strength: float = Field(1.0, description="Relationship strength 0-1", ge=0.0, le=1.0)


def register_memory_tools(mcp: FastMCP) -> None:
    """Register all memory tools with the MCP server."""

    @mcp.tool(
        name="cortex_remember",
        annotations={
            "title": "Remember Information",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def cortex_remember(params: RememberInput) -> str:
        """Store important information with auto-categorization and tagging.

        This tool saves knowledge, decisions, solutions, and other important
        information to the Cortex memory system. Content is automatically
        categorized and tagged based on analysis.

        Args:
            params: RememberInput with content, optional context, tags, type, importance

        Returns:
            Confirmation with memory ID and detected type/tags
        """
        try:
            conn = init_database()
            project_path = str(get_project_path())
            session_id = get_session_id()

            # Detect potential injection patterns in content
            injection_warnings = detect_injection_patterns(params.content)
            if injection_warnings:
                import logging
                logging.getLogger(__name__).warning(
                    f"Memory content contains potential injection patterns: {injection_warnings}"
                )

            # Create the memory
            memory_data = MemoryCreate(
                content=params.content,
                context=params.context,
                tags=params.tags or [],
                type=params.type or "general",
                importance=params.importance,
                related_activity_id=params.related_activity_id,
                related_memory_ids=params.related_memory_ids or [],
            )

            memory = create_memory(
                conn,
                memory_data,
                project_path=project_path,
                session_id=session_id,
            )

            # Create relationships if specified
            if params.related_memory_ids:
                for related_id in params.related_memory_ids:
                    create_relationship(
                        conn,
                        source_id=memory.id,
                        target_id=related_id,
                        relationship_type="related_to",
                    )

            # Generate embedding for semantic search (if enabled)
            has_embedding = False
            config = load_config()
            if config.embedding_enabled and is_model_available():
                try:
                    generate_and_store_embedding(
                        conn,
                        memory_id=memory.id,
                        content=memory.content,
                        context=memory.context,
                    )
                    has_embedding = True
                except Exception as e:
                    # Non-fatal: embedding generation is optional
                    # Log timeout errors to help with debugging
                    import logging
                    logging.getLogger(__name__).warning(f"Embedding generation failed: {e}")

            # Sync to global index for cross-project search
            sync_memory_to_global(
                memory_id=memory.id,
                content=memory.content,
                memory_type=memory.type,
                tags=memory.tags or [],
                context=memory.context,
                importance_score=memory.importance_score,
                status=memory.status,
                project_path=project_path,
                created_at=memory.created_at,
                updated_at=memory.updated_at,
            )

            embedding_status = "with embedding" if has_embedding else "no embedding"
            result = (
                f"Remembered: {memory.id}\n"
                f"Type: {memory.type}\n"
                f"Tags: {', '.join(memory.tags) if memory.tags else 'none'}\n"
                f"Importance: {memory.importance_score:.0f}/100\n"
                f"Search: {embedding_status}"
            )
            if injection_warnings:
                result += f"\n[Security Note: Content contains patterns that may be injection attempts: {', '.join(injection_warnings)}]"
            return result

        except Exception as e:
            return f"Error storing memory: {e}"

    @mcp.tool(
        name="cortex_recall",
        annotations={
            "title": "Search Memories",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_recall(params: RecallInput) -> str:
        """Search memories by keyword or semantic similarity.

        This tool searches through stored memories using keyword matching
        (FTS5) or semantic search (embeddings). Results are ranked by
        relevance, access frequency, recency, and importance.

        Args:
            params: RecallInput with query and filters

        Returns:
            Matching memories formatted as markdown
        """
        try:
            conn = init_database()

            # Use unified search function supporting all modes
            results = search(
                conn,
                query=params.query,
                mode=params.search_mode,
                type_filter=params.type_filter,
                tags_filter=params.tags_filter,
                status_filter=params.status_filter,
                min_importance=params.min_importance,
                include_archived=params.include_archived,
                limit=params.limit,
            )

            if not results:
                return f"No memories found matching: {params.query}"

            # Calculate full relevance scores and re-rank
            scored_results = []
            for memory, keyword_score, semantic_score in results:
                # Touch memory to update access count
                touch_memory(conn, memory.id)

                # Normalize scores to 0-1 range for ranking
                # Keyword scores from FTS can vary, normalize them
                kw_normalized = min(1.0, keyword_score / 10.0) if keyword_score > 0 else 0.0

                # Calculate combined score
                final_score = calculate_relevance_score(
                    memory,
                    keyword_score=kw_normalized,
                    semantic_score=semantic_score,
                    query=params.query,
                )
                scored_results.append((memory, final_score))

            # Sort by final score
            scored_results.sort(key=lambda x: x[1], reverse=True)

            # Build related memories map
            related_map: dict[str, list[dict]] = {}
            for memory, _ in scored_results:
                relationships = get_relationships(conn, memory.id)
                if relationships:
                    related_list = []
                    for rel in relationships[:3]:  # Limit to 3 related
                        # Get the related memory ID (could be source or target)
                        related_id = (
                            rel.target_memory_id
                            if rel.source_memory_id == memory.id
                            else rel.source_memory_id
                        )
                        related_mem = get_memory(conn, related_id)
                        if related_mem:
                            related_list.append({
                                "id": related_mem.id,
                                "content": related_mem.content,
                                "relationship_type": rel.relationship_type,
                            })
                    if related_list:
                        related_map[memory.id] = related_list

            # Format output - convert Memory objects to dicts for formatting
            memories = [m.model_dump() for m, _ in scored_results]
            return format_memories_list_markdown(memories, len(memories), related_map=related_map)

        except Exception as e:
            return f"Error searching memories: {e}"

    @mcp.tool(
        name="cortex_list_memories",
        annotations={
            "title": "List Memories",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_list_memories(params: ListMemoriesInput) -> str:
        """List memories with filtering and pagination.

        Args:
            params: ListMemoriesInput with filters and pagination

        Returns:
            Memories formatted as markdown
        """
        try:
            conn = init_database()

            memories, total = list_memories(
                conn,
                type_filter=params.type_filter,
                tags_filter=params.tags_filter,
                status_filter=params.status_filter,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
                limit=params.limit,
                offset=params.offset,
            )

            if not memories:
                return "No memories found."

            return format_memories_list_markdown(
                [m.model_dump() for m in memories],
                total,
            )

        except Exception as e:
            return f"Error listing memories: {e}"

    @mcp.tool(
        name="cortex_update_memory",
        annotations={
            "title": "Update Memory",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_update_memory(params: UpdateMemoryInput) -> str:
        """Update an existing memory.

        Args:
            params: UpdateMemoryInput with ID and fields to update

        Returns:
            Updated memory details or error
        """
        try:
            conn = init_database()

            update_data = MemoryUpdate(
                content=params.content,
                context=params.context,
                tags=params.tags,
                add_tags=params.add_tags,
                remove_tags=params.remove_tags,
                status=params.status,
                importance=params.importance,
            )

            updated = update_memory(conn, params.id, update_data)

            if not updated:
                return f"Memory not found: {params.id}"

            # Regenerate embedding if content or context changed (if enabled)
            config = load_config()
            if (params.content is not None or params.context is not None) and config.embedding_enabled and is_model_available():
                try:
                    generate_and_store_embedding(
                        conn,
                        memory_id=updated.id,
                        content=updated.content,
                        context=updated.context,
                    )
                except Exception:
                    pass  # Non-fatal

            # Sync update to global index
            sync_memory_to_global(
                memory_id=updated.id,
                content=updated.content,
                memory_type=updated.type,
                tags=updated.tags or [],
                context=updated.context,
                importance_score=updated.importance_score,
                status=updated.status,
                project_path=updated.project_path or str(get_project_path()),
                created_at=updated.created_at,
                updated_at=updated.updated_at,
            )

            return format_memory_markdown(updated.model_dump())

        except Exception as e:
            return f"Error updating memory: {e}"

    @mcp.tool(
        name="cortex_forget",
        annotations={
            "title": "Delete Memory",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_forget(params: ForgetInput) -> str:
        """Permanently delete a memory.

        Args:
            params: ForgetInput with ID and confirmation

        Returns:
            Confirmation or error
        """
        try:
            if not params.confirm:
                return "Deletion not confirmed. Set confirm=true to delete."

            conn = init_database()
            deleted = delete_memory(conn, params.id)

            if deleted:
                # Also remove from global index
                delete_memory_from_global(params.id)
                return f"Memory deleted: {params.id}"
            else:
                return f"Memory not found: {params.id}"

        except Exception as e:
            return f"Error deleting memory: {e}"

    @mcp.tool(
        name="cortex_link_memories",
        annotations={
            "title": "Link Memories",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_link_memories(params: LinkMemoriesInput) -> str:
        """Create a relationship between two memories.

        Relationship types:
        - related_to: General association
        - supersedes: New memory replaces old
        - derived_from: New memory based on old
        - contradicts: Memories conflict

        Args:
            params: LinkMemoriesInput with source, target, and type

        Returns:
            Confirmation or error
        """
        try:
            if params.relationship_type not in VALID_RELATIONSHIP_TYPES:
                return (
                    f"Invalid relationship type: {params.relationship_type}. "
                    f"Valid types: {', '.join(VALID_RELATIONSHIP_TYPES)}"
                )

            conn = init_database()
            relationship = create_relationship(
                conn,
                source_id=params.source_id,
                target_id=params.target_id,
                relationship_type=params.relationship_type,
                strength=params.strength,
            )

            if relationship:
                return (
                    f"Linked: {params.source_id} --[{params.relationship_type}]--> "
                    f"{params.target_id}"
                )
            else:
                return "Failed to create relationship. Check that both memories exist."

        except Exception as e:
            return f"Error linking memories: {e}"
