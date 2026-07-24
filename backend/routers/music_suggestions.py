from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.middleware.auth import current_tenant, require_roles
from backend.schemas.music_suggestions import MusicSuggestionCreate, MusicSuggestionStatusUpdate
from services.guest_portal_service import get_guest_portal_context
from services.music_suggestion_service import (
    create_music_suggestion,
    list_music_suggestions,
    update_music_suggestion_status,
)

router = APIRouter(prefix="/music-suggestions", tags=["music-suggestions"])


@router.post("/public")
def create_public_music_suggestion(payload: MusicSuggestionCreate):
    """Endpoint público para o portal do convidado enviar sugestões musicais."""
    try:
        context = get_guest_portal_context(payload.guest_token)
        if not context.get("ok"):
            raise HTTPException(status_code=403, detail=context.get("error") or "Convite inválido")
        link = context["link"]
        item = create_music_suggestion(
            tenant_id=int(link.get("tenant_id") or 1),
            event_id=int(link["event_id"]),
            guest_id=int(link["guest_id"]),
            guest_name=payload.guest_name or link.get("guest_name"),
            song_name=payload.song_name,
            artist_name=payload.artist_name,
            message=payload.message,
            source="guest_portal",
        )
        return {"ok": True, "data": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", dependencies=[Depends(require_roles("ADMIN", "CLIENT"))])
def read_music_suggestions(
    event_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    tenant_id: int = Depends(current_tenant),
):
    return {"ok": True, "data": list_music_suggestions(tenant_id=tenant_id, event_id=event_id, status=status, limit=limit)}


@router.patch("/{suggestion_id}/status", dependencies=[Depends(require_roles("ADMIN", "CLIENT"))])
def change_music_suggestion_status(
    suggestion_id: int,
    payload: MusicSuggestionStatusUpdate,
    tenant_id: int = Depends(current_tenant),
):
    try:
        item = update_music_suggestion_status(tenant_id=tenant_id, suggestion_id=suggestion_id, status=payload.status)
        return {"ok": True, "data": item}
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
