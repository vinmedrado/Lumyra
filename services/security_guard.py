from __future__ import annotations

from core.settings import get_settings


def assert_secure_settings() -> None:
    settings = get_settings()
    if settings.APP_ENV.lower() == "production" and settings.SECRET_KEY in {"", "change-me-in-production", "dev-secret"}:
        raise RuntimeError("SECRET_KEY segura é obrigatória em produção.")
