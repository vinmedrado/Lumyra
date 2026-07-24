from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.middleware.auth import current_tenant, require_roles
from backend.pagination import normalize_page, page_response
from backend.services.tenant_access import event_belongs_to_tenant
from repositories.database import connect, init_db
from services.storage_service import save_file

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(event_id: int | None = None, category: str | None = None, search: str | None = None, page: int = 1, page_size: int = 50, tenant_id: int = Depends(current_tenant)):
    init_db(); page, page_size = normalize_page(page, page_size)
    where = ["COALESCE(tenant_id,1)=?", "COALESCE(is_deleted,0)=0"]; params: list = [tenant_id]
    if event_id: where.append("event_id=?"); params.append(event_id)
    if category: where.append("category=?"); params.append(category)
    if search: where.append("lower(name) LIKE lower(?)"); params.append(f"%{search}%")
    where_sql = " AND ".join(where)
    with connect() as conn:
        total = int(conn.execute(f"SELECT COUNT(*) c FROM event_documents WHERE {where_sql}", tuple(params)).fetchone()["c"])
        rows = conn.execute(f"SELECT * FROM event_documents WHERE {where_sql} ORDER BY uploaded_at DESC LIMIT ? OFFSET ?", (*params, page_size, (page-1)*page_size)).fetchall()
    return page_response([dict(r) for r in rows], total, page, page_size)


@router.post("", dependencies=[Depends(require_roles("ADMIN"))])
def upload_document(event_id: int, name: str, category: str = "outro", description: str = "", file: UploadFile = File(...), tenant_id: int = Depends(current_tenant)):
    if not event_belongs_to_tenant(event_id, tenant_id):
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    stored = save_file(file.file, file.filename or "arquivo", tenant_id=tenant_id, folder=f"events/{event_id}/documents")
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO event_documents(event_id, tenant_id, name, file_path, original_filename, stored_filename, category, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (event_id, tenant_id, name, stored["file_path"], file.filename, stored["stored_filename"], category, description),
        )
    return {"ok": True, "data": {"id": int(cur.lastrowid), **stored}}
