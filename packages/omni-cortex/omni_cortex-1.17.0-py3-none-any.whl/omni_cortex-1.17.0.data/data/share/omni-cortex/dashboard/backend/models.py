"""Pydantic models for the dashboard API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    """Information about a project with omni-cortex database."""

    name: str
    path: str
    db_path: str
    last_modified: Optional[datetime] = None
    memory_count: int = 0
    is_global: bool = False
    is_favorite: bool = False
    is_registered: bool = False
    display_name: Optional[str] = None


class ScanDirectory(BaseModel):
    """A directory being scanned for projects."""

    path: str
    project_count: int = 0


class ProjectRegistration(BaseModel):
    """Request to register a project."""

    path: str
    display_name: Optional[str] = None


class ProjectConfigResponse(BaseModel):
    """Response with project configuration."""

    scan_directories: list[str]
    registered_count: int
    favorites_count: int


class Memory(BaseModel):
    """Memory record from the database."""

    id: str
    content: str
    context: Optional[str] = None
    memory_type: str = Field(default="other", validation_alias="type")
    status: str = "fresh"
    importance_score: int = 50
    access_count: int = 0
    created_at: datetime
    last_accessed: Optional[datetime] = None
    tags: list[str] = []

    model_config = {"populate_by_name": True}


class MemoryStats(BaseModel):
    """Statistics about memories in a database."""

    total_count: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    avg_importance: float
    total_access_count: int
    tags: list[dict[str, int | str]]


class FilterParams(BaseModel):
    """Query filter parameters."""

    memory_type: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[list[str]] = None
    search: Optional[str] = None
    min_importance: Optional[int] = None
    max_importance: Optional[int] = None
    sort_by: str = "last_accessed"
    sort_order: str = "desc"
    limit: int = 50
    offset: int = 0


class AggregateMemoryRequest(BaseModel):
    """Request for aggregate memory data across projects."""

    projects: list[str] = Field(..., description="List of project db paths")
    filters: Optional[FilterParams] = None


class AggregateStatsRequest(BaseModel):
    """Request for aggregate statistics."""

    projects: list[str] = Field(..., description="List of project db paths")


class AggregateStatsResponse(BaseModel):
    """Aggregate statistics across multiple projects."""

    total_count: int
    total_access_count: int
    avg_importance: float
    by_type: dict[str, int]
    by_status: dict[str, int]
    project_count: int


class AggregateChatRequest(BaseModel):
    """Request for chat across multiple projects."""

    projects: list[str] = Field(..., description="List of project db paths")
    question: str = Field(..., min_length=1, max_length=2000)
    max_memories_per_project: int = Field(default=5, ge=1, le=20)


class Activity(BaseModel):
    """Activity log record."""

    id: str
    session_id: Optional[str] = None
    event_type: str
    tool_name: Optional[str] = None
    tool_input: Optional[str] = None
    tool_output: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    file_path: Optional[str] = None
    timestamp: datetime
    # Command analytics fields
    command_name: Optional[str] = None
    command_scope: Optional[str] = None
    mcp_server: Optional[str] = None
    skill_name: Optional[str] = None
    # Natural language summary fields
    summary: Optional[str] = None
    summary_detail: Optional[str] = None


class Session(BaseModel):
    """Session record."""

    id: str
    project_path: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    summary: Optional[str] = None
    activity_count: int = 0


class TimelineEntry(BaseModel):
    """Entry in the timeline view."""

    timestamp: datetime
    entry_type: str  # "memory" or "activity"
    data: dict


class MemoryCreateRequest(BaseModel):
    """Create request for a new memory."""

    content: str = Field(..., min_length=1, max_length=50000)
    memory_type: str = Field(default="general")
    context: Optional[str] = None
    importance_score: int = Field(default=50, ge=1, le=100)
    tags: list[str] = Field(default_factory=list)


class MemoryUpdate(BaseModel):
    """Update request for a memory."""

    content: Optional[str] = None
    context: Optional[str] = None
    memory_type: Optional[str] = Field(None, validation_alias="type")
    status: Optional[str] = None
    importance_score: Optional[int] = Field(None, ge=1, le=100)
    tags: Optional[list[str]] = None

    model_config = {"populate_by_name": True}


class WSEvent(BaseModel):
    """WebSocket event message."""

    event_type: str
    data: dict
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """Request for the chat endpoint."""

    question: str = Field(..., min_length=1, max_length=2000)
    max_memories: int = Field(default=10, ge=1, le=50)
    use_style: bool = Field(default=False)


class ChatSource(BaseModel):
    """Source memory reference in chat response."""

    id: str
    type: str
    content_preview: str
    tags: list[str]
    project_path: Optional[str] = None
    project_name: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""

    answer: str
    sources: list[ChatSource]
    error: Optional[str] = None


class ConversationMessage(BaseModel):
    """A message in a conversation."""

    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str


class ConversationSaveRequest(BaseModel):
    """Request to save a conversation as memory."""

    messages: list[ConversationMessage]
    referenced_memory_ids: Optional[list[str]] = None
    importance: Optional[int] = Field(default=60, ge=1, le=100)


class ConversationSaveResponse(BaseModel):
    """Response after saving a conversation."""

    memory_id: str
    summary: str


# --- Image Generation Models ---


class SingleImageRequestModel(BaseModel):
    """Request for a single image in a batch."""
    preset: str = "custom"  # Maps to ImagePreset enum
    custom_prompt: str = ""
    aspect_ratio: str = "16:9"
    image_size: str = "2K"


class BatchImageGenerationRequest(BaseModel):
    """Request for generating multiple images."""
    images: list[SingleImageRequestModel]  # 1, 2, or 4 images
    memory_ids: list[str] = []
    chat_messages: list[dict] = []  # Recent chat for context
    use_search_grounding: bool = False


class ImageRefineRequest(BaseModel):
    """Request for refining an existing image."""
    image_id: str
    refinement_prompt: str
    aspect_ratio: Optional[str] = None
    image_size: Optional[str] = None


class SingleImageResponseModel(BaseModel):
    """Response for a single generated image."""
    success: bool
    image_data: Optional[str] = None  # Base64 encoded
    text_response: Optional[str] = None
    thought_signature: Optional[str] = None
    image_id: Optional[str] = None
    error: Optional[str] = None
    index: int = 0


class BatchImageGenerationResponse(BaseModel):
    """Response for batch image generation."""
    success: bool
    images: list[SingleImageResponseModel] = []
    errors: list[str] = []


# --- User Messages & Style Profile Models ---


class UserMessage(BaseModel):
    """User message record from the database."""

    id: str
    session_id: Optional[str] = None
    timestamp: Optional[str] = None  # Backward compatibility
    created_at: Optional[str] = None  # Frontend expects created_at
    content: str
    word_count: Optional[int] = None
    char_count: Optional[int] = None
    line_count: Optional[int] = None
    has_code_blocks: bool = False
    has_questions: bool = False
    has_commands: bool = False
    tone: Optional[str] = None  # Primary tone for frontend
    tone_indicators: list[str] = []
    project_path: Optional[str] = None


class UserMessageFilters(BaseModel):
    """Query filter parameters for user messages."""

    session_id: Optional[str] = None
    search: Optional[str] = None
    has_code_blocks: Optional[bool] = None
    has_questions: Optional[bool] = None
    has_commands: Optional[bool] = None
    tone_filter: Optional[str] = None
    sort_by: str = "timestamp"
    sort_order: str = "desc"
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class UserMessagesResponse(BaseModel):
    """Response containing user messages with pagination info."""

    messages: list[UserMessage]
    total_count: int
    limit: int
    offset: int
    has_more: bool = False  # Whether more results are available


class StyleSample(BaseModel):
    """A sample message for style preview."""

    id: str
    timestamp: str
    content_preview: str
    word_count: Optional[int] = None
    has_code_blocks: bool = False
    has_questions: bool = False
    tone_indicators: list[str] = []


class StyleProfile(BaseModel):
    """User style profile for aggregated style analysis."""

    id: str
    project_path: Optional[str] = None
    total_messages: int = 0
    avg_word_count: Optional[float] = None
    avg_char_count: Optional[float] = None
    common_phrases: Optional[list[str]] = None
    vocabulary_richness: Optional[float] = None
    formality_score: Optional[float] = None
    question_frequency: Optional[float] = None
    command_frequency: Optional[float] = None
    code_block_frequency: Optional[float] = None
    punctuation_style: Optional[dict] = None
    greeting_patterns: Optional[list[str]] = None
    instruction_style: Optional[dict] = None
    sample_messages: Optional[list[str]] = None
    created_at: str
    updated_at: str


class BulkDeleteRequest(BaseModel):
    """Request body for bulk delete operations."""

    message_ids: list[str] = Field(..., min_length=1, max_length=100)


# --- Response Composer Models ---


class ComposeRequest(BaseModel):
    """Request for composing a response in user's style."""

    incoming_message: str = Field(..., min_length=1, max_length=5000)
    context_type: str = Field(default="general")  # skool_post, dm, email, comment, general
    template: Optional[str] = None  # answer, guide, redirect, acknowledge
    tone_level: int = Field(default=50, ge=0, le=100)  # 0=casual, 100=professional
    include_memories: bool = Field(default=True)
    custom_instructions: Optional[str] = Field(default=None, max_length=2000)
    include_explanation: bool = Field(default=False)


