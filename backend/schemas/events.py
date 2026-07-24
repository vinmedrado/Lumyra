from __future__ import annotations
from pydantic import BaseModel, Field
class EventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    date: str = ''
    location: str = ''
class EventUpdate(EventCreate):
    pass
class EventOut(EventCreate):
    id: int
    tenant_id: int | None = None
