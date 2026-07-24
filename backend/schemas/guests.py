from __future__ import annotations
from pydantic import BaseModel, Field
class GuestCreate(BaseModel):
    event_id: int
    name: str = Field(min_length=1, max_length=160)
    phone: str | None = None
    group_name: str | None = None
    invitation_type: str | None = None
    invitation_label: str | None = None
    category: str | None = None
    final_table: str | None = None
class GuestUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    group_name: str | None = None
    invitation_type: str | None = None
    invitation_label: str | None = None
    category: str | None = None
    final_table: str | None = None
class GuestOut(GuestCreate):
    id: int
