from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket


class RealtimeConnectionManager:
    def __init__(self) -> None:
        self._tenant_rooms: dict[int, set[WebSocket]] = defaultdict(set)
        self._event_rooms: dict[tuple[int, int], set[WebSocket]] = defaultdict(set)
        self._meta: dict[WebSocket, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, tenant_id: int, user_id: int | None = None, event_id: int | None = None) -> None:
        await websocket.accept()
        async with self._lock:
            self._tenant_rooms[int(tenant_id)].add(websocket)
            if event_id is not None:
                self._event_rooms[(int(tenant_id), int(event_id))].add(websocket)
            self._meta[websocket] = {
                'tenant_id': int(tenant_id),
                'event_id': int(event_id) if event_id else None,
                'user_id': int(user_id) if user_id else None,
                'connected_at': datetime.now(timezone.utc).isoformat(),
            }
        await self.send_personal(websocket, {'type': 'connected', 'payload': {'tenant_id': tenant_id, 'event_id': event_id}})

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            meta = self._meta.pop(websocket, {})
            tenant_id = meta.get('tenant_id')
            event_id = meta.get('event_id')
            if tenant_id is not None:
                self._tenant_rooms[int(tenant_id)].discard(websocket)
            if tenant_id is not None and event_id is not None:
                self._event_rooms[(int(tenant_id), int(event_id))].discard(websocket)

    async def send_personal(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        await websocket.send_text(json.dumps(message, ensure_ascii=False, default=str))

    async def broadcast_tenant(self, tenant_id: int, message: dict[str, Any]) -> int:
        sockets = list(self._tenant_rooms.get(int(tenant_id), set()))
        return await self._broadcast(sockets, message)

    async def broadcast_event(self, tenant_id: int, event_id: int, message: dict[str, Any]) -> int:
        sockets = list(self._event_rooms.get((int(tenant_id), int(event_id)), set()))
        if not sockets:
            sockets = list(self._tenant_rooms.get(int(tenant_id), set()))
        return await self._broadcast(sockets, message)

    async def _broadcast(self, sockets: list[WebSocket], message: dict[str, Any]) -> int:
        delivered = 0
        stale: list[WebSocket] = []
        payload = json.dumps(message, ensure_ascii=False, default=str)
        for socket in sockets:
            try:
                await socket.send_text(payload)
                delivered += 1
            except Exception:
                stale.append(socket)
        for socket in stale:
            await self.disconnect(socket)
        return delivered

    def stats(self) -> dict[str, Any]:
        return {
            'connections': len(self._meta),
            'tenant_rooms': {str(k): len(v) for k, v in self._tenant_rooms.items()},
            'event_rooms': {f'{k[0]}:{k[1]}': len(v) for k, v in self._event_rooms.items()},
        }


realtime_manager = RealtimeConnectionManager()
