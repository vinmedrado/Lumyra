from __future__ import annotations

from pathlib import Path
from datetime import datetime
import pandas as pd

from core.settings import get_settings
from repositories.database import connect, init_db


def _export_dir() -> Path:
    path = get_settings().storage_root / "exports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def export_query_to_csv(name: str, sql: str, params: tuple = ()) -> str:
    init_db()
    with connect() as conn:
        df = pd.read_sql_query(sql, conn, params=params)
    safe = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in name)
    output = _export_dir() / f"{safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(output, index=False, encoding="utf-8-sig")
    return str(output)


def export_guests_csv(event_id: int, tenant_id: int | None = None) -> str:
    return export_query_to_csv("convidados", "SELECT * FROM guests WHERE event_id=?", (int(event_id),))


def export_tables_csv(event_id: int, tenant_id: int | None = None) -> str:
    return export_query_to_csv("mesas", "SELECT * FROM guests WHERE event_id=? ORDER BY final_table, group_name, name", (int(event_id),))


def export_financial_csv(event_id: int, tenant_id: int | None = None) -> str:
    return export_query_to_csv("financeiro", "SELECT e.*, v.name AS vendor_name FROM expenses e LEFT JOIN vendors v ON v.id=e.vendor_id WHERE e.event_id=?", (int(event_id),))


def export_form_responses_csv(event_id: int, tenant_id: int | None = None) -> str:
    return export_query_to_csv("respostas_formularios", """
        SELECT g.name AS guest_name, f.title AS form_title, ff.label, r.value, r.updated_at
        FROM event_form_responses r
        JOIN event_form_fields ff ON ff.id=r.field_id
        JOIN event_forms f ON f.id=ff.form_id
        JOIN guests g ON g.id=r.guest_id
        WHERE g.event_id=?
        ORDER BY g.name, f.title, ff.sort_order
    """, (int(event_id),))
