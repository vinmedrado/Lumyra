from __future__ import annotations

from repositories.database import connect, init_db


def event_belongs_to_tenant(event_id: int, tenant_id: int) -> bool:
    """Return whether an event belongs to the authenticated tenant."""
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM events WHERE id=? AND COALESCE(tenant_id, 1)=?",
            (int(event_id), int(tenant_id)),
        ).fetchone()
    return row is not None


def vendor_belongs_to_event(vendor_id: int, event_id: int, tenant_id: int) -> bool:
    """Prevent linking an expense to a vendor from another tenant or event."""
    init_db()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM vendors
            WHERE id=? AND event_id=? AND COALESCE(tenant_id, 1)=?
            """,
            (int(vendor_id), int(event_id), int(tenant_id)),
        ).fetchone()
    return row is not None
