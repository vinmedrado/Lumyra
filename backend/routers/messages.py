from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.middleware.auth import current_tenant, require_roles
from backend.pagination import normalize_page, page_response
from backend.schemas.campaigns import CampaignCreate
from backend.services.tenant_access import event_belongs_to_tenant
from repositories.database import connect, init_db

router = APIRouter(tags=["messages"])


@router.get("/campaigns")
def list_campaigns(event_id: int, tenant_id: int = Depends(current_tenant)):
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM whatsapp_campaigns WHERE event_id=? AND COALESCE(tenant_id,1)=? ORDER BY id DESC", (event_id, tenant_id)).fetchall()
    return {"ok": True, "data": [dict(r) for r in rows]}


@router.post("/campaigns", dependencies=[Depends(require_roles("ADMIN"))])
def create_campaign(payload: CampaignCreate, tenant_id: int = Depends(current_tenant)):
    if not event_belongs_to_tenant(payload.event_id, tenant_id):
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    with connect() as conn:
        cur = conn.execute("INSERT INTO whatsapp_campaigns(event_id, tenant_id, name, template, status) VALUES (?, ?, ?, ?, ?)", (payload.event_id, tenant_id, payload.name, payload.template, "draft" if payload.dry_run else "queued"))
    return {"ok": True, "data": {"id": int(cur.lastrowid)}}


@router.get("/messages/logs")
def message_logs(event_id: int | None = None, guest_id: int | None = None, status: str | None = None, date_from: str | None = None, date_to: str | None = None, page: int = 1, page_size: int = 50, tenant_id: int = Depends(current_tenant)):
    init_db(); page, page_size = normalize_page(page, page_size)
    where = ["COALESCE(tenant_id,1)=?"]; params: list = [tenant_id]
    if event_id: where.append("event_id=?"); params.append(event_id)
    if guest_id: where.append("guest_id=?"); params.append(guest_id)
    if status: where.append("status=?"); params.append(status)
    if date_from: where.append("date(created_at)>=date(?)"); params.append(date_from)
    if date_to: where.append("date(created_at)<=date(?)"); params.append(date_to)
    where_sql = " AND ".join(where)
    with connect() as conn:
        total = int(conn.execute(f"SELECT COUNT(*) c FROM message_logs WHERE {where_sql}", tuple(params)).fetchone()["c"])
        rows = conn.execute(f"SELECT * FROM message_logs WHERE {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?", (*params, page_size, (page-1)*page_size)).fetchall()
    return page_response([dict(r) for r in rows], total, page, page_size)
