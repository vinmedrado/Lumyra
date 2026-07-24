from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.middleware.auth import current_tenant, require_roles
from backend.pagination import normalize_page, page_response
from backend.schemas.financial import ExpenseCreate, VendorCreate
from backend.services.tenant_access import event_belongs_to_tenant, vendor_belongs_to_event
from repositories.database import connect, init_db

router = APIRouter(tags=["financial"])


@router.get("/vendors")
def vendors(event_id: int, tenant_id: int = Depends(current_tenant)):
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM vendors WHERE event_id=? AND COALESCE(tenant_id,1)=? ORDER BY name", (event_id, tenant_id)).fetchall()
    return {"ok": True, "data": [dict(r) for r in rows]}


@router.post("/vendors", dependencies=[Depends(require_roles("ADMIN"))])
def create_vendor(payload: VendorCreate, tenant_id: int = Depends(current_tenant)):
    if not event_belongs_to_tenant(payload.event_id, tenant_id):
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    with connect() as conn:
        cur = conn.execute("INSERT INTO vendors(event_id, tenant_id, name, category, phone, notes) VALUES (?, ?, ?, ?, ?, ?)", (payload.event_id, tenant_id, payload.name, payload.category, payload.phone, payload.notes))
    return {"ok": True, "data": {"id": int(cur.lastrowid)}}


@router.get("/expenses")
def expenses(event_id: int | None = None, status: str | None = None, vendor_id: int | None = None, date_from: str | None = None, date_to: str | None = None, page: int = 1, page_size: int = 50, tenant_id: int = Depends(current_tenant)):
    init_db(); page, page_size = normalize_page(page, page_size)
    where = ["COALESCE(tenant_id,1)=?"]; params: list = [tenant_id]
    if event_id: where.append("event_id=?"); params.append(event_id)
    if status: where.append("status=?"); params.append(status)
    if vendor_id: where.append("vendor_id=?"); params.append(vendor_id)
    if date_from: where.append("date(due_date)>=date(?)"); params.append(date_from)
    if date_to: where.append("date(due_date)<=date(?)"); params.append(date_to)
    where_sql = " AND ".join(where)
    with connect() as conn:
        total = int(conn.execute(f"SELECT COUNT(*) c FROM expenses WHERE {where_sql}", tuple(params)).fetchone()["c"])
        rows = conn.execute(f"SELECT * FROM expenses WHERE {where_sql} ORDER BY due_date, id DESC LIMIT ? OFFSET ?", (*params, page_size, (page-1)*page_size)).fetchall()
    return page_response([dict(r) for r in rows], total, page, page_size)


@router.post("/expenses", dependencies=[Depends(require_roles("ADMIN"))])
def create_expense(payload: ExpenseCreate, tenant_id: int = Depends(current_tenant)):
    if not event_belongs_to_tenant(payload.event_id, tenant_id):
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    if payload.vendor_id is not None and not vendor_belongs_to_event(
        payload.vendor_id, payload.event_id, tenant_id
    ):
        raise HTTPException(status_code=400, detail="Fornecedor não pertence ao evento")
    with connect() as conn:
        cur = conn.execute("INSERT INTO expenses(event_id, tenant_id, vendor_id, description, amount, status, due_date) VALUES (?, ?, ?, ?, ?, ?, ?)", (payload.event_id, tenant_id, payload.vendor_id, payload.description, payload.amount, payload.status, payload.due_date))
    return {"ok": True, "data": {"id": int(cur.lastrowid)}}
