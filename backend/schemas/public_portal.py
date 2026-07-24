from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InvitationMemberResponse(BaseModel):
    guest_id: int
    status: Literal["confirmed", "declined", "pending"]


class GuestPortalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    members: list[InvitationMemberResponse] = Field(min_length=1, max_length=20)
    phone: str | None = Field(default=None, max_length=40)
    needs_bus: bool = False
    bus_pickup_point: str | None = Field(default=None, max_length=255)
    dietary_restrictions: str | None = Field(default=None, max_length=600)
    notes: str | None = Field(default=None, max_length=1000)
