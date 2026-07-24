from __future__ import annotations
from pydantic import BaseModel, Field
class VendorCreate(BaseModel):
    event_id: int
    name: str = Field(min_length=1, max_length=160)
    category: str | None = None
    phone: str | None = None
    notes: str | None = None
class ExpenseCreate(BaseModel):
    event_id: int
    vendor_id: int | None = None
    description: str | None = None
    amount: float = Field(ge=0)
    status: str = 'pending'
    due_date: str | None = None
