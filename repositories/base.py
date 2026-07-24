from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


@dataclass
class Page:
    items: list[Any]
    page: int
    page_size: int
    total: int


def tenant_filter(model, tenant_id: int):
    return getattr(model, "tenant_id") == int(tenant_id)


def paginate(session: Session, stmt: Select, *, page: int = 1, page_size: int = 50) -> Page:
    page = max(1, int(page or 1))
    page_size = min(500, max(1, int(page_size or 50)))
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = int(session.execute(total_stmt).scalar() or 0)
    rows = session.execute(stmt.limit(page_size).offset((page - 1) * page_size)).scalars().all()
    return Page(items=list(rows), page=page, page_size=page_size, total=total)


def safe_commit(session: Session) -> None:
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
