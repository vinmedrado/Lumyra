from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from repositories.database import connect, init_db

VALID_TRIGGERS = {"rsvp_pending", "event_soon", "message_failed", "guest_without_table", "payment_overdue"}
VALID_ACTIONS = {"send_whatsapp", "create_insight", "reenqueue_message", "create_job", "mark_guest_priority", "generate_alert"}


def _loads(value: str | dict | None) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value or "{}")
    except Exception:
        return {}


def _dumps(value: dict | None) -> str:
    return json.dumps(value or {}, ensure_ascii=False)


def _next_run(schedule_type: str, interval_minutes: int | None = None, daily_time: str | None = None) -> str | None:
    now = datetime.now()
    if schedule_type == "interval":
        return (now + timedelta(minutes=max(1, int(interval_minutes or 60)))).isoformat(timespec="seconds")
    if schedule_type == "daily" and daily_time:
        hour, minute = [int(x) for x in daily_time.split(":")[:2]]
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target.isoformat(timespec="seconds")
    return None


def create_rule(
    tenant_id: int,
    trigger_type: str,
    action_type: str,
    event_id: int | None = None,
    condition_json: str = "{}",
    action_json: str = "{}",
    schedule_type: str = "manual",
    interval_minutes: int | None = None,
    daily_time: str | None = None,
) -> int:
    init_db()
    if trigger_type not in VALID_TRIGGERS:
        raise ValueError(f"Trigger inválido: {trigger_type}")
    if action_type not in VALID_ACTIONS:
        raise ValueError(f"Ação inválida: {action_type}")
    _loads(condition_json); _loads(action_json)
    next_run_at = _next_run(schedule_type, interval_minutes, daily_time)
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO automation_rule_advanced(
                tenant_id,event_id,trigger_type,condition_json,action_type,action_json,is_active,
                schedule_type,interval_minutes,daily_time,next_run_at
            ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
            """,
            (tenant_id, event_id, trigger_type, condition_json, action_type, action_json, schedule_type, interval_minutes, daily_time, next_run_at),
        )
    return int(cur.lastrowid)


def list_rules(tenant_id: int) -> list[dict]:
    init_db()
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM automation_rule_advanced WHERE tenant_id=? ORDER BY id DESC", (tenant_id,)).fetchall()]


def _count_trigger(conn, rule: dict) -> int:
    event_id = rule.get("event_id")
    trigger = rule["trigger_type"]
    if trigger == "message_failed":
        sql = "SELECT COUNT(*) c FROM message_logs WHERE status IN ('failed','error')"
        params = []
        if event_id: sql += " AND event_id=?"; params.append(event_id)
        return int(conn.execute(sql, tuple(params)).fetchone()["c"])
    if trigger == "guest_without_table":
        if event_id:
            return int(conn.execute("SELECT COUNT(*) c FROM guests WHERE event_id=? AND COALESCE(final_table, corrected_table, current_table, '')=''", (event_id,)).fetchone()["c"])
    if trigger == "rsvp_pending":
        if event_id:
            return int(conn.execute("SELECT COUNT(*) c FROM guest_rsvp WHERE event_id=? AND status='pending'", (event_id,)).fetchone()["c"])
    if trigger == "payment_overdue":
        if event_id:
            return int(conn.execute("SELECT COUNT(*) c FROM expenses WHERE event_id=? AND status='overdue'", (event_id,)).fetchone()["c"])
    if trigger == "event_soon":
        if event_id:
            return int(conn.execute("SELECT COUNT(*) c FROM events WHERE id=? AND date IS NOT NULL AND date <= date('now','+14 day')", (event_id,)).fetchone()["c"])
    return 0



def _create_job_in_conn(conn, job_type: str, tenant_id: int, event_id: int | None, metadata: dict | None = None, priority: int = 100) -> int:
    cur = conn.execute(
        """
        INSERT INTO background_jobs(tenant_id, event_id, type, status, progress, metadata_json, priority, max_retries, retry_count, created_at)
        VALUES (?, ?, ?, 'queued', 0, ?, ?, 3, 0, CURRENT_TIMESTAMP)
        """,
        (tenant_id, event_id, job_type, _dumps(metadata), int(priority)),
    )
    return int(cur.lastrowid)

def _execute_action(conn, rule: dict, matched_count: int) -> dict:
    action = rule["action_type"]
    action_json = _loads(rule.get("action_json"))
    event_id = rule.get("event_id")
    tenant_id = int(rule["tenant_id"])
    if matched_count <= 0:
        return {"status": "skipped", "matched_count": 0}
    if action == "send_whatsapp":
        job_id = _create_job_in_conn(conn, "send_whatsapp_campaign", tenant_id, event_id, action_json)
        return {"job_id": job_id, "action": action, "matched_count": matched_count}
    if action == "reenqueue_message":
        job_id = _create_job_in_conn(conn, "retry_failed_messages", tenant_id, event_id, action_json)
        return {"job_id": job_id, "action": action, "matched_count": matched_count}
    if action in {"create_insight", "generate_alert"}:
        job_id = _create_job_in_conn(conn, "generate_event_insights", tenant_id, event_id, action_json)
        return {"job_id": job_id, "action": action, "matched_count": matched_count}
    if action == "create_job":
        job_id = _create_job_in_conn(conn, action_json.get("job_type", "generate_analytics_snapshot"), tenant_id, event_id, action_json)
        return {"job_id": job_id, "action": action, "matched_count": matched_count}
    if action == "mark_guest_priority" and event_id:
        conn.execute("UPDATE guests SET category=COALESCE(category,'') || ' | prioridade' WHERE event_id=? AND COALESCE(final_table, corrected_table, current_table, '')=''", (event_id,))
        return {"updated": matched_count, "action": action}
    return {"action": action, "matched_count": matched_count}


def run_due_rules(tenant_id: int, only_due: bool = False) -> dict:
    init_db(); processed = success = skipped = failed = 0
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        sql = "SELECT * FROM automation_rule_advanced WHERE tenant_id=? AND is_active=1"
        params: list = [tenant_id]
        if only_due:
            sql += " AND (schedule_type='manual' OR next_run_at IS NULL OR next_run_at<=?)"; params.append(now)
        rules = [dict(r) for r in conn.execute(sql, tuple(params)).fetchall()]
        for rule in rules:
            processed += 1
            try:
                count = _count_trigger(conn, rule)
                result = _execute_action(conn, rule, count)
                status = "success" if count else "skipped"
                success += 1 if count else 0
                skipped += 0 if count else 1
                next_run_at = _next_run(rule.get("schedule_type") or "manual", rule.get("interval_minutes"), rule.get("daily_time"))
                conn.execute(
                    "INSERT INTO automation_run_advanced(rule_id, tenant_id, status, result_json, affected_count, executed_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                    (rule["id"], tenant_id, status, _dumps(result), int(count)),
                )
                conn.execute("UPDATE automation_rule_advanced SET last_run_at=CURRENT_TIMESTAMP, next_run_at=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (next_run_at, rule["id"]))
            except Exception as exc:
                failed += 1
                conn.execute(
                    "INSERT INTO automation_run_advanced(rule_id, tenant_id, status, result_json, error_message, affected_count, executed_at) VALUES (?, ?, 'failed', '{}', ?, 0, CURRENT_TIMESTAMP)",
                    (rule["id"], tenant_id, str(exc)[:2000]),
                )
    return {"processed": processed, "success": success, "skipped": skipped, "failed": failed}
