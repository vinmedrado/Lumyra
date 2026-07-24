from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.schemas.public_portal import GuestPortalResponse
from core.settings import get_settings
from services.guest_portal_service import (
    DEMO_GUEST_TOKEN,
    ensure_demo_guest_portal,
    get_guest_portal_api_context,
    submit_invitation_response,
)
from services.playlist_service import get_event_playlist

router = APIRouter(prefix="/public/guest", tags=["public-guest-portal"])


def _prepare_demo_token(token: str) -> None:
    if token == DEMO_GUEST_TOKEN and get_settings().DEMO_MODE:
        ensure_demo_guest_portal()


@router.get("/{token}")
def read_guest_portal(token: str):
    _prepare_demo_token(token)
    context = get_guest_portal_api_context(token)
    if not context.get("ok"):
        raise HTTPException(status_code=404, detail=context.get("error") or "Convite não encontrado")

    invitation = context["invitation"]
    playlist = get_event_playlist(
        tenant_id=int(invitation["tenant_id"]),
        event_id=int(invitation["event_id"]),
    )
    return {"ok": True, "data": {**context, "playlist": playlist}}


@router.post("/{token}/rsvp")
def save_guest_portal_response(token: str, payload: GuestPortalResponse):
    _prepare_demo_token(token)
    result = submit_invitation_response(token, payload.model_dump())
    if not result.get("ok"):
        status_code = 403 if "expir" in str(result.get("error", "")).lower() else 400
        raise HTTPException(status_code=status_code, detail=result.get("error") or "Não foi possível salvar")
    return {"ok": True, "data": result}
