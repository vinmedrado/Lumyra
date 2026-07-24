from __future__ import annotations

from collections import defaultdict

import pandas as pd

from repositories.database import list_tables, load_guests_df, update_guest_table
from services.audit_service import record_action


def generate_suggestions(event_id: int) -> list[dict]:
    """Sugere mesas para convidados sem mesa usando heurística determinística.

    Critérios: grupo junto quando possível, respeitar capacidade cadastrada e aproveitar ocupação atual.
    """
    guests = load_guests_df(event_id)
    tables = list_tables(event_id)
    if guests.empty or tables.empty:
        return []

    guests = guests.fillna("")
    table_caps = {}
    for _, row in tables.iterrows():
        cap = row.get("capacity")
        table_caps[str(row.get("name", "")).strip()] = int(cap) if str(cap or "").isdigit() and int(cap) > 0 else 9999

    ocup = defaultdict(int)
    for mesa in guests["mesa_final"].astype(str).str.strip():
        if mesa:
            ocup[mesa] += 1

    sem_mesa = guests[guests["mesa_final"].astype(str).str.strip().eq("")].copy()
    if sem_mesa.empty:
        return []

    suggestions: list[dict] = []
    grouped = sem_mesa.groupby(sem_mesa["grupo"].replace("", pd.NA).fillna(sem_mesa["nome_original"]))
    for grupo, gdf in grouped:
        size = len(gdf)
        chosen = None
        for table_name, cap in sorted(table_caps.items(), key=lambda item: (ocup[item[0]], item[0])):
            if ocup[table_name] + size <= cap:
                chosen = table_name
                break
        if chosen is None:
            chosen = min(table_caps.keys(), key=lambda name: ocup[name])
        for _, guest in gdf.iterrows():
            suggestions.append({
                "guest_id": int(guest["id"]),
                "guest_name": guest.get("nome_original") or guest.get("nome"),
                "group_name": str(grupo),
                "suggested_table": chosen,
                "reason": f"Grupo '{grupo}' alocado junto considerando capacidade disponível.",
            })
        ocup[chosen] += size
    return suggestions


def apply_suggestions(event_id: int, suggestions: list[dict]) -> int:
    count = 0
    for item in suggestions:
        guest_id = int(item["guest_id"])
        update_guest_table(event_id, guest_id, item.get("suggested_table", ""), "sugerida")
        count += 1
    record_action(event_id, "seating_suggestion", None, "apply", f"{count} sugestão(ões) aplicada(s)")
    return count
