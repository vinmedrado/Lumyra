from __future__ import annotations

from datetime import datetime, timedelta

from repositories.database import connect, init_db
from services.job_service import create_job
from services.workflow_service import run_due_rules

_LOCK_SECONDS = 60


def acquire_scheduler_lock(name: str = "scheduler") -> bool:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT id, locked_at FROM background_jobs WHERE type=? AND status='running' ORDER BY id DESC LIMIT 1", (name,)).fetchone()
        if row and row["locked_at"]:
            try:
                locked = datetime.fromisoformat(str(row["locked_at"]).replace("Z", "+00:00"))
                if datetime.now() - locked < timedelta(seconds=_LOCK_SECONDS):
                    return False
            except Exception:
                pass
        conn.execute("INSERT INTO background_jobs(type,status,progress,locked_at,locked_by,started_at) VALUES (?, 'running', 1, CURRENT_TIMESTAMP, 'scheduler', CURRENT_TIMESTAMP)", (name,))
    return True


def release_scheduler_lock(success: bool = True, error: str | None = None) -> None:
    with connect() as conn:
        row = conn.execute("SELECT id FROM background_jobs WHERE type='scheduler' AND status='running' ORDER BY id DESC LIMIT 1").fetchone()
        if row:
            conn.execute("UPDATE background_jobs SET status=?, progress=100, finished_at=CURRENT_TIMESTAMP, error_message=? WHERE id=?", ("success" if success else "failed", error, row["id"]))


def run_scheduler_tick() -> dict:
    if not acquire_scheduler_lock("scheduler"):
        return {"status": "locked", "message": "Scheduler já está em execução"}
    try:
        with connect() as conn:
            tenants = [int(r["id"]) for r in conn.execute("SELECT id FROM tenants").fetchall()]
            events = [dict(r) for r in conn.execute("SELECT id, COALESCE(tenant_id,1) tenant_id FROM events").fetchall()]
        workflow_results = {tid: run_due_rules(tid, only_due=True) for tid in tenants}
        snapshot_jobs = []
        for ev in events:
            snapshot_jobs.append(create_job("generate_analytics_snapshot", tenant_id=int(ev["tenant_id"]), event_id=int(ev["id"]), metadata_json={"source": "scheduler"}, priority=120))
        release_scheduler_lock(True)
        return {"status": "success", "workflows": workflow_results, "snapshot_jobs": snapshot_jobs}
    except Exception as exc:
        release_scheduler_lock(False, str(exc))
        raise
