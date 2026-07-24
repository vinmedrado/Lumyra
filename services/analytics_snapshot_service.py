from __future__ import annotations

from datetime import date

from repositories.database import connect, init_db


def _scalar(conn, sql: str, params: tuple = ()) -> float:
    row = conn.execute(sql, params).fetchone()
    if not row:
        return 0
    return float(row[0] or 0)


def generate_analytics_snapshot(tenant_id: int, event_id: int, snapshot_date: str | None = None) -> dict:
    init_db()
    snapshot_date = snapshot_date or date.today().isoformat()
    with connect() as conn:
        total_guests = int(_scalar(conn, "SELECT COUNT(*) FROM guests WHERE event_id=? AND COALESCE(tenant_id,?)=?", (event_id, tenant_id, tenant_id)))
        confirmed = int(_scalar(conn, "SELECT COUNT(*) FROM guest_rsvp WHERE event_id=? AND status='confirmed'", (event_id,)))
        declined = int(_scalar(conn, "SELECT COUNT(*) FROM guest_rsvp WHERE event_id=? AND status='declined'", (event_id,)))
        pending = max(0, total_guests - confirmed - declined)
        messages_sent = int(_scalar(conn, "SELECT COUNT(*) FROM message_logs WHERE event_id=? AND status IN ('sent','delivered')", (event_id,)))
        messages_failed = int(_scalar(conn, "SELECT COUNT(*) FROM message_logs WHERE event_id=? AND status IN ('failed','error')", (event_id,)))
        expenses_total = _scalar(conn, "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE event_id=? AND COALESCE(status,'pending') <> 'canceled'", (event_id,))
        expenses_paid = _scalar(conn, "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE event_id=? AND status='paid'", (event_id,))
        seated = int(_scalar(conn, "SELECT COUNT(*) FROM guests WHERE event_id=? AND COALESCE(final_table, corrected_table, current_table, '') <> ''", (event_id,)))
        occupancy = round((seated / total_guests) * 100, 2) if total_guests else 0.0
        conn.execute(
            """
            INSERT OR REPLACE INTO analytics_snapshots(
                id, tenant_id, event_id, snapshot_date, total_guests, confirmed_guests, pending_guests, declined_guests,
                messages_sent, messages_failed, expenses_total, expenses_paid, tables_occupancy_rate, created_at
            ) VALUES (
                (SELECT id FROM analytics_snapshots WHERE tenant_id=? AND event_id=? AND snapshot_date=?),
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
            )
            """,
            (tenant_id, event_id, snapshot_date, tenant_id, event_id, snapshot_date, total_guests, confirmed, pending, declined, messages_sent, messages_failed, expenses_total, expenses_paid, occupancy),
        )
    return {
        "tenant_id": tenant_id,
        "event_id": event_id,
        "snapshot_date": snapshot_date,
        "total_guests": total_guests,
        "confirmed_guests": confirmed,
        "pending_guests": pending,
        "declined_guests": declined,
        "messages_sent": messages_sent,
        "messages_failed": messages_failed,
        "expenses_total": expenses_total,
        "expenses_paid": expenses_paid,
        "tables_occupancy_rate": occupancy,
    }


def list_snapshots(event_id: int, tenant_id: int = 1, limit: int = 90) -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM analytics_snapshots WHERE tenant_id=? AND event_id=? ORDER BY snapshot_date DESC LIMIT ?",
            (tenant_id, event_id, int(limit)),
        ).fetchall()
    return [dict(r) for r in rows]
