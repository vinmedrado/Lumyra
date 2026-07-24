from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

from core.settings import get_settings

try:  # SQLAlchemy é usado em produção; fallback mantém testes locais sem dependência instalada.
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session, sessionmaker
except Exception:  # pragma: no cover
    create_engine = None  # type: ignore
    text = None  # type: ignore
    Engine = object  # type: ignore
    Session = object  # type: ignore
    sessionmaker = None  # type: ignore


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    if create_engine is None:
        raise RuntimeError("SQLAlchemy não está instalado. Rode `pip install -r requirements.txt`.")
    settings = get_settings()
    url = settings.DATABASE_URL
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, future=True, connect_args=connect_args)


def _session_factory():
    if sessionmaker is None:
        raise RuntimeError("SQLAlchemy não está instalado. Rode `pip install -r requirements.txt`.")
    return sessionmaker(bind=get_engine(), autocommit=False, autoflush=False, future=True)


class _SessionLocalProxy:
    def __call__(self):
        return _session_factory()()


SessionLocal = _SessionLocalProxy()


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all() -> None:
    from db.models import Base

    Base.metadata.create_all(bind=get_engine())


def ping_database() -> bool:
    try:
        if create_engine is None:
            from repositories.database import connect
            with connect() as conn:
                conn.execute("SELECT 1").fetchone()
            return True
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
