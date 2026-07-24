from __future__ import annotations
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from backend.services.auth_jwt import decode_access_token, get_user_by_id

bearer = HTTPBearer(auto_error=False)

async def current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token ausente')
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get('type') != 'access':
            raise ValueError('invalid token type')
        user = get_user_by_id(int(payload['sub']))
        if not user:
            raise ValueError('user not found')
        request.state.user = user
        request.state.tenant_id = int(user.get('tenant_id') or 1)
        return user
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token inválido ou expirado') from exc

async def current_tenant(user: dict = Depends(current_user)) -> int:
    return int(user.get('tenant_id') or 1)

def require_roles(*roles: str):
    allowed = {r.upper() for r in roles}
    async def dep(user: dict = Depends(current_user)) -> dict:
        if str(user.get('role','')).upper() not in allowed:
            raise HTTPException(status_code=403, detail='Perfil sem permissão')
        return user
    return dep

# Alias estável para routers novos.
get_current_user = current_user
get_current_tenant = current_tenant
