from __future__ import annotations

try:
    from sqlalchemy.orm import DeclarativeBase
except Exception:  # fallback para ambientes antes do pip install
    class DeclarativeBase:  # type: ignore
        class metadata:
            @staticmethod
            def create_all(bind=None):
                return None


class Base(DeclarativeBase):
    """Base declarativa única para modelos SQLAlchemy do SaaS."""

    pass
