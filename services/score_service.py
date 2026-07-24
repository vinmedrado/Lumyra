from __future__ import annotations

import pandas as pd

from repositories.database import get_rsvp, get_checkins, list_guest_scores, upsert_guest_score, audit_log


def calculate_guest_score(row: dict) -> dict:
    rsvp = str(row.get("status") or row.get("rsvp_status") or "pending")
    has_phone = bool(str(row.get("phone") or "").strip())
    has_table = bool(str(row.get("final_table") or row.get("mesa_final") or "").strip())
    group_name = str(row.get("group_name") or row.get("grupo") or "").strip()
    probability_map = {"confirmed": 0.92, "maybe": 0.58, "pending": 0.42, "declined": 0.05}
    attendance_probability = probability_map.get(rsvp, 0.35)
    engagement_score = 25
    if has_phone:
        engagement_score += 30
    if rsvp == "confirmed":
        engagement_score += 35
    elif rsvp == "maybe":
        engagement_score += 20
    elif rsvp == "declined":
        engagement_score -= 10
    if has_table:
        engagement_score += 10
    priority_score = 30
    if rsvp in {"confirmed", "maybe"}:
        priority_score += 25
    if not has_table and rsvp != "declined":
        priority_score += 25
    if group_name:
        priority_score += 10
    if not has_phone:
        priority_score += 10
    return {
        "attendance_probability": max(0, min(1, attendance_probability)),
        "priority_score": max(0, min(100, priority_score)),
        "engagement_score": max(0, min(100, engagement_score)),
        "explanation": f"RSVP={rsvp}; telefone={'sim' if has_phone else 'não'}; mesa={'sim' if has_table else 'não'}; grupo={'sim' if group_name else 'não'}",
    }


def recalculate_scores(event_id: int) -> pd.DataFrame:
    rsvp = get_rsvp(event_id)
    if rsvp.empty:
        return pd.DataFrame()
    for _, row in rsvp.fillna("").iterrows():
        score = calculate_guest_score(row.to_dict())
        upsert_guest_score(event_id, int(row["guest_id"]), **score)
    audit_log(event_id, "guest_score", None, "recalculate", f"total={len(rsvp)}")
    return list_guest_scores(event_id)
