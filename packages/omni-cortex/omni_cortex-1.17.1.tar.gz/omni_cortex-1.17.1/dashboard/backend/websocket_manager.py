"""WebSocket manager for real-time updates."""

import asyncio
import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import WebSocket


class WebSocketManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        self.connections: dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str | None = None) -> str:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        client_id = client_id or str(uuid4())
        async with self._lock:
            self.connections[client_id] = websocket
        print(f"[WS] Client connected: {client_id} (total: {len(self.connections)})")
        return client_id

    async def disconnect(self, client_id: str):
        """Remove a WebSocket connection."""
        async with self._lock:
            if client_id in self.connections:
                del self.connections[client_id]
        print(f"[WS] Client disconnected: {client_id} (total: {len(self.connections)})")

    async def broadcast(self, event_type: str, data: dict[str, Any]):
        """Broadcast a message to all connected clients."""
        if not self.connections:
            return

        message = json.dumps({
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }, default=str)

        disconnected = []
        async with self._lock:
            for client_id, websocket in self.connections.items():
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    print(f"[WS] Failed to send to {client_id}: {e}")
                    disconnected.append(client_id)

            # Clean up disconnected clients
            for client_id in disconnected:
                del self.connections[client_id]

    async def send_to_client(self, client_id: str, event_type: str, data: dict[str, Any]):
        """Send a message to a specific client."""
        message = json.dumps({
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }, default=str)

        async with self._lock:
            if client_id in self.connections:
                try:
                    await self.connections[client_id].send_text(message)
                except Exception as e:
                    print(f"[WS] Failed to send to {client_id}: {e}")
                    del self.connections[client_id]

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.connections)

    # Typed broadcast methods (IndyDevDan pattern)
    async def broadcast_activity_logged(self, project: str, activity: dict[str, Any]):
        """Broadcast when a new activity is logged."""
        await self.broadcast("activity_logged", {
            "project": project,
            "activity": activity,
        })

    async def broadcast_session_updated(self, project: str, session: dict[str, Any]):
        """Broadcast when a session is updated."""
        await self.broadcast("session_updated", {
            "project": project,
            "session": session,
        })

    async def broadcast_stats_updated(self, project: str, stats: dict[str, Any]):
        """Broadcast when stats change (for charts/panels)."""
        await self.broadcast("stats_updated", {
            "project": project,
            "stats": stats,
        })


# Global manager instance
manager = WebSocketManager()
