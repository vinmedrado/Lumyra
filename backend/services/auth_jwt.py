from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from core.settings import get_settings
from repositories.database import connect, init_db
from services.security_guard import assert_secure_settings
from services.security_service import verify_password

settings = get_settings()
ALGORITHM = "HS256"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user: dict[str, Any]) -> str:
    assert_secure_settings()
    exp = _utcnow() + timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES or 15))
    payload = {
        "sub": str(user["id"]),
        "tenant_id": user.get("tenant_id"),
        "role": user.get("role"),
        "type": "access",
        "exp": exp,
        "iat": _utcnow(),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user: dict[str, Any], user_agent: str | None = None, ip_address: str | None = None) -> str:
    assert_secure_settings()
    init_db()
    token = secrets.token_urlsafe(64)
    expires = (_utcnow() + timedelta(days=int(settings.REFRESH_TOKEN_EXPIRE_DAYS or 14))).isoformat()
    with connect() as conn:
        conn.execute(
            "INSERT INTO user_sessions(user_id, refresh_token_hash, expires_at, user_agent, ip_address) VALUES (?, ?, ?, ?, ?)",
            (int(user["id"]), _hash_token(token), expires, user_agent, ip_address),
        )
    return token


def authenticate(email: str, password: str) -> dict[str, Any] | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE lower(email)=lower(?) AND COALESCE(is_active, active, 1)=1 LIMIT 1",
            ((email or "").strip(),),
        ).fetchone()
    if not row or not verify_password(password or "", row["password_hash"] or ""):
        return None
    return dict(row)


def decode_access_token(token: str) -> dict[str, Any]:
    assert_secure_settings()
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id=? AND COALESCE(is_active, active, 1)=1",
            (int(user_id),),
        ).fetchone()
    return dict(row) if row else None


def rotate_refresh_token(refresh_token: str, user_agent: str | None = None, ip_address: str | None = None) -> tuple[str, str]:
    init_db()
    token_hash = _hash_token(refresh_token or "")
    now = _utcnow().isoformat()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT us.*, u.id AS uid, u.tenant_id, u.name, u.email, u.role, u.is_active
            FROM user_sessions us
            JOIN users u ON u.id = us.user_id
            WHERE us.refresh_token_hash=? AND us.revoked_at IS NULL AND us.expires_at > ? AND COALESCE(u.is_active, u.active, 1)=1
            """,
            (token_hash, now),
        ).fetchone()
        if not row:
            raise ValueError("Refresh token inválido ou expirado")
        conn.execute("UPDATE user_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE id=?", (row["id"],))
        user = {"id": row["uid"], "tenant_id": row["tenant_id"], "name": row["name"], "email": row["email"], "role": row["role"]}
    return create_access_token(user), create_refresh_token(user, user_agent=user_agent, ip_address=ip_address)


def revoke_refresh_token(token: str) -> None:
    init_db()
    with connect() as conn:
        conn.execute("UPDATE user_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE refresh_token_hash=?", (_hash_token(token or ""),))
