from __future__ import annotations
from pydantic import BaseModel
class LoginRequest(BaseModel):
    email: str
    password: str
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
    expires_in: int
class UserOut(BaseModel):
    id: int
    tenant_id: int | None = None
    name: str
    email: str | None = None
    role: str
