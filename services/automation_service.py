from __future__ import annotations

from datetime import date, datetime

import pandas as pd

from repositories.database import (
    create_task,
    enqueue_messages,
    get_event,
    get_rsvp,
    list_automation_rules,
    record_automation_run,
    audit_log,
)
from services.message_ai_service import gerar_lote_por_rsvp, gerar_template_dinamico


def _days_until(event_id: int) -> int | None:
    raw = str(get_event(event_id).get("date") or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return (datetime.strptime(raw[:10], fmt).date() - date.today()).days
        except ValueError:
            continue
    return None


def _trigger_is_due(event_id: int, trigger: str) -> bool:
    days = _days_until(event_id)
    if trigger == "event_minus_3_days":
        return days == 3
    if trigger == "event_minus_1_day":
        return days == 1
    return True


def execute_rule(event_id: int, rule: dict, dry_run: bool = True) -> dict:
    trigger = rule.get("trigger")
    action = rule.get("action")
    if not _trigger_is_due(event_id, trigger):
        record_automation_run(event_id, int(rule["id"]), "dry_run" if dry_run else "success", 0, "Trigger temporal ainda não está no prazo.")
        return {"rule_id": rule.get("id"), "status": "skipped", "processed_count": 0, "details": "fora do prazo"}
    status_filter = "pending"
    if trigger == "RSVP_confirmed":
        status_filter = "confirmed"
    elif trigger == "RSVP_pending":
        status_filter = "pending"
    elif trigger == "checkin_missing":
        status_filter = "confirmed"
    template = str(rule.get("template") or "").strip()
    processed = 0
    details = ""
    if action in {"send_message", "reminder"}:
        items = gerar_lote_por_rsvp(event_id, "lembrete" if action == "reminder" else "confirmacao", status_filter)
        condition = str(rule.get("condition") or "todos")
        if condition == "sem_mesa":
            items = [item for item in items if not str(item.get("mesa") or "").strip()]
        if template:
            from services.guest_portal_service import get_guest_link
            from services.whatsapp_service import render_template
            for item in items:
                guest_link = ""
                guest_id = item.get("guest_id")
                if str(guest_id or "").isdigit():
                    guest_link = get_guest_link(event_id, int(guest_id))
                item["template"] = template
                item["mensagem"] = render_template(template, nome=item.get("nome") or "", mesa=item.get("mesa") or "a confirmar", grupo=item.get("grupo") or "geral", guest_link=guest_link)
        if not dry_run:
            processed = enqueue_messages(event_id, items, skip_sent=True)
        else:
            processed = len(items)
        details = f"{processed} mensagem(ns) {'simuladas' if dry_run else 'enfileiradas'} para RSVP={status_filter}."
    elif action == "create_task":
        rsvp = get_rsvp(event_id, status_filter)
        processed = 0 if rsvp.empty else len(rsvp)
        if not dry_run and processed:
            create_task(event_id, f"Revisar convidados com RSVP {status_filter}", f"Automação gerou tarefa para {processed} convidado(s).", priority="high", owner="Assessoria")
        details = f"Tarefa {'simulada' if dry_run else 'criada'} para {processed} convidado(s)."
    run_status = "dry_run" if dry_run else "success"
    record_automation_run(event_id, int(rule["id"]), run_status, processed, details)
    audit_log(event_id, "automation_rule", int(rule["id"]), "execute", details)
    return {"rule_id": rule.get("id"), "rule_name": rule.get("name"), "status": run_status, "processed_count": processed, "details": details}


def execute_enabled_rules(event_id: int, dry_run: bool = True) -> pd.DataFrame:
    rules = list_automation_rules(event_id, enabled_only=True)
    results = []
    if rules.empty:
        return pd.DataFrame(columns=["rule_id", "rule_name", "status", "processed_count", "details"])
    for _, row in rules.iterrows():
        results.append(execute_rule(event_id, row.to_dict(), dry_run=dry_run))
    return pd.DataFrame(results)
