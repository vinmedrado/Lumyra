from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from repositories.database import connect, init_db, create_event, get_event, update_event
from backend.middleware.auth import current_tenant, require_roles
from backend.schemas.events import EventCreate, EventUpdate

router = APIRouter(prefix='/events', tags=['events'])

@router.get('')
def list_events(tenant_id: int = Depends(current_tenant)):
    init_db()
    with connect() as conn:
        rows = conn.execute('SELECT * FROM events WHERE COALESCE(tenant_id,1)=? ORDER BY id DESC', (tenant_id,)).fetchall()
    return {'ok': True, 'data': [dict(r) for r in rows]}

@router.post('', dependencies=[Depends(require_roles('ADMIN'))])
def create(payload: EventCreate, tenant_id: int = Depends(current_tenant)):
    event_id = create_event(payload.name, payload.date, payload.location)
    with connect() as conn:
        conn.execute('UPDATE events SET tenant_id=? WHERE id=?', (tenant_id, event_id))
    return {'ok': True, 'data': {'id': event_id}}

@router.get('/{event_id}')
def read(event_id: int, tenant_id: int = Depends(current_tenant)):
    event = get_event(event_id)
    if not event or int(event.get('tenant_id') or tenant_id) != tenant_id:
        raise HTTPException(status_code=404, detail='Evento não encontrado')
    return {'ok': True, 'data': event}

@router.put('/{event_id}', dependencies=[Depends(require_roles('ADMIN'))])
def update(event_id: int, payload: EventUpdate, tenant_id: int = Depends(current_tenant)):
    with connect() as conn:
        row = conn.execute('SELECT id FROM events WHERE id=? AND COALESCE(tenant_id,1)=?', (event_id, tenant_id)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Evento não encontrado')
    update_event(event_id, payload.name, payload.date, payload.location)
    return {'ok': True}
