from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import AnalyticsSnapshot, AutomationRule, AutomationRun, BackgroundJob, Event, Guest, MessageLog, Tenant, User, UserSession
from repositories.base import Page, paginate, tenant_filter


def list_guests(session: Session, tenant_id: int, event_id: int | None = None, search: str | None = None, page: int = 1, page_size: int = 50) -> Page:
    stmt = select(Guest).where(tenant_filter(Guest, tenant_id)).order_by(Guest.id.desc())
    if event_id:
        stmt = stmt.where(Guest.event_id == int(event_id))
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(Guest.name.ilike(like))
    return paginate(session, stmt, page=page, page_size=page_size)


def list_message_logs(session: Session, tenant_id: int, event_id: int | None = None, status: str | None = None, page: int = 1, page_size: int = 50) -> Page:
    stmt = select(MessageLog).where(tenant_filter(MessageLog, tenant_id)).order_by(MessageLog.created_at.desc())
    if event_id:
        stmt = stmt.where(MessageLog.event_id == int(event_id))
    if status:
        stmt = stmt.where(MessageLog.status == status)
    return paginate(session, stmt, page=page, page_size=page_size)
