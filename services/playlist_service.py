from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse

from db.models import EventPlaylist
from db.session import get_session

DEFAULT_TITLE = "Playlist do casamento"
DEFAULT_DESCRIPTION = "Quem faz a festa é você: salve a playlist do casamento e compartilhe suas melhores músicas para esse momento ficar ainda mais inesquecível."
DEFAULT_ETIQUETTE = "Pedimos apenas bom senso e carinho: escolha músicas que combinem com o clima do casamento e respeitem todos os convidados."


def validate_spotify_url(url: str) -> str:
    cleaned = (url or "").strip()
    if not cleaned:
        raise ValueError("Informe o link da playlist do Spotify.")
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("O link da playlist precisa começar com http:// ou https://.")
    host = parsed.netloc.lower()
    if "spotify.com" not in host:
        raise ValueError("Use um link válido do Spotify.")
    return cleaned


def _to_dict(row: EventPlaylist) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "event_id": row.event_id,
        "provider": row.provider,
        "playlist_url": row.playlist_url,
        "title": row.title,
        "description": row.description,
        "etiquette_message": row.etiquette_message,
        "is_active": bool(row.is_active),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def get_event_playlist(tenant_id: int, event_id: int) -> dict | None:
    with get_session() as session:
        row = session.query(EventPlaylist).filter(
            EventPlaylist.tenant_id == int(tenant_id),
            EventPlaylist.event_id == int(event_id),
        ).one_or_none()
        return _to_dict(row) if row else None


def upsert_event_playlist(tenant_id: int, event_id: int, playlist_url: str, title: str | None = None, description: str | None = None, etiquette_message: str | None = None, is_active: bool = True) -> dict:
    safe_url = validate_spotify_url(playlist_url)
    with get_session() as session:
        row = session.query(EventPlaylist).filter(
            EventPlaylist.tenant_id == int(tenant_id),
            EventPlaylist.event_id == int(event_id),
        ).one_or_none()
        if not row:
            row = EventPlaylist(tenant_id=int(tenant_id), event_id=int(event_id), playlist_url=safe_url)
            session.add(row)
        row.playlist_url = safe_url
        row.provider = "spotify"
        row.title = (title or DEFAULT_TITLE).strip()
        row.description = (description or DEFAULT_DESCRIPTION).strip()
        row.etiquette_message = (etiquette_message or DEFAULT_ETIQUETTE).strip()
        row.is_active = bool(is_active)
        row.updated_at = datetime.utcnow()
        session.flush()
        return _to_dict(row)
