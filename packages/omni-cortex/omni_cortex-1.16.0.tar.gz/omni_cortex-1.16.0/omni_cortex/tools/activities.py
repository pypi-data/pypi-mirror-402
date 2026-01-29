"""Activity logging tools for Omni Cortex MCP."""

import json
from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from mcp.server.fastmcp import FastMCP

from ..database.connection import init_database
from ..config import get_project_path, get_session_id
from ..models.activity import Activity, ActivityCreate, create_activity, get_activities
from ..models.memory import list_memories
from ..utils.formatting import format_activity_markdown, format_timeline_markdown
from ..utils.timestamps import now_iso, parse_iso
from pathlib import Path


# === Input Models ===

class LogActivityInput(BaseModel):
    """Input for logging an activity."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    event_type: str = Field(
        ..., description="Event type: pre_tool_use, post_tool_use, decision, observation"
    )
    tool_name: Optional[str] = Field(None, description="Tool name if applicable")
    tool_input: Optional[str] = Field(None, description="Tool input (JSON string)")
    tool_output: Optional[str] = Field(None, description="Tool output (JSON string)")
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds", ge=0)
    success: bool = Field(True, description="Whether the operation succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    file_path: Optional[str] = Field(None, description="Relevant file path")
    agent_id: Optional[str] = Field(None, description="Agent ID")
    # Command analytics fields
    command_name: Optional[str] = Field(None, description="Slash command name")
    command_scope: Optional[str] = Field(None, description="'universal' or 'project'")
    mcp_server: Optional[str] = Field(None, description="MCP server name")
    skill_name: Optional[str] = Field(None, description="Skill name")


class GetActivitiesInput(BaseModel):
    """Input for getting activities."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    session_id: Optional[str] = Field(None, description="Filter by session ID")
    agent_id: Optional[str] = Field(None, description="Filter by agent ID")
    event_type: Optional[str] = Field(None, description="Filter by event type")
    tool_name: Optional[str] = Field(None, description="Filter by tool name")
    since: Optional[str] = Field(None, description="Start time (ISO 8601)")
    until: Optional[str] = Field(None, description="End time (ISO 8601)")
    limit: int = Field(50, description="Maximum results", ge=1, le=200)
    offset: int = Field(0, description="Pagination offset", ge=0)


