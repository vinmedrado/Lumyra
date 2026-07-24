from __future__ import annotations

import pandas as pd

from repositories.database import (
    audit_log,
    get_checkins,
    get_rsvp,
    list_guest_profiles,
    load_guests_df,
    upsert_guest_profile,
    list_guest_portal_responses,
)


def _classify(rsvp_status: str, checked_in: int, has_phone: bool, has_table: bool, group_size: int) -> tuple[str, str, float, str]:
    if rsvp_status == "declined":
        return "declined", "declined", 15.0, "Recusou presença; baixa prioridade de acionamento."
    if checked_in:
        influence = 65 + min(20, group_size * 3) + (10 if has_phone else 0)
        return "champion", "confirmed_present", min(100, influence), "Confirmou/compareceu; perfil confiável para operação."
    if rsvp_status == "confirmed":
        influence = 55 + min(20, group_size * 3) + (10 if has_phone else 0) + (5 if has_table else 0)
        return "reliable", "confirmed_absent", min(100, influence), "Confirmado, mas ainda sem check-in; monitorar no evento ao vivo."
    if rsvp_status == "maybe":
        influence = 45 + min(15, group_size * 2) + (10 if has_phone else 0)
        return "needs_followup", "uncertain", min(100, influence), "Talvez; bom alvo para mensagem de confirmação."
    influence = 35 + min(15, group_size * 2) + (10 if has_phone else 0) + (10 if not has_table else 0)
    return "at_risk", "uncertain", min(100, influence), "Pendente; exige acompanhamento proativo."


def rebuild_guest_profiles(event_id: int) -> pd.DataFrame:
    guests = load_guests_df(event_id)
    if guests.empty:
        return pd.DataFrame()
    rsvp = get_rsvp(event_id)
    checkins = get_checkins(event_id)
    portal = list_guest_portal_responses(event_id)
    portal_map = {int(r["guest_id"]): True for _, r in portal.iterrows()} if not portal.empty and "guest_id" in portal else {}
    rsvp_map = {int(r["guest_id"]): r.get("status", "pending") for _, r in rsvp.fillna("pending").iterrows()} if not rsvp.empty else {}
    checkin_map = {int(r["guest_id"]): int(r.get("checked_in", 0) or 0) for _, r in checkins.fillna(0).iterrows()} if not checkins.empty else {}
    group_sizes = guests["grupo"].fillna("").astype(str).value_counts().to_dict() if "grupo" in guests else {}

    for _, row in guests.fillna("").iterrows():
        guest_id = int(row["id"])
        group_name = str(row.get("grupo", ""))
        behavioral_type, attendance_pattern, influence, notes = _classify(
            str(rsvp_map.get(guest_id, "pending")),
            int(checkin_map.get(guest_id, 0)),
            bool(str(row.get("telefone", "")).strip()) or bool(portal_map.get(guest_id)),
            bool(str(row.get("mesa_final", "")).strip()),
            int(group_sizes.get(group_name, 1)) + (1 if portal_map.get(guest_id) else 0),
        )
        upsert_guest_profile(event_id, guest_id, behavioral_type, attendance_pattern, influence, notes)
    audit_log(event_id, "guest_profile", None, "rebuild", f"total={len(guests)}")
    return list_guest_profiles(event_id)
