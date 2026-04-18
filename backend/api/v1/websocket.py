"""WebSocket endpoint with connection manager.

Usage:
    Include this router in your API:

        from api.v1.websocket import router as ws_router
        api_v1_router.include_router(ws_router)

    Then connect from the frontend:

        const ws = new WebSocket("ws://localhost:3101/api/v1/ws?token=<jwt>");

Supports JWT authentication, room-based broadcasting, and structured
JSON messages.
"""

from typing import Any

import structlog
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["websocket"])


# ---------------------------------------------------------------------------
# Connection manager
# ---------------------------------------------------------------------------


class ConnectionManager:
    """Track active WebSocket connections, optionally grouped by room."""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str = "default") -> None:
        await websocket.accept()
        self._connections.setdefault(room, []).append(websocket)
        logger.info("ws.connected", room=room, total=len(self._connections[room]))

    def disconnect(self, websocket: WebSocket, room: str = "default") -> None:
        conns = self._connections.get(room, [])
        if websocket in conns:
            conns.remove(websocket)
        logger.info("ws.disconnected", room=room, total=len(conns))

    async def send_personal(self, websocket: WebSocket, data: dict[str, Any]) -> None:
        await websocket.send_json(data)

    async def broadcast(self, room: str, data: dict[str, Any], *, exclude: WebSocket | None = None) -> None:
        for connection in self._connections.get(room, []):
            if connection is not exclude:
                try:
                    await connection.send_json(data)
                except Exception:
                    pass

    @property
    def active_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    room: str = Query("default", description="Room to join"),
    token: str | None = Query(None, description="JWT token for auth"),
) -> None:
    """
    WebSocket endpoint with optional JWT authentication.

    Messages should be JSON with a "type" field:
        {"type": "chat", "content": "hello"}
        {"type": "ping"}

    Server responds with:
        {"type": "chat", "content": "...", "from": "user_id"}
        {"type": "pong"}
        {"type": "error", "detail": "..."}
    """
    # Optional: verify JWT token
    user_id = "anonymous"
    if token:
        try:
            from services.auth import verify_token

            payload = verify_token(token)
            user_id = str(payload.get("sub", "anonymous"))
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await manager.connect(websocket, room)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "unknown")

            if msg_type == "ping":
                await manager.send_personal(websocket, {"type": "pong"})

            elif msg_type == "chat":
                await manager.broadcast(
                    room,
                    {
                        "type": "chat",
                        "content": data.get("content", ""),
                        "from": user_id,
                    },
                )

            else:
                await manager.send_personal(
                    websocket,
                    {"type": "error", "detail": f"Unknown message type: {msg_type}"},
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        await manager.broadcast(
            room,
            {"type": "system", "content": f"{user_id} left the room"},
        )
