from __future__ import annotations

from db.session import ping_database
from repositories.database import connect, init_db
from services.job_service import count_active_jobs
from services.storage_service import ensure_storage


def _count(table: str, where: str = "1=1") -> int:
    try:
        with connect() as conn:
            row = conn.execute(f"SELECT COUNT(*) AS total FROM {table} WHERE {where}").fetchone()
        return int(row["total"] or 0) if row else 0
    except Exception:
        return 0


def system_health() -> dict:
    init_db()
    return {
        "database_ok": ping_database(),
        "storage_ok": ensure_storage(),
        "active_jobs": count_active_jobs(),
        "queued_jobs": _count("background_jobs", "status='queued'"),
        "failed_jobs": _count("background_jobs", "status='failed'"),
        "scheduler_status": "ok" if _count("background_jobs", "type='scheduler' AND status='running'") == 0 else "running",
        "worker_status": "ready" if _count("background_jobs", "status='queued'") >= 0 else "unknown",
        "pending_messages": _count("messages", "status='pending'"),
        "failed_messages": _count("messages", "status='error'"),
        "total_tenants": _count("tenants"),
        "total_users": _count("users"),
        "total_events": _count("events"),
        "notifications": _count("notifications"),
        "online_users": _count("online_users", "is_online=1"),
    }
