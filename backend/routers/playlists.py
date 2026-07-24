from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.middleware.auth import current_tenant, require_roles
from backend.schemas.playlists import PlaylistUpsert
from services.playlist_service import get_event_playlist, upsert_event_playlist

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.get("/{event_id}")
def read_playlist(event_id: int, tenant_id: int = Depends(current_tenant)):
    item = get_event_playlist(tenant_id=tenant_id, event_id=event_id)
    return {"ok": True, "data": item}


@router.put("", dependencies=[Depends(require_roles("ADMIN"))])
def save_playlist(payload: PlaylistUpsert, tenant_id: int = Depends(current_tenant)):
    try:
        item = upsert_event_playlist(
            tenant_id=tenant_id,
            event_id=payload.event_id,
            playlist_url=payload.playlist_url,
            title=payload.title,
            description=payload.description,
            etiquette_message=payload.etiquette_message,
            is_active=payload.is_active,
        )
        return {"ok": True, "data": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
