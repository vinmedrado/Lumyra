from __future__ import annotations

from datetime import datetime
from typing import Any

from repositories.database import connect, init_db

VALID_SEVERITIES = {'success', 'info', 'warning', 'critical'}


def ensure_notification_schema() -> None:
    init_db()
    with connect() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL DEFAULT 1,
            user_id INTEGER,
            type TEXT NOT NULL DEFAULT 'info',
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'info',
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            related_entity_type TEXT,
            related_entity_id INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_notifications_tenant_read ON notifications(tenant_id, is_read, created_at);
        CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read, created_at);
        ''')


def create_notification(
    tenant_id: int = 1,
    title: str = '',
    message: str = '',
    severity: str = 'info',
    user_id: int | None = None,
    notification_type: str | None = None,
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
) -> dict[str, Any]:
    ensure_notification_schema()
    severity = severity if severity in VALID_SEVERITIES else 'info'
    with connect() as conn:
        cur = conn.execute(
            '''INSERT INTO notifications(tenant_id,user_id,type,title,message,severity,is_read,related_entity_type,related_entity_id)
               VALUES(?,?,?,?,?,?,0,?,?)''',
            (int(tenant_id), user_id, notification_type or severity, title.strip() or 'Nova notificação', message.strip(), severity, related_entity_type, related_entity_id),
        )
        row = conn.execute('SELECT * FROM notifications WHERE id=?', (cur.lastrowid,)).fetchone()
    return dict(row)


def list_notifications(tenant_id: int = 1, user_id: int | None = None, unread_only: bool = False, severity: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    ensure_notification_schema()
    where = ['tenant_id=?']; params: list[Any] = [int(tenant_id)]
    if user_id:
        where.append('(user_id IS NULL OR user_id=?)'); params.append(int(user_id))
    if unread_only:
        where.append('is_read=0')
    if severity:
        where.append('severity=?'); params.append(severity)
    params.append(int(limit))
    with connect() as conn:
        return [dict(r) for r in conn.execute(f"SELECT * FROM notifications WHERE {' AND '.join(where)} ORDER BY created_at DESC, id DESC LIMIT ?", tuple(params)).fetchall()]


def unread_count(tenant_id: int = 1, user_id: int | None = None) -> int:
    ensure_notification_schema()
    params: list[Any] = [int(tenant_id)]
    clause = 'tenant_id=? AND is_read=0'
    if user_id:
        clause += ' AND (user_id IS NULL OR user_id=?)'; params.append(int(user_id))
    with connect() as conn:
        row = conn.execute(f'SELECT COUNT(*) AS total FROM notifications WHERE {clause}', tuple(params)).fetchone()
    return int(row['total'] or 0)


def mark_read(notification_id: int, tenant_id: int = 1) -> None:
    ensure_notification_schema()
    with connect() as conn:
        conn.execute('UPDATE notifications SET is_read=1 WHERE id=? AND tenant_id=?', (int(notification_id), int(tenant_id)))


def mark_all_read(tenant_id: int = 1, user_id: int | None = None) -> int:
    ensure_notification_schema()
    sql = 'UPDATE notifications SET is_read=1 WHERE tenant_id=?'
    params: list[Any] = [int(tenant_id)]
    if user_id:
        sql += ' AND (user_id IS NULL OR user_id=?)'; params.append(int(user_id))
    with connect() as conn:
        cur = conn.execute(sql, tuple(params))
        return int(cur.rowcount or 0)
