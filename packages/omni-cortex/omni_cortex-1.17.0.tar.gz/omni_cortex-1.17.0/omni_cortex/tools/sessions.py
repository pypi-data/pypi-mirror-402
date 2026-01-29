"""Session continuity tools for Omni Cortex MCP."""

import json
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from mcp.server.fastmcp import FastMCP

from ..database.connection import init_database
from ..config import get_project_path, get_session_id
from ..models.session import (
    Session,
    SessionCreate,
    SessionSummary,
    create_session,
    get_session,
    end_session,
    get_recent_sessions,
    get_session_summary,
)
from ..models.memory import list_memories
from ..utils.formatting import format_session_context_markdown
from ..utils.timestamps import format_relative_time


# === Input Models ===

class StartSessionInput(BaseModel):
    """Input for starting a session."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    session_id: Optional[str] = Field(None, description="Custom session ID (auto-generated if not provided)")
    project_path: Optional[str] = Field(None, description="Project path (uses current directory if not provided)")
    provide_context: bool = Field(True, description="Return context from previous sessions")
    context_depth: int = Field(3, description="Number of past sessions to summarize", ge=1, le=10)


class EndSessionInput(BaseModel):
    """Input for ending a session."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    session_id: str = Field(..., description="Session ID to end")
    summary: Optional[str] = Field(None, description="Manual summary (auto-generated if not provided)")
    key_learnings: Optional[list[str]] = Field(None, description="Key learnings from the session")


