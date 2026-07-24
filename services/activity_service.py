from __future__ import annotations

from datetime import datetime
from typing import Any
from repositories.database import connect, init_db


def ensure_activity_schema() -> None:
    init_db()
    with connect() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS activity_feed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL DEFAULT 1,
            user_id INTEGER,
            action_type TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_activity_tenant_created ON activity_feed(tenant_id, created_at);
        ''')


def record_activity(tenant_id: int = 1, message: str = '', action_type: str = 'system', user_id: int | None = None, entity_type: str | None = None, entity_id: int | None = None) -> dict[str, Any]:
    ensure_activity_schema()
    created_at = datetime.now().isoformat(timespec='seconds')
    with connect() as conn:
        cur = conn.execute(
            '''INSERT INTO activity_feed(tenant_id,user_id,action_type,entity_type,entity_id,message,created_at) VALUES(?,?,?,?,?,?,?)''',
            (int(tenant_id), user_id, action_type, entity_type, entity_id, message, created_at),
        )
        row = conn.execute('SELECT * FROM activity_feed WHERE id=?', (cur.lastrowid,)).fetchone()
    return dict(row)


def list_activity(tenant_id: int = 1, limit: int = 30) -> list[dict[str, Any]]:
    ensure_activity_schema()
    with connect() as conn:
        rows = conn.execute('SELECT * FROM activity_feed WHERE tenant_id=? ORDER BY created_at DESC, id DESC LIMIT ?', (int(tenant_id), int(limit))).fetchall()
    return [dict(r) for r in rows]