class TimelineInput(BaseModel):
    """Input for getting timeline."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    hours: int = Field(24, description="Hours to look back", ge=1, le=168)
    include_activities: bool = Field(True, description="Include activities")
    include_memories: bool = Field(True, description="Include memories")
    group_by: str = Field("hour", description="Group by: hour, day, or session")


def register_activity_tools(mcp: FastMCP) -> None:
    """Register all activity tools with the MCP server."""

    @mcp.tool(
        name="cortex_log_activity",
        annotations={
            "title": "Log Activity",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def cortex_log_activity(params: LogActivityInput) -> str:
        """Log a tool call, decision, or observation.

        This tool records activities in the audit trail. Most activity logging
        is done automatically by hooks, but this tool allows manual logging.

        Args:
            params: LogActivityInput with event details

        Returns:
            Confirmation with activity ID
        """
        try:
            conn = init_database()
            project_path = str(get_project_path())
            session_id = get_session_id()

            # Auto-detect command analytics if not provided
            command_name = params.command_name
            command_scope = params.command_scope
            mcp_server = params.mcp_server
            skill_name = params.skill_name

            # Extract skill info from Skill tool calls
            if params.tool_name == "Skill" and params.tool_input:
                extracted_skill, extracted_scope = _extract_skill_info(
                    params.tool_input, project_path
                )
                if extracted_skill:
                    skill_name = skill_name or extracted_skill
                    command_scope = command_scope or extracted_scope

            # Extract MCP server from tool name (mcp__servername__toolname pattern)
            if params.tool_name and params.tool_name.startswith("mcp__"):
                extracted_mcp = _extract_mcp_server(params.tool_name)
                mcp_server = mcp_server or extracted_mcp

            activity_data = ActivityCreate(
                event_type=params.event_type,
                tool_name=params.tool_name,
                tool_input=params.tool_input,
                tool_output=params.tool_output,
                duration_ms=params.duration_ms,
                success=params.success,
                error_message=params.error_message,
                file_path=params.file_path,
                agent_id=params.agent_id,
                command_name=command_name,
                command_scope=command_scope,
                mcp_server=mcp_server,
                skill_name=skill_name,
            )

            activity = create_activity(
                conn,
                activity_data,
                session_id=session_id,
                project_path=project_path,
            )

            return (
                f"Logged: {activity.id}\n"
                f"Type: {activity.event_type}\n"
                f"Tool: {activity.tool_name or 'N/A'}\n"
                f"Success: {'Yes' if activity.success else 'No'}"
            )

        except Exception as e:
            return f"Error logging activity: {e}"

    @mcp.tool(
        name="cortex_get_activities",
        annotations={
            "title": "Get Activities",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_get_activities(params: GetActivitiesInput) -> str:
        """Query the activity log with filters.

        Args:
            params: GetActivitiesInput with filters and pagination

        Returns:
            Activities formatted as markdown
        """
        try:
            conn = init_database()

            activities, total = get_activities(
                conn,
                session_id=params.session_id,
                agent_id=params.agent_id,
                event_type=params.event_type,
                tool_name=params.tool_name,
                since=params.since,
                until=params.until,
                limit=params.limit,
                offset=params.offset,
            )

            if not activities:
                return "No activities found."

            lines = [f"# Activities ({len(activities)} of {total})", ""]

            for activity in activities:
                lines.append(format_activity_markdown(activity.model_dump()))
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return f"Error getting activities: {e}"

    @mcp.tool(
        name="cortex_get_timeline",
        annotations={
            "title": "Get Timeline",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_get_timeline(params: TimelineInput) -> str:
        """Get a timeline of activities and memories.

        This provides a chronological view of what happened in the project
        over the specified time period.

        Args:
            params: TimelineInput with time range and inclusion options

        Returns:
            Timeline formatted as markdown
        """
        try:
            conn = init_database()

            # Calculate time range
            now = datetime.now(timezone.utc)
            since = (now - timedelta(hours=params.hours)).isoformat()

            activities_list = []
            memories_list = []

            if params.include_activities:
                activities_result, _ = get_activities(
                    conn,
                    since=since,
                    limit=100,
                )
                activities_list = [a.model_dump() for a in activities_result]

            if params.include_memories:
                memories_result, _ = list_memories(
                    conn,
                    sort_by="created_at",
                    sort_order="desc",
                    limit=50,
                )
                # Filter to time range
                memories_list = [
                    m.model_dump()
                    for m in memories_result
                    if parse_iso(m.created_at) >= parse_iso(since)
                ]

            return format_timeline_markdown(
                activities_list,
                memories_list,
                group_by=params.group_by,
            )

        except Exception as e:
            return f"Error getting timeline: {e}"


# === Helper Functions for Command Analytics ===


def _extract_skill_info(tool_input: str, project_path: str) -> tuple[Optional[str], Optional[str]]:
    """Extract skill name and scope from Skill tool input.

    Args:
        tool_input: JSON string of tool input
        project_path: Current project path for scope detection

    Returns:
        Tuple of (skill_name, scope) where scope is 'universal' or 'project'
    """
    try:
        input_data = json.loads(tool_input)
        skill_name = input_data.get("skill", "")
        if not skill_name:
            return None, None

        # Determine scope by checking file locations
        from pathlib import Path

        # Check project-specific commands first
        project_cmd = Path(project_path) / ".claude" / "commands" / f"{skill_name}.md"
        if project_cmd.exists():
            return skill_name, "project"

        # Check universal commands
        universal_cmd = Path.home() / ".claude" / "commands" / f"{skill_name}.md"
        if universal_cmd.exists():
            return skill_name, "universal"

        # Default to unknown scope if skill exists but location is unclear
        return skill_name, "unknown"

    except (json.JSONDecodeError, TypeError, KeyError):
        return None, None


def _extract_mcp_server(tool_name: str) -> Optional[str]:
    """Extract MCP server name from tool name.

    Tool names follow the pattern: mcp__servername__toolname

    Args:
        tool_name: Full tool name

    Returns:
        MCP server name or None
    """
    if not tool_name or not tool_name.startswith("mcp__"):
        return None

    parts = tool_name.split("__")
    if len(parts) >= 3:
        return parts[1]  # Server name is the second part

    return None


# === Natural Language Summary Generation ===


def generate_activity_summary(
    tool_name: Optional[str],
    tool_input: Optional[str],
    success: bool,
    file_path: Optional[str],
    event_type: str,
) -> tuple[str, str]:
    """Generate natural language summary for an activity.

    Returns:
        tuple of (short_summary, detailed_summary)
        - short_summary: 12-20 words, shown in collapsed view
        - detailed_summary: Expanded description with more context
    """
    short = ""
    detail = ""

    # Parse tool input if available
    input_data = {}
    if tool_input:
        try:
            input_data = json.loads(tool_input)
        except (json.JSONDecodeError, TypeError):
            pass

    # Generate summaries based on tool type
    if tool_name == "Read":
        path = input_data.get("file_path", file_path or "unknown file")
        filename = Path(path).name if path else "file"
        short = f"Read file: {filename}"
        detail = f"Reading contents of {path}"

    elif tool_name == "Write":
        path = input_data.get("file_path", file_path or "unknown file")
        filename = Path(path).name if path else "file"
        short = f"Write file: {filename}"
        detail = f"Writing/creating file at {path}"

    elif tool_name == "Edit":
        path = input_data.get("file_path", file_path or "unknown file")
        filename = Path(path).name if path else "file"
        short = f"Edit file: {filename}"
        detail = f"Editing {path} - replacing text content"

    elif tool_name == "Bash":
        cmd = input_data.get("command", "")[:50]
        short = f"Run command: {cmd}..."
        detail = f"Executing bash command: {input_data.get('command', 'unknown')}"

    elif tool_name == "Grep":
        pattern = input_data.get("pattern", "")
        short = f"Search for: {pattern[:30]}"
        detail = f"Searching codebase for pattern: {pattern}"

    elif tool_name == "Glob":
        pattern = input_data.get("pattern", "")
        short = f"Find files: {pattern[:30]}"
        detail = f"Finding files matching pattern: {pattern}"

    elif tool_name == "Skill":
        skill = input_data.get("skill", "unknown")
        short = f"Run skill: /{skill}"
        detail = f"Executing slash command /{skill}"

    elif tool_name == "Task":
        desc = input_data.get("description", "task")
        short = f"Spawn agent: {desc[:30]}"
        detail = f"Launching sub-agent for: {input_data.get('prompt', desc)[:100]}"

    elif tool_name == "WebSearch":
        query = input_data.get("query", "")
        short = f"Web search: {query[:30]}"
        detail = f"Searching the web for: {query}"

    elif tool_name == "WebFetch":
        url = input_data.get("url", "")
        short = f"Fetch URL: {url[:40]}"
        detail = f"Fetching content from: {url}"

    elif tool_name == "TodoWrite":
        todos = input_data.get("todos", [])
        count = len(todos) if isinstance(todos, list) else 0
        short = f"Update todo list: {count} items"
        detail = f"Managing task list with {count} items"

    elif tool_name == "AskUserQuestion":
        questions = input_data.get("questions", [])
        count = len(questions) if isinstance(questions, list) else 1
        short = f"Ask user: {count} question(s)"
        detail = f"Prompting user for input with {count} question(s)"

    elif tool_name and tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        server = parts[1] if len(parts) > 1 else "unknown"
        tool = parts[2] if len(parts) > 2 else tool_name
        short = f"MCP call: {server}/{tool}"
        detail = f"Calling {tool} tool from MCP server {server}"

    elif tool_name == "cortex_remember" or (tool_name and "remember" in tool_name.lower()):
        params = input_data.get("params", {})
        content = params.get("content", "") if isinstance(params, dict) else ""
        short = f"Store memory: {content[:30]}..." if content else "Store memory"
        detail = f"Saving to memory system: {content[:100]}" if content else "Saving to memory system"

    elif tool_name == "cortex_recall" or (tool_name and "recall" in tool_name.lower()):
        params = input_data.get("params", {})
        query = params.get("query", "") if isinstance(params, dict) else ""
        short = f"Recall: {query[:30]}" if query else "Recall memories"
        detail = f"Searching memories for: {query}" if query else "Retrieving memories"

    elif tool_name == "NotebookEdit":
        path = input_data.get("notebook_path", "")
        filename = Path(path).name if path else "notebook"
        short = f"Edit notebook: {filename}"
        detail = f"Editing Jupyter notebook {path}"

    else:
        short = f"{event_type}: {tool_name or 'unknown'}"
        detail = f"Activity type {event_type} with tool {tool_name}"

    # Add status suffix for failures
    if not success:
        short = f"[FAILED] {short}"
        detail = f"[FAILED] {detail}"

    return short, detail
