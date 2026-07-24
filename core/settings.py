from __future__ import annotations

from functools import lru_cache
from pathlib import Path

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception:  # pydantic v1 fallback
    from pydantic import BaseSettings  # type: ignore
    SettingsConfigDict = dict  # type: ignore


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "Lumyra"
    APP_VERSION: str = "0.5-backend-consolidation"
    DATABASE_URL: str = "sqlite:///data/event_erp.sqlite3"
    STORAGE_PATH: str = "storage"
    SECRET_KEY: str = "change-me-in-production"
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    WHATSAPP_PROVIDER: str = "demo"
    LOG_LEVEL: str = "INFO"
    DEMO_MODE: bool = True
    ADMIN_EMAIL: str = "admin@local"
    ADMIN_PASSWORD: str = "admin123"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    API_BASE_URL: str = "http://localhost:8000"
    SCHEDULER_LOCK_SECONDS: int = 60
    WORKER_ID: str = "event-erp-worker"
    DEFAULT_TENANT_NAME: str = "Assessoria Demo"
    DEFAULT_TENANT_SLUG: str = "assessoria-demo"

    try:
        model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    except Exception:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            extra = "ignore"

    @property
    def storage_root(self) -> Path:
        return Path(self.STORAGE_PATH)

    @property
    def is_postgres(self) -> bool:
        return self.DATABASE_URL.startswith(("postgresql://", "postgresql+psycopg2://"))

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
