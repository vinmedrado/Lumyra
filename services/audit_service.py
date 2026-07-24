from __future__ import annotations
import json
from typing import Any
from repositories.database import connect, init_db


def log_audit(
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    tenant_id: int | None = None,
    user_id: int | None = None,
    metadata: dict[str, Any] | None = None,
    event_id: int | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
    severity: str = 'info',
) -> None:
    init_db()
    payload = json.dumps(metadata or {}, ensure_ascii=False, default=str)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO audit_logs(tenant_id, user_id, event_id, action, entity_type, entity_id, metadata_json, ip, user_agent, request_id, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (tenant_id, user_id, event_id, action, entity_type, entity_id, payload, ip, user_agent, request_id, severity),
        )


def list_audit_logs(tenant_id: int | None = None, limit: int = 100, action: str | None = None, entity_type: str | None = None, severity: str | None = None) -> list[dict]:
    init_db()
    sql = 'SELECT * FROM audit_logs'
    where=[]; params=[]
    if tenant_id:
        where.append('tenant_id=?'); params.append(int(tenant_id))
    if action:
        where.append('action LIKE ?'); params.append(f'%{action}%')
    if entity_type:
        where.append('entity_type LIKE ?'); params.append(f'%{entity_type}%')
    if severity:
        where.append("COALESCE(severity,'info')=?"); params.append(severity)
    if where: sql += ' WHERE ' + ' AND '.join(where)
    sql += ' ORDER BY created_at DESC LIMIT ?'; params.append(int(limit))
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, tuple(params)).fetchall()]
