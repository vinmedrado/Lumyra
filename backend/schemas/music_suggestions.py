from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MusicSuggestionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    guest_token: str = Field(min_length=20, max_length=180)
    guest_name: str | None = Field(default=None, max_length=180)
    song_name: str = Field(min_length=1, max_length=180)
    artist_name: str = Field(min_length=1, max_length=180)
    message: str | None = Field(default=None, max_length=600)


class MusicSuggestionStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=40)
