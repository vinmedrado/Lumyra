from __future__ import annotations
from pydantic import BaseModel, Field
class CampaignCreate(BaseModel):
    event_id: int
    name: str = Field(min_length=1, max_length=160)
    template: str = Field(min_length=1)
    dry_run: bool = True
