from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field
class FormResponseCreate(BaseModel):
    guest_id: int
    responses: dict[int, Any]
class FormCreate(BaseModel):
    event_id: int
    title: str = Field(min_length=1, max_length=160)
