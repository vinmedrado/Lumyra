from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from repositories.database import connect, init_db


def ensure_presence_schema() -> None:
    init_db()
    with connect() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS online_users (
            user_id INTEGER NOT NULL,
            tenant_id INTEGER NOT NULL DEFAULT 1,
            last_seen TEXT NOT NULL,
            current_page TEXT,
            is_online INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY(user_id, tenant_id)
        );
        CREATE INDEX IF NOT EXISTS idx_online_tenant_seen ON online_users(tenant_id, last_seen);
        CREATE TABLE IF NOT EXISTS entity_locks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL DEFAULT 1,
            user_id INTEGER,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            locked_until TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tenant_id, entity_type, entity_id)
        );
        ''')


def update_presence(user_id: int, tenant_id: int = 1, current_page: str | None = None) -> None:
    ensure_presence_schema()
    now = datetime.now().isoformat(timespec='seconds')
    with connect() as conn:
        conn.execute('''INSERT INTO online_users(user_id,tenant_id,last_seen,current_page,is_online) VALUES(?,?,?,?,1)
                        ON CONFLICT(user_id,tenant_id) DO UPDATE SET last_seen=excluded.last_seen,current_page=excluded.current_page,is_online=1''',
                     (int(user_id), int(tenant_id), now, current_page))


def mark_offline(user_id: int, tenant_id: int = 1) -> None:
    ensure_presence_schema()
    with connect() as conn:
        conn.execute('UPDATE online_users SET is_online=0,last_seen=? WHERE user_id=? AND tenant_id=?', (datetime.now().isoformat(timespec='seconds'), int(user_id), int(tenant_id)))


def list_online_users(tenant_id: int = 1, active_minutes: int = 5) -> list[dict[str, Any]]:
    ensure_presence_schema()
    cutoff = (datetime.now() - timedelta(minutes=active_minutes)).isoformat(timespec='seconds')
    with connect() as conn:
        rows = conn.execute('''SELECT ou.*, u.name, u.email, u.role FROM online_users ou LEFT JOIN users u ON u.id=ou.user_id
                               WHERE ou.tenant_id=? AND ou.is_online=1 AND ou.last_seen>=? ORDER BY ou.last_seen DESC''', (int(tenant_id), cutoff)).fetchall()
    return [dict(r) for r in rows]


def acquire_lock(tenant_id: int, user_id: int | None, entity_type: str, entity_id: int, ttl_seconds: int = 120) -> dict[str, Any]:
    ensure_presence_schema()
    now = datetime.now()
    expires = (now + timedelta(seconds=ttl_seconds)).isoformat(timespec='seconds')
    with connect() as conn:
        existing = conn.execute('SELECT * FROM entity_locks WHERE tenant_id=? AND entity_type=? AND entity_id=? AND locked_until>?', (int(tenant_id), entity_type, int(entity_id), now.isoformat(timespec='seconds'))).fetchone()
        if existing and existing['user_id'] != user_id:
            return {'locked': False, 'lock': dict(existing)}
        conn.execute('''INSERT INTO entity_locks(tenant_id,user_id,entity_type,entity_id,locked_until,created_at) VALUES(?,?,?,?,?,?)
                        ON CONFLICT(tenant_id,entity_type,entity_id) DO UPDATE SET user_id=excluded.user_id,locked_until=excluded.locked_until''',
                     (int(tenant_id), user_id, entity_type, int(entity_id), expires, now.isoformat(timespec='seconds')))
    return {'locked': True, 'locked_until': expires}
