from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from repositories.database import (
    audit_log,
    get_checkins,
    get_rsvp,
    list_adaptive_weights,
    list_guest_scores,
    load_guests_df,
    upsert_adaptive_weight,
    upsert_event_profile,
    upsert_guest_score,
)
from services.score_service import calculate_guest_score, recalculate_scores


@dataclass
class AdaptiveResult:
    updated_scores: int
    confirmation_weight: float
    presence_weight: float
    risk_level: str
    notes: str


def _risk_level(confirmation_rate: float, presence_rate: float, without_table_rate: float) -> str:
    if confirmation_rate < 0.35 or without_table_rate > 0.25:
        return "critical"
    if confirmation_rate < 0.55 or presence_rate < 0.50 or without_table_rate > 0.10:
        return "high"
    if confirmation_rate < 0.70 or without_table_rate > 0.03:
        return "medium"
    return "low"


def _dominant_groups(guests: pd.DataFrame) -> str:
    if guests.empty or "grupo" not in guests.columns:
        return ""
    groups = guests["grupo"].fillna("Sem grupo").astype(str).replace("", "Sem grupo")
    top = groups.value_counts().head(5)
    return ", ".join(f"{name} ({count})" for name, count in top.items())


def update_scores_from_real_data(event_id: int) -> AdaptiveResult:
    """Atualiza score dos convidados usando RSVP e presença reais do evento ativo.

    A lógica é heurística e determinística: não chama IA externa, mas adapta os pesos
    conforme os sinais reais já registrados no ERP.
    """
    guests = load_guests_df(event_id)
    if guests.empty:
        return AdaptiveResult(0, 1.0, 1.0, "low", "Sem convidados para aprender.")

    base_scores = recalculate_scores(event_id)
    rsvp = get_rsvp(event_id)
    checkins = get_checkins(event_id)

    total = len(guests)
    confirmed = int((rsvp["status"] == "confirmed").sum()) if not rsvp.empty and "status" in rsvp else 0
    declined = int((rsvp["status"] == "declined").sum()) if not rsvp.empty and "status" in rsvp else 0
    present = int(checkins["checked_in"].fillna(0).astype(int).sum()) if not checkins.empty and "checked_in" in checkins else 0
    with_table = int(guests["mesa_final"].fillna("").astype(str).ne("").sum()) if "mesa_final" in guests else 0

    confirmation_rate = confirmed / total if total else 0
    presence_rate = present / total if total else 0
    no_show_rate = max(0.0, (confirmed - present) / confirmed) if confirmed else 0.0
    without_table_rate = (total - with_table) / total if total else 0.0

    confirmation_weight = 1.0 + (confirmation_rate - 0.50) * 0.50
    presence_weight = 1.0 + (presence_rate - 0.50) * 0.70 - (no_show_rate * 0.30)
    confirmation_weight = max(0.70, min(1.35, confirmation_weight))
    presence_weight = max(0.65, min(1.40, presence_weight))

    upsert_adaptive_weight(event_id, "confirmation_weight", confirmation_weight, total)
    upsert_adaptive_weight(event_id, "presence_weight", presence_weight, total)
    upsert_adaptive_weight(event_id, "no_show_penalty", no_show_rate, confirmed)
    upsert_adaptive_weight(event_id, "without_table_penalty", without_table_rate, total)

    updated = 0
    if not base_scores.empty:
        checkin_map = {}
        if not checkins.empty:
            checkin_map = {int(r["guest_id"]): int(r.get("checked_in", 0) or 0) for _, r in checkins.fillna(0).iterrows()}
        for _, row in base_scores.fillna("").iterrows():
            guest_id = int(row["guest_id"])
            probability = float(row.get("attendance_probability", 0)) * confirmation_weight
            engagement = float(row.get("engagement_score", 0)) * confirmation_weight
            priority = float(row.get("priority_score", 0))
            if checkin_map.get(guest_id) == 1:
                probability = max(probability, 0.98)
                engagement += 12
                priority -= 10
            elif row.get("rsvp_status") == "confirmed":
                probability *= presence_weight
            if not str(row.get("final_table") or "").strip():
                priority += 15
            score = calculate_guest_score(row.to_dict())
            upsert_guest_score(
                event_id,
                guest_id,
                attendance_probability=max(0, min(1, probability or score["attendance_probability"])),
                priority_score=max(0, min(100, priority or score["priority_score"])),
                engagement_score=max(0, min(100, engagement or score["engagement_score"])),
                explanation=f"Adaptativo: RSVP real, check-in real, peso confirmação={confirmation_weight:.2f}, peso presença={presence_weight:.2f}",
            )
            updated += 1

    avg_probability = float(list_guest_scores(event_id)["attendance_probability"].mean()) if updated else 0.0
    risk = _risk_level(confirmation_rate, presence_rate, without_table_rate)
    notes = (
        f"Confirmação {confirmation_rate:.1%}; presença {presence_rate:.1%}; "
        f"no-show {no_show_rate:.1%}; sem mesa {without_table_rate:.1%}."
    )
    upsert_event_profile(event_id, {
        "confirmation_rate": confirmation_rate,
        "presence_rate": presence_rate,
        "no_show_rate": no_show_rate,
        "avg_attendance_probability": avg_probability,
        "dominant_groups": _dominant_groups(guests),
        "operational_risk": risk,
        "learned_notes": notes,
    })
    audit_log(event_id, "adaptive_engine", None, "update_scores", notes)
    return AdaptiveResult(updated, confirmation_weight, presence_weight, risk, notes)


def get_learning_summary(event_id: int) -> dict:
    weights = list_adaptive_weights(event_id)
    scores = list_guest_scores(event_id)
    return {
        "weights": weights,
        "scores": scores,
        "avg_probability": 0 if scores.empty else float(scores["attendance_probability"].mean()),
        "high_priority": 0 if scores.empty else int((scores["priority_score"] >= 70).sum()),
    }
