from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.middleware.auth import current_user
from backend.schemas.auth import LoginRequest, TokenResponse, UserOut
from backend.services.auth_jwt import authenticate, create_access_token, create_refresh_token, revoke_refresh_token, rotate_refresh_token
from services.audit_service import log_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request):
    user = authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")
    try:
        log_audit("api_login", "user", int(user["id"]), tenant_id=int(user.get("tenant_id") or 1), user_id=int(user["id"]))
    except Exception:
        pass
    access = create_access_token(user)
    refresh = create_refresh_token(user, user_agent=request.headers.get("user-agent"), ip_address=request.client.host if request.client else None)
    return TokenResponse(access_token=access, refresh_token=refresh, expires_in=3600)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: dict, request: Request):
    token = payload.get("refresh_token") if isinstance(payload, dict) else None
    if not token:
        raise HTTPException(status_code=400, detail="refresh_token obrigatório")
    try:
        access, refresh_token = rotate_refresh_token(token, user_agent=request.headers.get("user-agent"), ip_address=request.client.host if request.client else None)
        return TokenResponse(access_token=access, refresh_token=refresh_token, expires_in=3600)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Refresh token inválido") from exc


@router.post("/logout")
def logout(payload: dict | None = None, user: dict = Depends(current_user)):
    refresh_token = (payload or {}).get("refresh_token") if isinstance(payload, dict) else None
    if refresh_token:
        revoke_refresh_token(refresh_token)
    return {"ok": True, "message": "Logout registrado"}


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(current_user)):
    return UserOut(id=int(user["id"]), tenant_id=user.get("tenant_id"), name=user.get("name") or "Usuário", email=user.get("email"), role=user.get("role") or "ADMIN")