class ComposeResponse(BaseModel):
    """Response from compose endpoint."""

    id: str
    response: str
    sources: list[ChatSource]
    style_applied: bool
    tone_level: int
    template_used: Optional[str]
    incoming_message: str
    context_type: str
    created_at: str
    custom_instructions: Optional[str] = None
    explanation: Optional[str] = None


# --- Agent & ADW Models ---


class Agent(BaseModel):
    """Agent from the agents table."""

    id: str
    name: Optional[str] = None
    type: str  # 'main', 'subagent', 'tool'
    first_seen: datetime
    last_seen: datetime
    total_activities: int
    recent_activity_count: int = 0  # Activities in last hour
    is_active: bool = False  # Has activity in last 5 minutes


class AgentToolStats(BaseModel):
    """Tool usage breakdown for an agent."""

    tool_name: str
    count: int
    avg_duration_ms: float
    success_rate: float


class AgentStats(BaseModel):
    """Detailed stats for a single agent."""

    agent: Agent
    tool_breakdown: list[AgentToolStats]
    files_touched: list[str]
    parent_agent_id: Optional[str] = None  # If subagent, who spawned it
    adw_phase: Optional[str] = None  # Which ADW phase this agent ran in


class ADWPhaseInfo(BaseModel):
    """Info about a single ADW phase."""

    name: str  # 'plan', 'build', 'validate', 'release'
    status: str  # 'pending', 'running', 'completed', 'failed', 'skipped'
    duration_seconds: Optional[float] = None
    agent_ids: list[str] = []  # Agents that ran in this phase


class ADWState(BaseModel):
    """Full ADW state with agent correlation."""

    adw_id: str
    task_description: str
    created_at: datetime
    current_phase: str
    completed_phases: list[str]
    status: str  # 'running', 'completed', 'failed'
    phases: list[ADWPhaseInfo]
    project_path: str


class ADWListItem(BaseModel):
    """Summary for ADW list."""

    adw_id: str
    created_at: datetime
    status: str
    current_phase: str
    phases_completed: int
    phases_total: int
