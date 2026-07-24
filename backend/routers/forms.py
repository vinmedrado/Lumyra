from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from backend.middleware.auth import current_tenant, require_roles
from backend.schemas.forms import FormCreate, FormResponseCreate
from repositories.database import connect, init_db
from services.form_service import save_response

router=APIRouter(prefix='/forms', tags=['forms'])

@router.get('')
def list_forms(event_id:int, tenant_id:int=Depends(current_tenant)):
    init_db()
    with connect() as conn:
        rows=conn.execute('SELECT * FROM event_forms WHERE event_id=? AND COALESCE(tenant_id,1)=? ORDER BY id DESC', (event_id, tenant_id)).fetchall()
    return {'ok': True, 'data':[dict(r) for r in rows]}

@router.post('', dependencies=[Depends(require_roles('ADMIN'))])
def create_form(payload:FormCreate, tenant_id:int=Depends(current_tenant)):
    with connect() as conn:
        ev=conn.execute('SELECT 1 FROM events WHERE id=? AND COALESCE(tenant_id,1)=?', (payload.event_id, tenant_id)).fetchone()
        if not ev: raise HTTPException(status_code=404, detail='Evento não encontrado')
        cur=conn.execute('INSERT INTO event_forms(event_id, tenant_id, title, is_active, active) VALUES (?, ?, ?, 1, 1)', (payload.event_id, tenant_id, payload.title))
    return {'ok': True, 'data': {'id': int(cur.lastrowid)}}

@router.post('/responses')
def submit_response(payload:FormResponseCreate, tenant_id:int=Depends(current_tenant)):
    with connect() as conn:
        guest=conn.execute('SELECT id FROM guests WHERE id=? AND COALESCE(tenant_id,1)=?', (payload.guest_id, tenant_id)).fetchone()
        if not guest: raise HTTPException(status_code=404, detail='Convidado não encontrado')
    for field_id, value in payload.responses.items():
        save_response(payload.guest_id, int(field_id), str(value))
    return {'ok': True}
