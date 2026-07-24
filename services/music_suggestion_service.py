from __future__ import annotations

from datetime import datetime
from typing import Iterable

from db.models import EventMusicSuggestion
from db.session import get_session

VALID_STATUSES = {"pending", "approved", "rejected", "added"}


def _clean(value: str | None, max_len: int | None = None) -> str:
    text = (value or "").strip()
    if max_len and len(text) > max_len:
        text = text[:max_len].strip()
    return text


def _to_dict(row: EventMusicSuggestion) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "event_id": row.event_id,
        "guest_id": row.guest_id,
        "guest_name": row.guest_name,
        "song_name": row.song_name,
        "artist_name": row.artist_name,
        "message": row.message,
        "status": row.status,
        "source": row.source,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def create_music_suggestion(
    tenant_id: int,
    event_id: int,
    song_name: str,
    artist_name: str,
    guest_name: str | None = None,
    message: str | None = None,
    guest_id: int | None = None,
    source: str = "guest_portal",
) -> dict:
    safe_song = _clean(song_name, 180)
    safe_artist = _clean(artist_name, 180)
    safe_guest = _clean(guest_name, 180) or "Convidado"
    safe_message = _clean(message, 600) or None

    if not safe_song:
        raise ValueError("Informe o nome da música.")
    if not safe_artist:
        raise ValueError("Informe o artista da música.")

    with get_session() as session:
        row = EventMusicSuggestion(
            tenant_id=int(tenant_id or 1),
            event_id=int(event_id or 1),
            guest_id=guest_id,
            guest_name=safe_guest,
            song_name=safe_song,
            artist_name=safe_artist,
            message=safe_message,
            status="pending",
            source=_clean(source, 60) or "guest_portal",
        )
        session.add(row)
        session.flush()
        return _to_dict(row)


def list_music_suggestions(tenant_id: int, event_id: int | None = None, status: str | None = None, limit: int = 100) -> list[dict]:
    with get_session() as session:
        query = session.query(EventMusicSuggestion).filter(EventMusicSuggestion.tenant_id == int(tenant_id or 1))
        if event_id is not None:
            query = query.filter(EventMusicSuggestion.event_id == int(event_id))
        if status:
            query = query.filter(EventMusicSuggestion.status == status)
        rows: Iterable[EventMusicSuggestion] = query.order_by(EventMusicSuggestion.created_at.desc()).limit(max(1, min(int(limit or 100), 500))).all()
        return [_to_dict(row) for row in rows]


def update_music_suggestion_status(tenant_id: int, suggestion_id: int, status: str) -> dict:
    safe_status = _clean(status, 40).lower()
    if safe_status not in VALID_STATUSES:
        raise ValueError("Status inválido para sugestão musical.")

    with get_session() as session:
        row = session.query(EventMusicSuggestion).filter(
            EventMusicSuggestion.tenant_id == int(tenant_id or 1),
            EventMusicSuggestion.id == int(suggestion_id),
        ).one_or_none()
        if not row:
            raise LookupError("Sugestão musical não encontrada.")
        row.status = safe_status
        row.updated_at = datetime.utcnow()
        session.flush()
        return _to_dict(row)
