from __future__ import annotations

import io
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from backend.middleware.auth import current_tenant, require_roles
from backend.pagination import normalize_page, page_response
from backend.schemas.guests import GuestCreate, GuestUpdate
from backend.services.tenant_access import event_belongs_to_tenant
from repositories.database import connect, init_db
from services.import_service import import_guest_rows, preview_guest_file
from services.phone_utils import normalize_phone

router = APIRouter(prefix="/guests", tags=["guests"])


def _event_allowed(event_id: int, tenant_id: int) -> bool:
    return event_belongs_to_tenant(event_id, tenant_id)


@router.get("")
def list_guests(event_id: int, page: int = 1, page_size: int = 50, status: str | None = None, search: str | None = None, tenant_id: int = Depends(current_tenant)):
    init_db()
    page, page_size = normalize_page(page, page_size)
    if not _event_allowed(event_id, tenant_id):
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    where = ["g.event_id=?", "COALESCE(g.tenant_id,1)=?"]
    params: list = [event_id, tenant_id]
    if search:
        where.append("(lower(g.name) LIKE lower(?) OR lower(COALESCE(g.phone,'')) LIKE lower(?))")
        params.extend([f"%{search}%", f"%{search}%"])
    if status:
        where.append("g.id IN (SELECT guest_id FROM guest_rsvp WHERE status=?)")
        params.append(status)
    where_sql = " AND ".join(where)
    with connect() as conn:
        total = int(conn.execute(f"SELECT COUNT(*) c FROM guests g WHERE {where_sql}", tuple(params)).fetchone()["c"])
        rows = conn.execute(
            f"""
            SELECT g.*,
                   COALESCE(r.status, 'pending') AS rsvp_status,
                   COALESCE(g.final_table, g.corrected_table, g.current_table) AS table_name
            FROM guests g
            LEFT JOIN guest_rsvp r ON r.event_id=g.event_id AND r.guest_id=g.id
            WHERE {where_sql}
            ORDER BY g.id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, (page - 1) * page_size),
        ).fetchall()
    return page_response([dict(r) for r in rows], total, page, page_size)


@router.post("", dependencies=[Depends(require_roles("ADMIN"))])
def create_guest(payload: GuestCreate, tenant_id: int = Depends(current_tenant)):
    if not _event_allowed(payload.event_id, tenant_id):
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO guests(event_id, tenant_id, name, phone, group_name, invitation_type, invitation_label, category, final_table) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (payload.event_id, tenant_id, payload.name.strip(), normalize_phone(payload.phone or ""), payload.group_name, payload.invitation_type or ("family" if payload.group_name else "individual"), payload.invitation_label or payload.group_name or payload.name.strip(), payload.category, payload.final_table),
        )
    return {"ok": True, "data": {"id": int(cur.lastrowid)}}


@router.put("/{guest_id}", dependencies=[Depends(require_roles("ADMIN", "STAFF"))])
def update_guest(guest_id: int, payload: GuestUpdate, tenant_id: int = Depends(current_tenant)):
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return {"ok": True}
    allowed = {"name", "phone", "group_name", "invitation_type", "invitation_label", "category", "final_table"}
    fields = [k for k in data if k in allowed]
    values = [normalize_phone(data[k]) if k == "phone" and data[k] else data[k] for k in fields]
    with connect() as conn:
        row = conn.execute("SELECT event_id FROM guests WHERE id=? AND COALESCE(tenant_id,1)=?", (guest_id, tenant_id)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Convidado não encontrado")
        conn.execute(f"UPDATE guests SET {', '.join(f + '=?' for f in fields)}, updated_at=CURRENT_TIMESTAMP WHERE id=?", (*values, guest_id))
    return {"ok": True}


@router.post("/import", dependencies=[Depends(require_roles("ADMIN"))])
def import_guests(event_id: int, file: UploadFile = File(...), preview: bool = True, tenant_id: int = Depends(current_tenant)):
    if not _event_allowed(event_id, tenant_id):
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    raw = file.file.read()
    rows, report = preview_guest_file(raw, file.filename or "upload")
    if preview:
        return {"ok": True, "data": {"preview": rows[:20], "report": report}}
    result = import_guest_rows(event_id, tenant_id, rows)
    return {"ok": True, "data": result}


@router.get("/export")
def export_guests(event_id: int, tenant_id: int = Depends(current_tenant)):
    if not _event_allowed(event_id, tenant_id):
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    with connect() as conn:
        rows = [dict(r) for r in conn.execute("SELECT name, phone, group_name, invitation_type, invitation_label, category, final_table FROM guests WHERE event_id=?", (event_id,)).fetchall()]
    df = pd.DataFrame(rows)
    buf = io.StringIO(); df.to_csv(buf, index=False)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=convidados.csv"})