class SessionContextInput(BaseModel):
    """Input for getting session context."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    project_path: Optional[str] = Field(None, description="Filter by project path")
    session_count: int = Field(5, description="Number of past sessions to include", ge=1, le=20)
    include_learnings: bool = Field(True, description="Include key learnings")
    include_decisions: bool = Field(True, description="Include key decisions")
    include_errors: bool = Field(True, description="Include errors encountered")


def register_session_tools(mcp: FastMCP) -> None:
    """Register all session tools with the MCP server."""

    @mcp.tool(
        name="cortex_start_session",
        annotations={
            "title": "Start Session",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def cortex_start_session(params: StartSessionInput) -> str:
        """Start a new session and optionally get context from previous sessions.

        A session groups related activities and memories. Starting a new session
        establishes context and can provide a summary of what happened before.

        Args:
            params: StartSessionInput with optional session_id and context settings

        Returns:
            Session info and context from previous sessions
        """
        try:
            conn = init_database()
            project_path = params.project_path or str(get_project_path())

            # Create new session
            session_data = SessionCreate(
                session_id=params.session_id,
                project_path=project_path,
                provide_context=params.provide_context,
                context_depth=params.context_depth,
            )

            session = create_session(conn, session_data)

            lines = [
                f"# Session Started: {session.id}",
                f"Project: {session.project_path}",
                f"Started: {session.started_at}",
                "",
            ]

            # Get context from previous sessions if requested
            if params.provide_context:
                recent = get_recent_sessions(
                    conn,
                    project_path=project_path,
                    limit=params.context_depth + 1,  # +1 because current session is included
                )

                # Exclude current session
                past_sessions = [s for s in recent if s.id != session.id]

                if past_sessions:
                    lines.append("## Previous Sessions")
                    lines.append("")

                    learnings = []
                    decisions = []
                    errors = []

                    for prev in past_sessions[:params.context_depth]:
                        summary = get_session_summary(conn, prev.id)
                        if summary:
                            if summary.key_learnings:
                                learnings.extend(summary.key_learnings)
                            if summary.key_decisions:
                                decisions.extend(summary.key_decisions)
                            if summary.key_errors:
                                errors.extend(summary.key_errors)

                        ended = prev.ended_at
                        if ended:
                            lines.append(f"- Ended {format_relative_time(ended)}")
                            if prev.summary:
                                lines.append(f"  Summary: {prev.summary[:100]}...")

                    if learnings or decisions or errors:
                        lines.append("")
                        lines.append(format_session_context_markdown(
                            [s.model_dump() for s in past_sessions],
                            learnings[:5],
                            decisions[:5],
                            errors[:5],
                        ))

            return "\n".join(lines)

        except Exception as e:
            return f"Error starting session: {e}"

    @mcp.tool(
        name="cortex_end_session",
        annotations={
            "title": "End Session",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_end_session(params: EndSessionInput) -> str:
        """End a session and generate summary statistics.

        This closes the session and creates a summary of activities,
        memories created, tools used, and files modified.

        Args:
            params: EndSessionInput with session_id and optional summary

        Returns:
            Session summary
        """
        try:
            conn = init_database()

            session = end_session(
                conn,
                session_id=params.session_id,
                summary=params.summary,
                key_learnings=params.key_learnings,
            )

            if not session:
                return f"Session not found: {params.session_id}"

            # Get the summary
            summary = get_session_summary(conn, params.session_id)

            lines = [
                f"# Session Ended: {session.id}",
                f"Duration: {session.started_at} to {session.ended_at}",
                "",
            ]

            if summary:
                lines.append(f"## Statistics")
                lines.append(f"- Total activities: {summary.total_activities}")
                lines.append(f"- Memories created: {summary.total_memories_created}")

                if summary.tools_used:
                    lines.append(f"- Tools used: {len(summary.tools_used)}")
                    for tool, count in list(summary.tools_used.items())[:5]:
                        lines.append(f"  - {tool}: {count} calls")

                if summary.files_modified:
                    lines.append(f"- Files modified: {len(summary.files_modified)}")

                if summary.key_errors:
                    lines.append(f"- Errors encountered: {len(summary.key_errors)}")

            if session.summary:
                lines.append("")
                lines.append(f"## Summary")
                lines.append(session.summary)

            return "\n".join(lines)

        except Exception as e:
            return f"Error ending session: {e}"

    @mcp.tool(
        name="cortex_get_session_context",
        annotations={
            "title": "Get Session Context",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_get_session_context(params: SessionContextInput) -> str:
        """Get context from previous sessions for continuity.

        This provides a "Last time you were working on..." summary
        to help resume work on a project.

        Args:
            params: SessionContextInput with filters

        Returns:
            Context summary from previous sessions
        """
        try:
            conn = init_database()
            project_path = params.project_path or str(get_project_path())

            recent = get_recent_sessions(
                conn,
                project_path=project_path,
                limit=params.session_count,
            )

            if not recent:
                return "No previous sessions found for this project."

            learnings = []
            decisions = []
            errors = []

            for session in recent:
                summary = get_session_summary(conn, session.id)
                if summary:
                    if params.include_learnings and summary.key_learnings:
                        learnings.extend(summary.key_learnings)
                    if params.include_decisions and summary.key_decisions:
                        decisions.extend(summary.key_decisions)
                    if params.include_errors and summary.key_errors:
                        errors.extend(summary.key_errors)

            # Get recent important memories
            memories_result, _ = list_memories(
                conn,
                sort_by="importance_score",
                sort_order="desc",
                limit=5,
            )

            lines = []

            # Opening context
            if recent:
                last = recent[0]
                if last.ended_at:
                    lines.append(f"Last session ended {format_relative_time(last.ended_at)}.")
                    if last.summary:
                        lines.append(f"Summary: {last.summary}")
                    lines.append("")

            # Add formatted context
            lines.append(format_session_context_markdown(
                [s.model_dump() for s in recent],
                learnings[:5],
                decisions[:5],
                errors[:5],
            ))

            # Add important memories
            if memories_result:
                lines.append("## Important Memories")
                for mem in memories_result[:3]:
                    lines.append(f"- [{mem.type}] {mem.content[:100]}...")

            return "\n".join(lines)

        except Exception as e:
            return f"Error getting session context: {e}"
