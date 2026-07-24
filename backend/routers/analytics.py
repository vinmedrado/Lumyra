from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.middleware.auth import current_tenant
from backend.services.tenant_access import event_belongs_to_tenant
from services.analytics_service import event_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
def overview(event_id: int, tenant_id: int = Depends(current_tenant)):
    if not event_belongs_to_tenant(event_id, tenant_id):
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return {"ok": True, "data": event_analytics(event_id)}
