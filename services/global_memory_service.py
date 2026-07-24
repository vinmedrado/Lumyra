from __future__ import annotations

import json

from repositories.database import (
    get_event_profile,
    list_global_event_insights,
    list_guest_scores,
    upsert_global_event_insight,
)
from services.insight_service import generate_event_insights


def snapshot_event_to_global_memory(event_id: int, source: str = "manual") -> dict:
    """Salva um snapshot comparável do evento atual na memória global.

    A memória é global entre eventos, mas cada linha permanece vinculada a um
    event_id para manter rastreabilidade e evitar mistura operacional.
    """
    metrics = generate_event_insights(event_id)
    profile = get_event_profile(event_id)
    scores = list_guest_scores(event_id)
    avg_prob = 0.0 if scores.empty else float(scores["attendance_probability"].mean())
    no_show = float(profile.get("no_show_rate", 0) or 0) if profile else 0.0
    snapshot = {
        "total_guests": int(metrics.get("total_guests", 0) or 0),
        "confirmation_rate": float(metrics.get("confirmation_rate", 0) or 0),
        "presence_rate": float(metrics.get("presence_rate", 0) or 0),
        "no_show_rate": no_show,
        "table_efficiency": float(metrics.get("table_efficiency", 0) or 0),
        "avg_attendance_probability": avg_prob,
        "critical_conflicts": int(metrics.get("critical_conflicts", 0) or 0),
    }
    upsert_global_event_insight(event_id, snapshot, json.dumps(snapshot, ensure_ascii=False), source=source)
    return snapshot


def get_global_memory_summary(event_id: int) -> dict:
    base = list_global_event_insights(exclude_event_id=event_id, limit=500)
    if base.empty:
        return {"events_count": 0, "benchmarks": {}, "dataframe": base}
    benchmarks = {}
    for col in ["confirmation_rate", "presence_rate", "no_show_rate", "table_efficiency", "avg_attendance_probability", "critical_conflicts", "total_guests"]:
        if col in base.columns:
            benchmarks[col] = float(base[col].fillna(0).mean())
    return {"events_count": len(base), "benchmarks": benchmarks, "dataframe": base}
