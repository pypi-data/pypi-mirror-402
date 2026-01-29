"""FastAPI backend for Omni-Cortex Web Dashboard."""
# Trigger reload for relationship graph column fix

import asyncio
import json
import os
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Rate limiting imports (optional - graceful degradation if not installed)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    Limiter = None

from database import (
    bulk_update_memory_status,
    create_memory,
    delete_memory,
    delete_user_message,
    delete_user_messages_bulk,
    ensure_migrations,
    get_activities,
    get_activity_detail,
    get_activity_heatmap,
    get_agents,
    get_agent_by_id,
    get_agent_files_touched,
    get_agent_parent,
    get_agent_tool_breakdown,
    get_all_tags,
    get_command_usage,
    get_mcp_usage,
    get_memories,
    get_memories_needing_review,
    get_memory_by_id,
    get_memory_growth,
    get_memory_stats,
    get_recent_sessions,
    get_relationship_graph,
    get_relationships,
    get_sessions,
    get_skill_usage,
    get_style_profile,
    get_style_samples,
    get_style_samples_by_category,
    compute_style_profile_from_messages,
    get_timeline,
    get_tool_usage,
    get_type_distribution,
    get_user_message_count,
    get_user_messages,
    search_memories,
    update_memory,
)
from logging_config import log_success, log_error
from models import (
    AggregateChatRequest,
    AggregateMemoryRequest,
    AggregateStatsRequest,
    AggregateStatsResponse,
    BatchImageGenerationRequest,
    BatchImageGenerationResponse,
    BulkDeleteRequest,
    ChatRequest,
    ChatResponse,
    ComposeRequest,
    ComposeResponse,
    ConversationSaveRequest,
    ConversationSaveResponse,
    FilterParams,
    ImageRefineRequest,
    MemoryCreateRequest,
    MemoryUpdate,
    ProjectInfo,
    ProjectRegistration,
    SingleImageRequestModel,
    SingleImageResponseModel,
    StyleProfile,
    StyleSample,
    UserMessage,
    UserMessagesResponse,
)
from project_config import (
    load_config,
    add_registered_project,
    remove_registered_project,
    toggle_favorite,
    add_scan_directory,
    remove_scan_directory,
)
from project_scanner import scan_projects
from websocket_manager import manager
import chat_service
from image_service import image_service, ImagePreset, SingleImageRequest
from security import PathValidator, get_cors_config, IS_PRODUCTION


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Vue needs these
            "style-src 'self' 'unsafe-inline'; "  # Tailwind needs inline
            "img-src 'self' data: blob: https:; "  # Allow AI-generated images
            "connect-src 'self' ws: wss: https://generativelanguage.googleapis.com; "
            "font-src 'self'; "
            "frame-ancestors 'none';"
        )

        # HSTS (only in production with HTTPS)
        if IS_PRODUCTION and os.getenv("SSL_CERTFILE"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


def validate_project_path(project: str = Query(..., description="Path to the database file")) -> Path:
    """Validate project database path - dependency for endpoints."""
    try:
        return PathValidator.validate_project_path(project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class DatabaseChangeHandler(FileSystemEventHandler):
    """Handle database file changes for real-time updates."""

    def __init__(self, ws_manager, loop):
        self.ws_manager = ws_manager
        self.loop = loop
        self._debounce_task: Optional[asyncio.Task] = None
        self._last_path: Optional[str] = None
        self._last_activity_count: dict[str, int] = {}

    def on_modified(self, event):
        if event.src_path.endswith("cortex.db") or event.src_path.endswith("global.db"):
            # Debounce rapid changes
            self._last_path = event.src_path
            if self._debounce_task is None or self._debounce_task.done():
                self._debounce_task = asyncio.run_coroutine_threadsafe(
                    self._debounced_notify(), self.loop
                )

    async def _debounced_notify(self):
        await asyncio.sleep(0.3)  # Reduced from 0.5s for faster updates
        if self._last_path:
            db_path = self._last_path

            # Broadcast general database change
            await self.ws_manager.broadcast("database_changed", {"path": db_path})

            # Fetch and broadcast latest activities (IndyDevDan pattern)
            try:
                # Get recent activities
                recent = get_activities(db_path, limit=5, offset=0)
                if recent:
                    # Broadcast each new activity
                    for activity in recent:
                        await self.ws_manager.broadcast_activity_logged(
                            db_path,
                            activity if isinstance(activity, dict) else activity.model_dump()
                        )

                    # Also broadcast session update
                    sessions = get_recent_sessions(db_path, limit=1)
                    if sessions:
                        session = sessions[0]
                        await self.ws_manager.broadcast_session_updated(
                            db_path,
                            session if isinstance(session, dict) else dict(session)
                        )
            except Exception as e:
                print(f"[WS] Error broadcasting activities: {e}")


# File watcher
observer: Optional[Observer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage file watcher lifecycle."""
    global observer
    loop = asyncio.get_event_loop()
    handler = DatabaseChangeHandler(manager, loop)
    observer = Observer()

    # Watch common project directories
    watch_paths = [
        Path.home() / ".omni-cortex",
        Path("D:/Projects"),
    ]

    for watch_path in watch_paths:
        if watch_path.exists():
            observer.schedule(handler, str(watch_path), recursive=True)
            print(f"[Watcher] Monitoring: {watch_path}")

    observer.start()
    print("[Server] File watcher started")

    yield

    observer.stop()
    observer.join()
    print("[Server] File watcher stopped")


# FastAPI app
app = FastAPI(
    title="Omni-Cortex Dashboard",
    description="Web dashboard for viewing and managing Omni-Cortex memories",
    version="0.1.0",
    lifespan=lifespan,
)

# Add security headers middleware (MUST come before CORS)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting (if available)
if RATE_LIMITING_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
else:
    limiter = None


def rate_limit(limit_string: str):
    """Decorator for conditional rate limiting.

    Returns the actual limiter decorator if available, otherwise a no-op.
    Usage: @rate_limit("10/minute")
    """
    if limiter is not None:
        return limiter.limit(limit_string)
    # No-op decorator when rate limiting is not available
    def noop_decorator(func):
        return func
    return noop_decorator

# CORS configuration (environment-aware)
cors_config = get_cors_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config["allow_origins"],
    allow_credentials=True,
    allow_methods=cors_config["allow_methods"],
    allow_headers=cors_config["allow_headers"],
)

# Static files for production build
DASHBOARD_DIR = Path(__file__).parent.parent
DIST_DIR = DASHBOARD_DIR / "frontend" / "dist"


def setup_static_files():
    """Mount static files if dist directory exists (production build)."""
    if DIST_DIR.exists():
        # Mount assets directory
        assets_dir = DIST_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
            print(f"[Static] Serving assets from: {assets_dir}")


# Call setup at module load
setup_static_files()


# --- REST Endpoints ---


@app.get("/api/projects", response_model=list[ProjectInfo])
async def list_projects():
    """List all discovered omni-cortex project databases."""
    return scan_projects()


# --- Project Management Endpoints ---


@app.get("/api/projects/config")
async def get_project_config():
    """Get project configuration (scan dirs, counts)."""
    config = load_config()
    return {
        "scan_directories": config.scan_directories,
        "registered_count": len(config.registered_projects),
        "favorites_count": len(config.favorites),
    }


@app.post("/api/projects/register")
async def register_project(body: ProjectRegistration):
    """Manually register a project by path."""
    success = add_registered_project(body.path, body.display_name)
    if not success:
        raise HTTPException(400, "Invalid path or already registered")
    return {"success": True}


@app.delete("/api/projects/register")
async def unregister_project(path: str = Query(..., description="Project path to unregister")):
    """Remove a registered project."""
    success = remove_registered_project(path)
    if not success:
        raise HTTPException(404, "Project not found")
    return {"success": True}


@app.post("/api/projects/favorite")
async def toggle_project_favorite(path: str = Query(..., description="Project path to toggle favorite")):
    """Toggle favorite status for a project."""
    is_favorite = toggle_favorite(path)
    return {"is_favorite": is_favorite}


@app.post("/api/projects/scan-directories")
async def add_scan_dir(directory: str = Query(..., description="Directory path to add")):
    """Add a directory to auto-scan list."""
    success = add_scan_directory(directory)
    if not success:
        raise HTTPException(400, "Invalid directory or already added")
    return {"success": True}


@app.delete("/api/projects/scan-directories")
async def remove_scan_dir(directory: str = Query(..., description="Directory path to remove")):
    """Remove a directory from auto-scan list."""
    success = remove_scan_directory(directory)
    if not success:
        raise HTTPException(404, "Directory not found")
    return {"success": True}


@app.post("/api/projects/refresh")
async def refresh_projects():
    """Force rescan of all project directories."""
    projects = scan_projects()
    return {"count": len(projects)}


# --- Aggregate Multi-Project Endpoints ---


@app.post("/api/aggregate/memories")
@rate_limit("50/minute")
async def get_aggregate_memories(request: AggregateMemoryRequest):
    """Get memories from multiple projects with project attribution."""
    try:
        all_memories = []
        filters = request.filters or FilterParams()

        for project_path in request.projects:
            if not Path(project_path).exists():
                continue

            try:
                memories = get_memories(project_path, filters)
                # Add project attribution to each memory
                for m in memories:
                    m_dict = m.model_dump()
                    m_dict['source_project'] = project_path
                    # Extract project name from path
                    project_dir = Path(project_path).parent
                    m_dict['source_project_name'] = project_dir.name
                    all_memories.append(m_dict)
            except Exception as e:
                log_error(f"/api/aggregate/memories (project: {project_path})", e)
                continue

        # Sort by last_accessed or created_at (convert to str to handle mixed tz-aware/naive)
        all_memories.sort(
            key=lambda x: str(x.get('last_accessed') or x.get('created_at') or ''),
            reverse=True
        )

        # Apply pagination
        start = filters.offset
        end = start + filters.limit
        return all_memories[start:end]
    except Exception as e:
        log_error("/api/aggregate/memories", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/aggregate/stats", response_model=AggregateStatsResponse)
@rate_limit("50/minute")
async def get_aggregate_stats(request: AggregateStatsRequest):
    """Get combined statistics across multiple projects."""
    try:
        total_count = 0
        total_access = 0
        importance_sum = 0
        by_type = {}
        by_status = {}

        for project_path in request.projects:
            if not Path(project_path).exists():
                continue

            try:
                stats = get_memory_stats(project_path)
                total_count += stats.total_count
                total_access += stats.total_access_count

                # Weighted average for importance
                project_count = stats.total_count
                project_avg_importance = stats.avg_importance
                importance_sum += project_avg_importance * project_count

                # Aggregate by_type
                for type_name, count in stats.by_type.items():
                    by_type[type_name] = by_type.get(type_name, 0) + count

                # Aggregate by_status
                for status, count in stats.by_status.items():
                    by_status[status] = by_status.get(status, 0) + count
            except Exception as e:
                log_error(f"/api/aggregate/stats (project: {project_path})", e)
                continue

        return AggregateStatsResponse(
            total_count=total_count,
            total_access_count=total_access,
            avg_importance=round(importance_sum / total_count, 1) if total_count > 0 else 0,
            by_type=by_type,
            by_status=by_status,
            project_count=len(request.projects),
        )
    except Exception as e:
        log_error("/api/aggregate/stats", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/aggregate/tags")
@rate_limit("50/minute")
async def get_aggregate_tags(request: AggregateStatsRequest):
    """Get combined tags across multiple projects."""
    try:
        tag_counts = {}

        for project_path in request.projects:
            if not Path(project_path).exists():
                continue

            try:
                tags = get_all_tags(project_path)
                for tag in tags:
                    tag_name = tag['name']
                    tag_counts[tag_name] = tag_counts.get(tag_name, 0) + tag['count']
            except Exception as e:
                log_error(f"/api/aggregate/tags (project: {project_path})", e)
                continue

        # Return sorted by count
        return sorted(
            [{'name': k, 'count': v} for k, v in tag_counts.items()],
            key=lambda x: x['count'],
            reverse=True
        )
    except Exception as e:
        log_error("/api/aggregate/tags", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/aggregate/chat", response_model=ChatResponse)
@rate_limit("10/minute")
async def chat_across_projects(request: AggregateChatRequest):
    """Ask AI about memories across multiple projects."""
    try:
        if not chat_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Chat service not available. Set GEMINI_API_KEY environment variable."
            )

        all_sources = []

        # Gather relevant memories from each project
        for project_path in request.projects:
            if not Path(project_path).exists():
                continue

            try:
                memories = search_memories(
                    project_path,
                    request.question,
                    limit=request.max_memories_per_project
                )

                for m in memories:
                    project_dir = Path(project_path).parent
                    source = {
                        'id': m.id,
                        'type': m.memory_type,
                        'content_preview': m.content[:200],
                        'tags': m.tags,
                        'project_path': project_path,
                        'project_name': project_dir.name,
                    }
                    all_sources.append(source)
            except Exception as e:
                log_error(f"/api/aggregate/chat (project: {project_path})", e)
                continue

        if not all_sources:
            return ChatResponse(
                answer="No relevant memories found across the selected projects.",
                sources=[],
            )

        # Build context with project attribution
        context = "\n\n".join([
            f"[From: {s['project_name']}] {s['content_preview']}"
            for s in all_sources
        ])

        # Query AI with attributed context
        answer = await chat_service.generate_response(request.question, context)

        log_success("/api/aggregate/chat", projects=len(request.projects), sources=len(all_sources))

        return ChatResponse(
            answer=answer,
            sources=[ChatSource(**s) for s in all_sources],
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error("/api/aggregate/chat", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memories")
@rate_limit("100/minute")
async def list_memories(
    project: str = Query(..., description="Path to the database file"),
    memory_type: Optional[str] = Query(None, alias="type"),
    status: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    min_importance: Optional[int] = None,
    max_importance: Optional[int] = None,
    sort_by: str = "last_accessed",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0,
):
    """Get memories with filtering and pagination."""
    try:
        if not Path(project).exists():
            log_error("/api/memories", FileNotFoundError("Database not found"), project=project)
            raise HTTPException(status_code=404, detail="Database not found")

        filters = FilterParams(
            memory_type=memory_type,
            status=status,
            tags=tags.split(",") if tags else None,
            search=search,
            min_importance=min_importance,
            max_importance=max_importance,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

        memories = get_memories(project, filters)
        log_success("/api/memories", count=len(memories), offset=offset, filters=bool(search or memory_type))
        return memories
    except Exception as e:
        log_error("/api/memories", e, project=project)
        raise


@app.post("/api/memories")
@rate_limit("30/minute")
async def create_memory_endpoint(
    request: MemoryCreateRequest,
    project: str = Query(..., description="Path to the database file"),
):
    """Create a new memory."""
    try:
        if not Path(project).exists():
            log_error("/api/memories POST", FileNotFoundError("Database not found"), project=project)
            raise HTTPException(status_code=404, detail="Database not found")

        # Create the memory
        memory_id = create_memory(
            db_path=project,
            content=request.content,
            memory_type=request.memory_type,
            context=request.context,
            tags=request.tags if request.tags else None,
            importance_score=request.importance_score,
        )

        # Fetch the created memory to return it
        created_memory = get_memory_by_id(project, memory_id)

        # Broadcast to WebSocket clients
        await manager.broadcast("memory_created", created_memory.model_dump(by_alias=True))

        log_success("/api/memories POST", memory_id=memory_id, type=request.memory_type)
        return created_memory
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[DEBUG] create_memory_endpoint error: {type(e).__name__}: {e}")
        traceback.print_exc()
        log_error("/api/memories POST", e, project=project)
        raise


# NOTE: These routes MUST be defined before /api/memories/{memory_id} to avoid path conflicts
@app.get("/api/memories/needs-review")
async def get_memories_needing_review_endpoint(
    project: str = Query(..., description="Path to the database file"),
    days_threshold: int = 30,
    limit: int = 50,
):
    """Get memories that may need freshness review."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_memories_needing_review(project, days_threshold, limit)


@app.post("/api/memories/bulk-update-status")
async def bulk_update_status_endpoint(
    project: str = Query(..., description="Path to the database file"),
    memory_ids: list[str] = [],
    status: str = "fresh",
):
    """Update status for multiple memories at once."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    valid_statuses = ["fresh", "needs_review", "outdated", "archived"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    count = bulk_update_memory_status(project, memory_ids, status)

    # Notify connected clients
    await manager.broadcast("memories_bulk_updated", {"count": count, "status": status})

    return {"updated_count": count, "status": status}


@app.get("/api/memories/{memory_id}")
async def get_memory(
    memory_id: str,
    project: str = Query(..., description="Path to the database file"),
):
    """Get a single memory by ID."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    memory = get_memory_by_id(project, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@app.put("/api/memories/{memory_id}")
async def update_memory_endpoint(
    memory_id: str,
    updates: MemoryUpdate,
    project: str = Query(..., description="Path to the database file"),
):
    """Update a memory."""
    try:
        if not Path(project).exists():
            log_error("/api/memories/update", FileNotFoundError("Database not found"), memory_id=memory_id)
            raise HTTPException(status_code=404, detail="Database not found")

        updated = update_memory(project, memory_id, updates)
        if not updated:
            log_error("/api/memories/update", ValueError("Memory not found"), memory_id=memory_id)
            raise HTTPException(status_code=404, detail="Memory not found")

        # Notify connected clients
        await manager.broadcast("memory_updated", updated.model_dump(by_alias=True))
        log_success("/api/memories/update", memory_id=memory_id, fields_updated=len(updates.model_dump(exclude_unset=True)))
        return updated
    except HTTPException:
        raise
    except Exception as e:
        log_error("/api/memories/update", e, memory_id=memory_id)
        raise


@app.delete("/api/memories/{memory_id}")
async def delete_memory_endpoint(
    memory_id: str,
    project: str = Query(..., description="Path to the database file"),
):
    """Delete a memory."""
    try:
        if not Path(project).exists():
            log_error("/api/memories/delete", FileNotFoundError("Database not found"), memory_id=memory_id)
            raise HTTPException(status_code=404, detail="Database not found")

        deleted = delete_memory(project, memory_id)
        if not deleted:
            log_error("/api/memories/delete", ValueError("Memory not found"), memory_id=memory_id)
            raise HTTPException(status_code=404, detail="Memory not found")

        # Notify connected clients
        await manager.broadcast("memory_deleted", {"id": memory_id})
        log_success("/api/memories/delete", memory_id=memory_id)
        return {"message": "Memory deleted", "id": memory_id}
    except HTTPException:
        raise
    except Exception as e:
        log_error("/api/memories/delete", e, memory_id=memory_id)
        raise


@app.get("/api/memories/stats/summary")
async def memory_stats(
    project: str = Query(..., description="Path to the database file"),
):
    """Get memory statistics."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_memory_stats(project)


@app.get("/api/search")
async def search(
    q: str = Query(..., min_length=1),
    project: str = Query(..., description="Path to the database file"),
    limit: int = 20,
):
    """Search memories."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return search_memories(project, q, limit)


@app.get("/api/activities")
async def list_activities(
    project: str = Query(..., description="Path to the database file"),
    event_type: Optional[str] = None,
    tool_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """Get activity log entries."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    # Ensure migrations are applied (adds summary columns if missing)
    ensure_migrations(project)

    activities = get_activities(project, event_type, tool_name, limit, offset)
    return {"activities": activities, "count": len(activities)}


@app.get("/api/timeline")
async def get_timeline_view(
    project: str = Query(..., description="Path to the database file"),
    hours: int = 24,
    include_memories: bool = True,
    include_activities: bool = True,
):
    """Get timeline of recent activity."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_timeline(project, hours, include_memories, include_activities)


@app.get("/api/tags")
async def list_tags(
    project: str = Query(..., description="Path to the database file"),
):
    """Get all tags with counts."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_all_tags(project)


@app.get("/api/types")
async def list_types(
    project: str = Query(..., description="Path to the database file"),
):
    """Get memory type distribution."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_type_distribution(project)


@app.get("/api/sessions")
async def list_sessions(
    project: str = Query(..., description="Path to the database file"),
    limit: int = 20,
):
    """Get recent sessions."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_sessions(project, limit)


# --- Stats Endpoints for Charts ---


@app.get("/api/stats/activity-heatmap")
async def get_activity_heatmap_endpoint(
    project: str = Query(..., description="Path to the database file"),
    days: int = 90,
):
    """Get activity counts grouped by day for heatmap visualization."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_activity_heatmap(project, days)


@app.get("/api/stats/tool-usage")
async def get_tool_usage_endpoint(
    project: str = Query(..., description="Path to the database file"),
    limit: int = 10,
):
    """Get tool usage statistics."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_tool_usage(project, limit)


@app.get("/api/stats/memory-growth")
async def get_memory_growth_endpoint(
    project: str = Query(..., description="Path to the database file"),
    days: int = 30,
):
    """Get memory creation over time."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_memory_growth(project, days)


# --- Command Analytics Endpoints ---


@app.get("/api/stats/command-usage")
async def get_command_usage_endpoint(
    project: str = Query(..., description="Path to the database file"),
    scope: Optional[str] = Query(None, description="Filter by scope: 'universal' or 'project'"),
    days: int = Query(30, ge=1, le=365),
):
    """Get slash command usage statistics."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_command_usage(project, scope, days)


@app.get("/api/stats/skill-usage")
async def get_skill_usage_endpoint(
    project: str = Query(..., description="Path to the database file"),
    scope: Optional[str] = Query(None, description="Filter by scope: 'universal' or 'project'"),
    days: int = Query(30, ge=1, le=365),
):
    """Get skill usage statistics."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_skill_usage(project, scope, days)


@app.get("/api/stats/mcp-usage")
async def get_mcp_usage_endpoint(
    project: str = Query(..., description="Path to the database file"),
    days: int = Query(30, ge=1, le=365),
):
    """Get MCP server usage statistics."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_mcp_usage(project, days)


@app.get("/api/activities/{activity_id}")
async def get_activity_detail_endpoint(
    activity_id: str,
    project: str = Query(..., description="Path to the database file"),
):
    """Get full activity details including complete input/output."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    # Ensure migrations are applied
    ensure_migrations(project)

    activity = get_activity_detail(project, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    return activity


@app.post("/api/activities/backfill-summaries")
async def backfill_activity_summaries_endpoint(
    project: str = Query(..., description="Path to the database file"),
):
    """Generate summaries for existing activities that don't have them."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    try:
        from backfill_summaries import backfill_all
        results = backfill_all(project)
        return {
            "success": True,
            "summaries_updated": results["summaries"],
            "mcp_servers_updated": results["mcp_servers"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backfill failed: {str(e)}")


# --- Session Context Endpoints ---


@app.get("/api/sessions/recent")
async def get_recent_sessions_endpoint(
    project: str = Query(..., description="Path to the database file"),
    limit: int = 5,
):
    """Get recent sessions with summaries."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_recent_sessions(project, limit)


# --- Relationship Graph Endpoints ---


@app.get("/api/relationships")
async def get_relationships_endpoint(
    project: str = Query(..., description="Path to the database file"),
    memory_id: Optional[str] = None,
):
    """Get memory relationships for graph visualization."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_relationships(project, memory_id)


@app.get("/api/relationships/graph")
async def get_relationship_graph_endpoint(
    project: str = Query(..., description="Path to the database file"),
    center_id: Optional[str] = None,
    depth: int = 2,
):
    """Get graph data centered on a memory with configurable depth."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_relationship_graph(project, center_id, depth)


# --- Chat Endpoint ---


@app.get("/api/chat/status")
async def chat_status():
    """Check if chat service is available."""
    return {
        "available": chat_service.is_available(),
        "message": "Chat is available" if chat_service.is_available() else "Set GEMINI_API_KEY environment variable to enable chat",
    }


@app.post("/api/chat", response_model=ChatResponse)
@rate_limit("10/minute")
async def chat_with_memories(
    request: ChatRequest,
    project: str = Query(..., description="Path to the database file"),
):
    """Ask a natural language question about memories."""
    try:
        if not Path(project).exists():
            log_error("/api/chat", FileNotFoundError("Database not found"), question=request.question[:50])
            raise HTTPException(status_code=404, detail="Database not found")

        # Fetch style profile if style mode enabled
        style_context = None
        if request.use_style:
            try:
                # First try computed profile from user_messages (richer data)
                style_context = compute_style_profile_from_messages(project)
                # Fall back to stored profile if no user_messages
                if not style_context:
                    style_context = get_style_profile(project)
            except Exception:
                pass  # Graceful fallback if no style data

        result = await chat_service.ask_about_memories(
            project,
            request.question,
            request.max_memories,
            style_context,
        )

        log_success("/api/chat", question_len=len(request.question), sources=len(result.get("sources", [])))
        return ChatResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        log_error("/api/chat", e, question=request.question[:50])
        raise


@app.get("/api/chat/stream")
@rate_limit("10/minute")
async def stream_chat(
    project: str = Query(..., description="Path to the database file"),
    question: str = Query(..., description="The question to ask"),
    max_memories: int = Query(10, ge=1, le=50),
    use_style: bool = Query(False, description="Use user's communication style"),
):
    """SSE endpoint for streaming chat responses."""
    from fastapi.responses import StreamingResponse

    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    # Fetch style profile if style mode enabled
    style_context = None
    if use_style:
        try:
            # First try computed profile from user_messages (richer data)
            style_context = compute_style_profile_from_messages(project)
            # Fall back to stored profile if no user_messages
            if not style_context:
                style_context = get_style_profile(project)
        except Exception:
            pass  # Graceful fallback if no style data

    async def event_generator():
        try:
            async for event in chat_service.stream_ask_about_memories(project, question, max_memories, style_context):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/api/chat/save", response_model=ConversationSaveResponse)
async def save_chat_conversation(
    request: ConversationSaveRequest,
    project: str = Query(..., description="Path to the database file"),
):
    """Save a chat conversation as a memory."""
    try:
        if not Path(project).exists():
            log_error("/api/chat/save", FileNotFoundError("Database not found"))
            raise HTTPException(status_code=404, detail="Database not found")

        result = await chat_service.save_conversation(
            project,
            [msg.model_dump() for msg in request.messages],
            request.referenced_memory_ids,
            request.importance or 60,
        )

        log_success("/api/chat/save", memory_id=result["memory_id"], messages=len(request.messages))
        return ConversationSaveResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        log_error("/api/chat/save", e)
        raise


@app.post("/api/compose-response", response_model=ComposeResponse)
@rate_limit("10/minute")
async def compose_response_endpoint(
    request: ComposeRequest,
    project: str = Query(..., description="Path to the database file"),
):
    """Compose a response to an incoming message in the user's style."""
    try:
        if not Path(project).exists():
            log_error("/api/compose-response", FileNotFoundError("Database not found"))
            raise HTTPException(status_code=404, detail="Database not found")

        # Get style profile
        style_profile = compute_style_profile_from_messages(project)

        # Compose the response
        result = await chat_service.compose_response(
            db_path=project,
            incoming_message=request.incoming_message,
            context_type=request.context_type,
            template=request.template,
            tone_level=request.tone_level,
            include_memories=request.include_memories,
            style_profile=style_profile,
            custom_instructions=request.custom_instructions,
            include_explanation=request.include_explanation,
        )

        if result.get("error"):
            log_error("/api/compose-response", Exception(result["error"]))
            raise HTTPException(status_code=500, detail=result["error"])

        # Build response model
        import uuid
        from datetime import datetime
        response = ComposeResponse(
            id=str(uuid.uuid4()),
            response=result["response"],
            sources=result["sources"],
            style_applied=bool(style_profile and style_profile.get("total_messages", 0) > 0),
            tone_level=request.tone_level,
            template_used=request.template,
            incoming_message=request.incoming_message,
            context_type=request.context_type,
            created_at=datetime.now().isoformat(),
            custom_instructions=request.custom_instructions,
            explanation=result.get("explanation"),
        )

        log_success("/api/compose-response", context=request.context_type, tone=request.tone_level)
        return response
    except HTTPException:
        raise
    except Exception as e:
        log_error("/api/compose-response", e)
        raise HTTPException(status_code=500, detail=str(e))


# --- Image Generation Endpoints ---


@app.get("/api/image/status")
async def get_image_status():
    """Check if image generation is available."""
    return {
        "available": image_service.is_available(),
        "message": "Image generation ready" if image_service.is_available()
                   else "Configure GEMINI_API_KEY and install google-genai for image generation",
    }


@app.get("/api/image/presets")
async def get_image_presets():
    """Get available image preset templates."""
    return {"presets": image_service.get_presets()}


@app.post("/api/image/generate-batch", response_model=BatchImageGenerationResponse)
@rate_limit("5/minute")
async def generate_images_batch(
    request: BatchImageGenerationRequest,
    db_path: str = Query(..., alias="project", description="Path to the database file"),
):
    """Generate multiple images with different presets/prompts."""
    # Validate image count
    if len(request.images) not in [1, 2, 4]:
        return BatchImageGenerationResponse(
            success=False,
            errors=["Must request 1, 2, or 4 images"]
        )

    # Build memory context
    memory_context = ""
    if request.memory_ids:
        memory_context = image_service.build_memory_context(db_path, request.memory_ids)

    # Build chat context
    chat_context = image_service.build_chat_context(request.chat_messages)

    # Convert request models to internal format
    image_requests = [
        SingleImageRequest(
            preset=ImagePreset(img.preset),
            custom_prompt=img.custom_prompt,
            aspect_ratio=img.aspect_ratio,
            image_size=img.image_size
        )
        for img in request.images
    ]

    result = await image_service.generate_batch(
        requests=image_requests,
        memory_context=memory_context,
        chat_context=chat_context,
        use_search_grounding=request.use_search_grounding
    )

    return BatchImageGenerationResponse(
        success=result.success,
        images=[
            SingleImageResponseModel(
                success=img.success,
                image_data=img.image_data,
                text_response=img.text_response,
                thought_signature=img.thought_signature,
                image_id=img.image_id,
                error=img.error,
                index=img.index
            )
            for img in result.images
        ],
        errors=result.errors
    )


@app.post("/api/image/refine", response_model=SingleImageResponseModel)
@rate_limit("5/minute")
async def refine_image(request: ImageRefineRequest):
    """Refine an existing generated image with a new prompt."""
    result = await image_service.refine_image(
        image_id=request.image_id,
        refinement_prompt=request.refinement_prompt,
        aspect_ratio=request.aspect_ratio,
        image_size=request.image_size
    )

    return SingleImageResponseModel(
        success=result.success,
        image_data=result.image_data,
        text_response=result.text_response,
        thought_signature=result.thought_signature,
        image_id=result.image_id,
        error=result.error
    )


@app.post("/api/image/clear-conversation")
async def clear_image_conversation(image_id: Optional[str] = None):
    """Clear image conversation history. If image_id provided, clear only that image."""
    image_service.clear_conversation(image_id)
    return {"status": "cleared", "image_id": image_id}


# --- User Messages & Style Profile Endpoints ---


@app.get("/api/user-messages", response_model=UserMessagesResponse)
@rate_limit("100/minute")
async def list_user_messages(
    project: str = Query(..., description="Path to the database file"),
    session_id: Optional[str] = None,
    search: Optional[str] = None,
    has_code_blocks: Optional[bool] = None,
    has_questions: Optional[bool] = None,
    has_commands: Optional[bool] = None,
    tone_filter: Optional[str] = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get user messages with filtering and pagination.

    Filter options:
    - session_id: Filter by session
    - search: Search in message content
    - has_code_blocks: Filter by presence of code blocks
    - has_questions: Filter by presence of questions
    - has_commands: Filter by slash commands
    - tone_filter: Filter by tone indicator (polite, urgent, technical, casual, direct, inquisitive)
    """
    try:
        if not Path(project).exists():
            raise HTTPException(status_code=404, detail="Database not found")

        messages = get_user_messages(
            project,
            session_id=session_id,
            search=search,
            has_code_blocks=has_code_blocks,
            has_questions=has_questions,
            has_commands=has_commands,
            tone_filter=tone_filter,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

        total_count = get_user_message_count(project, session_id=session_id)
        has_more = (offset + len(messages)) < total_count

        log_success("/api/user-messages", count=len(messages), total=total_count)
        return UserMessagesResponse(
            messages=[UserMessage(**m) for m in messages],
            total_count=total_count,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error("/api/user-messages", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/user-messages/{message_id}")
async def delete_single_user_message(
    message_id: str,
    project: str = Query(..., description="Path to the database file"),
):
    """Delete a single user message by ID."""
    try:
        if not Path(project).exists():
            raise HTTPException(status_code=404, detail="Database not found")

        deleted = delete_user_message(project, message_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Message not found")

        log_success("/api/user-messages/delete", message_id=message_id)
        return {"message": "Message deleted", "id": message_id}
    except HTTPException:
        raise
    except Exception as e:
        log_error("/api/user-messages/delete", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/user-messages/bulk-delete")
async def delete_user_messages_bulk_endpoint(
    request: BulkDeleteRequest,
    project: str = Query(..., description="Path to the database file"),
):
    """Delete multiple user messages at once."""
    try:
        if not Path(project).exists():
            raise HTTPException(status_code=404, detail="Database not found")

        count = delete_user_messages_bulk(project, request.message_ids)

        log_success("/api/user-messages/bulk-delete", deleted_count=count)
        return {"message": f"Deleted {count} messages", "deleted_count": count}
    except HTTPException:
        raise
    except Exception as e:
        log_error("/api/user-messages/bulk-delete", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/style/profile")
async def get_style_profile_endpoint(
    project: str = Query(..., description="Path to the database file"),
    project_path: Optional[str] = Query(None, description="Project-specific profile path, or None for global"),
):
    """Get user style profile for style analysis.

    Returns style metrics computed from user messages:
    - total_messages: Total message count
    - avg_word_count: Average words per message
    - primary_tone: Most common tone (direct, polite, technical, etc.)
    - question_percentage: Percentage of messages containing questions
    - tone_distribution: Count of messages by tone
    - style_markers: Descriptive labels for writing style
    """
    try:
        if not Path(project).exists():
            raise HTTPException(status_code=404, detail="Database not found")

        # First try to get pre-computed profile from user_style_profiles table
        profile = get_style_profile(project, project_path=project_path)

        # If no stored profile, compute from user_messages
        if not profile:
            profile = compute_style_profile_from_messages(project)

        # If still no profile (no user_messages), return empty structure
        if not profile:
            return {
                "totalMessages": 0,
                "avgWordCount": 0,
                "primaryTone": "direct",
                "questionPercentage": 0,
                "toneDistribution": {},
                "styleMarkers": ["No data available yet"],
            }

        # Convert stored profile format to frontend expected format if needed
        if "totalMessages" in profile:
            # Already in camelCase format from compute_style_profile_from_messages
            pass
        elif "id" in profile:
            # Convert stored profile (from user_style_profiles table) to frontend format
            tone_dist = {}
            # Stored profile doesn't have tone_distribution, so compute it
            computed = compute_style_profile_from_messages(project)
            if computed:
                tone_dist = computed.get("toneDistribution", {})
                primary_tone = computed.get("primaryTone", "direct")
                style_markers = computed.get("styleMarkers", [])
            else:
                primary_tone = "direct"
                style_markers = []

            profile = {
                "totalMessages": profile.get("total_messages", 0),
                "avgWordCount": profile.get("avg_word_count", 0) or 0,
                "primaryTone": primary_tone,
                "questionPercentage": (profile.get("question_frequency", 0) or 0) * 100,
                "toneDistribution": tone_dist,
                "styleMarkers": style_markers or profile.get("greeting_patterns", []) or [],
            }

        log_success("/api/style/profile", has_profile=True, total_messages=profile.get("totalMessages", 0))
        return profile
    except HTTPException:
        raise
    except Exception as e:
        log_error("/api/style/profile", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/style/samples")
async def get_style_samples_endpoint(
    project: str = Query(..., description="Path to the database file"),
    samples_per_tone: int = Query(3, ge=1, le=10, description="Max samples per tone category"),
):
    """Get sample user messages for style analysis preview.

    Returns messages grouped by style category (professional, casual, technical, creative).
    """
    try:
        if not Path(project).exists():
            raise HTTPException(status_code=404, detail="Database not found")

        samples = get_style_samples_by_category(project, samples_per_tone=samples_per_tone)

        total_count = sum(len(v) for v in samples.values())
        log_success("/api/style/samples", count=total_count)
        return samples
    except HTTPException:
        raise
    except Exception as e:
        log_error("/api/style/samples", e)
        raise HTTPException(status_code=500, detail=str(e))


# --- WebSocket Endpoint ---


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    client_id = await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await manager.send_to_client(client_id, "connected", {"client_id": client_id})

        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_text()
            # Echo back for ping/pong
            if data == "ping":
                await manager.send_to_client(client_id, "pong", {})
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
    except Exception as e:
        print(f"[WS] Error: {e}")
        await manager.disconnect(client_id)


# --- Export Endpoints ---


@app.get("/api/export")
async def export_memories(
    project: str = Query(..., description="Path to the database file"),
    format: str = Query("json", description="Export format: json, markdown, csv"),
    memory_ids: Optional[str] = Query(None, description="Comma-separated memory IDs to export, or all if empty"),
    include_relationships: bool = Query(True, description="Include memory relationships"),
):
    """Export memories to specified format."""
    from fastapi.responses import Response
    import csv
    import io

    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    # Get memories
    if memory_ids:
        ids = memory_ids.split(",")
        memories = [get_memory_by_id(project, mid) for mid in ids if mid.strip()]
        memories = [m for m in memories if m is not None]
    else:
        from models import FilterParams
        filters = FilterParams(limit=1000, offset=0, sort_by="created_at", sort_order="desc")
        memories = get_memories(project, filters)

    # Get relationships if requested
    relationships = []
    if include_relationships:
        relationships = get_relationships(project)

    if format == "json":
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "project": project,
            "memory_count": len(memories),
            "memories": [m.model_dump(by_alias=True) for m in memories],
            "relationships": relationships if include_relationships else [],
        }
        return Response(
            content=json.dumps(export_data, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=memories_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
        )

    elif format == "markdown":
        md_lines = [
            f"# Omni-Cortex Memory Export",
            f"",
            f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Memories:** {len(memories)}",
            f"",
            "---",
            "",
        ]
        for m in memories:
            md_lines.extend([
                f"## {m.type.title()}: {m.content[:50]}{'...' if len(m.content) > 50 else ''}",
                f"",
                f"**ID:** `{m.id}`",
                f"**Type:** {m.type}",
                f"**Status:** {m.status}",
                f"**Importance:** {m.importance_score}",
                f"**Created:** {m.created_at}",
                f"**Tags:** {', '.join(m.tags) if m.tags else 'None'}",
                f"",
                "### Content",
                f"",
                m.content,
                f"",
                "### Context",
                f"",
                m.context or "_No context_",
                f"",
                "---",
                "",
            ])
        return Response(
            content="\n".join(md_lines),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=memories_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"}
        )

    elif format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "type", "status", "importance", "content", "context", "tags", "created_at", "last_accessed"])
        for m in memories:
            writer.writerow([
                m.id,
                m.type,
                m.status,
                m.importance_score,
                m.content,
                m.context or "",
                ",".join(m.tags) if m.tags else "",
                m.created_at,
                m.last_accessed or "",
            ])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=memories_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}. Use json, markdown, or csv.")


# --- Agent Endpoints ---


@app.get("/api/agents")
async def list_agents(
    project: str = Query(..., description="Path to the database file"),
    type: Optional[str] = Query(None, description="Filter by agent type: main, subagent, tool"),
    active_only: bool = Query(False, description="Show only active agents (last 5 minutes)"),
    limit: int = Query(50, ge=1, le=200),
):
    """List all agents with filtering."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    agents = get_agents(project, agent_type=type, limit=limit, active_only=active_only)
    return {"agents": agents, "count": len(agents)}


@app.get("/api/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    project: str = Query(..., description="Path to the database file"),
):
    """Get single agent details."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    agent = get_agent_by_id(project, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent


@app.get("/api/agents/{agent_id}/stats")
async def get_agent_stats_endpoint(
    agent_id: str,
    project: str = Query(..., description="Path to the database file"),
):
    """Get detailed stats for an agent."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    agent = get_agent_by_id(project, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    tool_breakdown = get_agent_tool_breakdown(project, agent_id)
    files_touched = get_agent_files_touched(project, agent_id)
    parent_agent = get_agent_parent(project, agent_id) if agent.get('type') == 'subagent' else None

    return {
        "agent": agent,
        "tool_breakdown": tool_breakdown,
        "files_touched": files_touched,
        "parent_agent_id": parent_agent,
        "adw_phase": None  # Will be populated in Part 2 with ADW integration
    }


# --- ADW Endpoints ---


def scan_adw_folder(project_path: str) -> list[dict]:
    """Scan agents/ folder for ADW runs relative to project directory."""
    # Get project directory from db path (e.g., /project/.cortex/cortex.db -> /project)
    project_dir = Path(project_path).parent.parent if project_path.endswith(".db") else Path(project_path)
    agents_dir = project_dir / "agents"

    if not agents_dir.exists():
        return []

    adw_runs = []
    for adw_dir in agents_dir.iterdir():
        if adw_dir.is_dir() and adw_dir.name.startswith("adw_"):
            state_file = adw_dir / "adw_state.json"
            if state_file.exists():
                try:
                    state = json.loads(state_file.read_text())
                    adw_runs.append({
                        "adw_id": state.get("adw_id", adw_dir.name),
                        "created_at": state.get("created_at"),
                        "status": state.get("status", "unknown"),
                        "current_phase": state.get("current_phase", "unknown"),
                        "phases_completed": len(state.get("completed_phases", [])),
                        "phases_total": 4,  # plan, build, validate, release
                        "project_path": str(project_dir)
                    })
                except json.JSONDecodeError:
                    pass

    # Sort by created_at descending
    adw_runs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return adw_runs


def get_adw_state_with_agents(adw_id: str, db_path: str) -> Optional[dict]:
    """Get ADW state with correlated agent activity."""
    # Get project directory from db path
    project_dir = Path(db_path).parent.parent if db_path.endswith(".db") else Path(db_path)
    adw_dir = project_dir / "agents" / adw_id
    state_file = adw_dir / "adw_state.json"

    if not state_file.exists():
        return None

    state = json.loads(state_file.read_text())

    # Build phase info with agent correlation
    phases = []
    all_phases = ["plan", "build", "validate", "release"]
    completed = state.get("completed_phases", [])
    current = state.get("current_phase")

    for phase_name in all_phases:
        phase_dir = adw_dir / phase_name

        # Determine status
        if phase_name in completed:
            status = "completed"
        elif phase_name == current:
            status = "running"
        else:
            status = "pending"

        # Find agents that ran in this phase (from output files) and count calls
        phase_agents = []
        total_phase_calls = 0
        if phase_dir.exists():
            for output_file in phase_dir.glob("*_output.jsonl"):
                agent_name = output_file.stem.replace("_output", "")
                # Count tool_use entries in the JSONL file
                call_count = 0
                try:
                    with open(output_file, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                entry = json.loads(line)
                                if entry.get("type") == "tool_use":
                                    call_count += 1
                            except json.JSONDecodeError:
                                pass
                except Exception:
                    pass
                phase_agents.append({
                    "id": agent_name,
                    "call_count": call_count
                })
                total_phase_calls += call_count

        phases.append({
            "name": phase_name,
            "status": status,
            "agents": phase_agents,  # Now includes id and call_count
            "agent_ids": [a["id"] for a in phase_agents],  # Keep for backwards compat
            "call_count": total_phase_calls,
            "duration_seconds": None  # Could be computed from timestamps if needed
        })

    return {
        "adw_id": state.get("adw_id", adw_id),
        "task_description": state.get("task_description", ""),
        "created_at": state.get("created_at"),
        "current_phase": current,
        "completed_phases": completed,
        "status": state.get("status", "unknown"),
        "phases": phases,
        "project_path": state.get("project_path", "")
    }


@app.get("/api/adw/list")
async def list_adw_runs(
    project: str = Query(..., description="Path to the database file"),
    limit: int = Query(20, ge=1, le=100)
):
    """List all ADW runs from agents/ folder for the selected project."""
    adw_runs = scan_adw_folder(project)[:limit]
    return {"adw_runs": adw_runs, "count": len(adw_runs)}


@app.get("/api/adw/{adw_id}")
async def get_adw_details(
    adw_id: str,
    project: str = Query(..., description="Path to the database file"),
):
    """Get ADW state with agent correlation."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    state = get_adw_state_with_agents(adw_id, project)
    if not state:
        raise HTTPException(status_code=404, detail="ADW not found")

    return state


# --- Health Check ---


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "websocket_connections": manager.connection_count,
    }


# --- Static File Serving (SPA) ---
# These routes must come AFTER all API routes


@app.get("/")
async def serve_root():
    """Serve the frontend index.html."""
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Omni-Cortex Dashboard API", "docs": "/docs"}


@app.get("/{path:path}")
async def serve_spa(path: str):
    """Catch-all route to serve SPA for client-side routing with path traversal protection."""
    # Skip API routes and known paths
    if path.startswith(("api/", "ws", "health", "docs", "openapi", "redoc")):
        raise HTTPException(status_code=404, detail="Not found")

    # Check if it's a static file (with path traversal protection)
    safe_path = PathValidator.is_safe_static_path(DIST_DIR, path)
    if safe_path:
        return FileResponse(str(safe_path))

    # Otherwise serve index.html for SPA routing
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    raise HTTPException(status_code=404, detail="Not found")


def run():
    """Run the dashboard server."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8765,
        reload=True,
        reload_dirs=[str(Path(__file__).parent)],
    )


if __name__ == "__main__":
    run()
