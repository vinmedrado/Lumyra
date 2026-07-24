from __future__ import annotations

import json
from datetime import date
from typing import Any

from repositories.database import connect, init_db
from services.analytics_snapshot_service import generate_analytics_snapshot
from services.export_service import export_guests_csv, export_financial_csv, export_tables_csv, export_form_responses_csv
from services.event_insights import generate_insights
from services.whatsapp_service import send_pending_messages, retry_failed_messages


def _metadata(job: dict) -> dict[str, Any]:
    raw = job.get("metadata_json") or "{}"
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return {}


def send_whatsapp_campaign(job: dict) -> dict:
    meta = _metadata(job)
    event_id = int(job.get("event_id") or meta.get("event_id") or 1)
    limit = int(meta.get("limit") or 50)
    return {"sent": send_pending_messages(event_id, limit=limit)}


def retry_failed_messages_task(job: dict) -> dict:
    meta = _metadata(job)
    event_id = int(job.get("event_id") or meta.get("event_id") or 1)
    limit = int(meta.get("limit") or 50)
    return {"reenqueued": retry_failed_messages(event_id, limit=limit)}


def generate_event_insights(job: dict) -> dict:
    event_id = int(job.get("event_id") or _metadata(job).get("event_id") or 1)
    insights = generate_insights(event_id)
    return {"insights": len(insights)}


def generate_analytics_snapshot_task(job: dict) -> dict:
    event_id = int(job.get("event_id") or _metadata(job).get("event_id") or 1)
    tenant_id = int(job.get("tenant_id") or _metadata(job).get("tenant_id") or 1)
    snapshot = generate_analytics_snapshot(tenant_id, event_id, snapshot_date=date.today().isoformat())
    return snapshot


def export_data(job: dict) -> dict:
    meta = _metadata(job)
    export_type = meta.get("export_type", "guests")
    event_id = int(job.get("event_id") or meta.get("event_id") or 1)
    tenant_id = int(job.get("tenant_id") or meta.get("tenant_id") or 1)
    if export_type == "financial":
        path = export_financial_csv(event_id, tenant_id)
    elif export_type == "tables":
        path = export_tables_csv(event_id, tenant_id)
    elif export_type == "forms":
        path = export_form_responses_csv(event_id, tenant_id)
    else:
        path = export_guests_csv(event_id, tenant_id)
    return {"path": str(path), "export_type": export_type}


TASKS = {
    "send_whatsapp_campaign": send_whatsapp_campaign,
    "retry_failed_messages": retry_failed_messages_task,
    "generate_event_insights": generate_event_insights,
    "generate_analytics_snapshot": generate_analytics_snapshot_task,
    "export_data": export_data,
}
