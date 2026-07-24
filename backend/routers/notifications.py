from __future__ import annotations

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.middleware.auth import get_current_user
from backend.realtime.manager import realtime_manager
from services.notification_service import create_notification, list_notifications, mark_all_read, mark_read, unread_count
from services.activity_service import list_activity, record_activity
from services.presence_service import acquire_lock, list_online_users, update_presence

router = APIRouter(prefix='/notifications', tags=['notifications'])

class NotificationCreate(BaseModel):
    title: str
    message: str
    severity: str = 'info'
    user_id: int | None = None
    related_entity_type: str | None = None
    related_entity_id: int | None = None

@router.get('')
def notifications(unread_only: bool = False, severity: str | None = None, current_user: dict = Depends(get_current_user)):
    tenant_id = int(current_user.get('tenant_id') or 1)
    user_id = int(current_user.get('id') or 0) or None
    items = list_notifications(tenant_id=tenant_id, user_id=user_id, unread_only=unread_only, severity=severity)
    return {'items': items, 'unread_count': unread_count(tenant_id=tenant_id, user_id=user_id)}

@router.post('')
async def create(payload: NotificationCreate, current_user: dict = Depends(get_current_user)):
    tenant_id = int(current_user.get('tenant_id') or 1)
    item = create_notification(tenant_id=tenant_id, user_id=payload.user_id, title=payload.title, message=payload.message, severity=payload.severity, related_entity_type=payload.related_entity_type, related_entity_id=payload.related_entity_id)
    record_activity(tenant_id=tenant_id, user_id=int(current_user.get('id') or 0), action_type='notification_created', entity_type='notification', entity_id=item['id'], message=f"Notificação criada: {item['title']}")
    await realtime_manager.broadcast_tenant(tenant_id, {'type': 'notification_created', 'payload': item})
    return item

@router.post('/{notification_id}/read')
def read(notification_id: int, current_user: dict = Depends(get_current_user)):
    mark_read(notification_id, tenant_id=int(current_user.get('tenant_id') or 1))
    return {'ok': True}

@router.post('/read-all')
def read_all(current_user: dict = Depends(get_current_user)):
    total = mark_all_read(tenant_id=int(current_user.get('tenant_id') or 1), user_id=int(current_user.get('id') or 0) or None)
    return {'ok': True, 'updated': total}

@router.get('/activity')
def activity(current_user: dict = Depends(get_current_user)):
    return {'items': list_activity(tenant_id=int(current_user.get('tenant_id') or 1))}

@router.get('/presence')
def presence(current_user: dict = Depends(get_current_user)):
    tenant_id = int(current_user.get('tenant_id') or 1)
    update_presence(user_id=int(current_user.get('id') or 0), tenant_id=tenant_id, current_page='api')
    return {'items': list_online_users(tenant_id=tenant_id)}

class LockRequest(BaseModel):
    entity_type: str
    entity_id: int

@router.post('/locks')
def lock_entity(payload: LockRequest, current_user: dict = Depends(get_current_user)):
    result = acquire_lock(tenant_id=int(current_user.get('tenant_id') or 1), user_id=int(current_user.get('id') or 0), entity_type=payload.entity_type, entity_id=payload.entity_id)
    if not result.get('locked'):
        raise HTTPException(status_code=409, detail=result)
    return result
