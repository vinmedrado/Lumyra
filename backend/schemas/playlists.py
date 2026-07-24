from __future__ import annotations

from pydantic import BaseModel, Field


class PlaylistUpsert(BaseModel):
    event_id: int
    playlist_url: str = Field(min_length=8)
    title: str | None = None
    description: str | None = None
    etiquette_message: str | None = None
    is_active: bool = True
