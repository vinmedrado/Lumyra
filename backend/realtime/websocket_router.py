from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.realtime.manager import realtime_manager
from backend.services.auth_jwt import decode_access_token, get_user_by_id
from backend.services.tenant_access import event_belongs_to_tenant
from services.presence_service import mark_offline, update_presence

router = APIRouter()


def _resolve_user(token: str | None) -> dict | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            return None
        return get_user_by_id(int(payload.get('sub') or 0))
    except Exception:
        return None


@router.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket, token: str | None = Query(default=None), tenant_id: int | None = Query(default=None), event_id: int | None = Query(default=None), page: str | None = Query(default=None)):
    user = _resolve_user(token)
    if not user:
        await websocket.close(code=4401, reason="Token ausente ou inválido")
        return
    resolved_tenant = int(user.get('tenant_id') or 0)
    user_id = int(user.get('id') or 0) or None
    if not resolved_tenant or not user_id:
        await websocket.close(code=4403, reason="Usuário sem tenant válido")
        return
    if tenant_id is not None and int(tenant_id) != resolved_tenant:
        await websocket.close(code=4403, reason="Tenant não autorizado")
        return
    if event_id is not None and not event_belongs_to_tenant(event_id, resolved_tenant):
        await websocket.close(code=4403, reason="Evento não autorizado")
        return
    await realtime_manager.connect(websocket, tenant_id=resolved_tenant, user_id=user_id, event_id=event_id)
    if user_id:
        update_presence(user_id=user_id, tenant_id=resolved_tenant, current_page=page or 'websocket')
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30)
            except asyncio.TimeoutError:
                await websocket.send_json({'type': 'ping', 'created_at': datetime.now(timezone.utc).isoformat()})
                continue
            if data.get('type') in {'pong', 'heartbeat'} and user_id:
                update_presence(user_id=user_id, tenant_id=resolved_tenant, current_page=data.get('page') or page or 'websocket')
            if data.get('type') == 'ping':
                await websocket.send_json({'type': 'pong', 'created_at': datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect:
        pass
    finally:
        await realtime_manager.disconnect(websocket)
        if user_id:
            mark_offline(user_id=user_id, tenant_id=resolved_tenant)
