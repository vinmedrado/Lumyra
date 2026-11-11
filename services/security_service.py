from __future__ import annotations

try:
    from passlib.context import CryptContext
except Exception:  # fallback para ambientes sem passlib instalado ainda
    CryptContext = None  # type: ignore

import hashlib
import hmac

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") if CryptContext else None


def hash_password(password: str) -> str:
    password = password or ""
    if _pwd_context is None:
        # Never silently create new unsalted hashes if bcrypt is unavailable.
        raise RuntimeError("Secure password hashing is unavailable; install passlib[bcrypt].")
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    if _pwd_context and not password_hash.startswith("sha256$"):
        try:
            return bool(_pwd_context.verify(password or "", password_hash))
        except Exception:
            return False
    expected = "sha256$" + hashlib.sha256((password or "").encode("utf-8")).hexdigest()
    return hmac.compare_digest(expected, password_hash)
