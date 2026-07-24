from __future__ import annotations

import json
import os
import traceback
from datetime import datetime, timedelta
from threading import Thread
from typing import Callable

from repositories.database import connect, init_db

TERMINAL_STATUS = {"success", "failed", "canceled"}
RUNNABLE_STATUS = {"queued", "failed"}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _json(value) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value or {}, ensure_ascii=False)


def create_job(
    job_type: str,
    tenant_id: int | None = None,
    event_id: int | None = None,
    metadata_json: str | dict = "{}",
    priority: int = 100,
    max_retries: int = 3,
) -> int:
    init_db()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO background_jobs(tenant_id, event_id, type, status, progress, metadata_json, priority, max_retries, retry_count, created_at)
            VALUES (?, ?, ?, 'queued', 0, ?, ?, ?, 0, ?)
            """,
            (tenant_id, event_id, job_type, _json(metadata_json), int(priority), int(max_retries), _now()),
        )
        return int(cur.lastrowid)


def update_job(job_id: int, status: str | None = None, progress: int | None = None, error_message: str | None = None, result_json: str | dict | None = None) -> None:
    init_db()
    fields, params = [], []
    if status is not None:
        fields.append("status=?"); params.append(status)
        if status == "running": fields.append("started_at=COALESCE(started_at, ?)"); params.append(_now())
        if status in TERMINAL_STATUS: fields.append("finished_at=?"); params.append(_now())
    if progress is not None:
        fields.append("progress=?"); params.append(max(0, min(100, int(progress))))
    if error_message is not None:
        fields.append("error_message=?"); params.append(error_message[:4000])
    if result_json is not None:
        fields.append("result_json=?"); params.append(_json(result_json))
    if not fields:
        return
    params.append(int(job_id))
    with connect() as conn:
        conn.execute(f"UPDATE background_jobs SET {', '.join(fields)} WHERE id=?", tuple(params))


def lock_next_job(worker_id: str | None = None) -> dict | None:
    init_db()
    worker_id = worker_id or f"worker-{os.getpid()}"
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM background_jobs
            WHERE status='queued'
            ORDER BY priority ASC, created_at ASC, id ASC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return None
        conn.execute(
            "UPDATE background_jobs SET status='running', locked_at=CURRENT_TIMESTAMP, locked_by=?, started_at=COALESCE(started_at, CURRENT_TIMESTAMP), progress=5 WHERE id=? AND status='queued'",
            (worker_id, row["id"]),
        )
        locked = conn.execute("SELECT * FROM background_jobs WHERE id=?", (row["id"],)).fetchone()
    return dict(locked) if locked else None


def mark_retry(job: dict, error_message: str) -> None:
    retry_count = int(job.get("retry_count") or job.get("attempts") or 0) + 1
    max_retries = int(job.get("max_retries") or 3)
    if retry_count <= max_retries:
        delay = min(300, 2 ** retry_count * 5)
        with connect() as conn:
            conn.execute(
                "UPDATE background_jobs SET status='queued', retry_count=?, progress=0, locked_at=NULL, locked_by=NULL, error_message=? WHERE id=?",
                (retry_count, f"Retry em ~{delay}s: {error_message[:1500]}", job["id"]),
            )
    else:
        update_job(int(job["id"]), status="failed", progress=100, error_message=error_message)


def run_async(job_id: int, fn: Callable[[], None]) -> None:
    def _runner() -> None:
        try:
            update_job(job_id, status="running", progress=5)
            fn()
            update_job(job_id, status="success", progress=100)
        except Exception as exc:
            update_job(job_id, status="failed", error_message=f"{exc}\n{traceback.format_exc()}")
    Thread(target=_runner, daemon=True).start()


def list_jobs(limit: int = 50, tenant_id: int | None = None, status: str | None = None) -> list[dict]:
    init_db()
    sql = "SELECT * FROM background_jobs"
    params: list = []
    where = []
    if tenant_id:
        where.append("tenant_id=?"); params.append(int(tenant_id))
    if status:
        where.append("status=?"); params.append(status)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT ?"; params.append(int(limit))
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, tuple(params)).fetchall()]


def count_active_jobs() -> int:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM background_jobs WHERE status IN ('queued','running')").fetchone()
    return int(row["total"] or 0) if row else 0
