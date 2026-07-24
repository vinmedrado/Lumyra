from __future__ import annotations

import pandas as pd

from repositories.database import create_task, get_checkins, get_rsvp, list_tables, load_guests_df, audit_log
from services.whatsapp_service import build_queue_from_guests

DEFAULT_RSVP_TEMPLATE = "Olá {nome}! Confirme ou atualize seus dados do evento por aqui: {guest_link}"
DEFAULT_CHECKIN_TEMPLATE = "Olá {nome}! Estamos aguardando sua chegada no evento. Mesa: {mesa}. Qualquer dúvida, responda por aqui."


def _message_df_from_guests(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    mapped = df.copy()
    rename = {
        "guest_id": "id",
        "guest_name": "nome_original",
        "name": "nome",
        "group_name": "grupo",
        "final_table": "mesa_final",
        "phone": "telefone",
    }
    for src, dst in rename.items():
        if src in mapped.columns and dst not in mapped.columns:
            mapped[dst] = mapped[src]
    return mapped


def get_action_label(action_type: str) -> str:
    labels = {
        "send_rsvp_reminder": "Enviar mensagem",
        "prioritize_followup": "Criar tarefa",
        "generate_seating_suggestions": "Ajustar mesa",
        "review_table_conflicts": "Marcar ação",
        "review_table_warnings": "Marcar ação",
        "checkin_followup": "Enviar mensagem",
        "profile_followup": "Criar tarefa",
        "create_tables": "Criar tarefa",
        "monitor": "Marcar ação",
        "operational_review": "Marcar ação",
    }
    return labels.get(action_type or "", "Marcar ação")


def execute_quick_action(event_id: int, insight: dict) -> dict:
    """Executa uma ação segura e auditável baseada em um insight do Event Brain.

    Nenhuma ação ignora event_id. A execução é conservadora: mensagens entram em fila,
    ajustes de mesa viram tarefas e revisões viram ações operacionais.
    """
    action_type = str(insight.get("action_type") or "operational_review")
    title = str(insight.get("title") or "Ação do Event Brain")
    message = str(insight.get("message") or "")
    recommendation = str(insight.get("recommendation") or "")

    if action_type == "send_rsvp_reminder":
        rsvp = get_rsvp(event_id, "pending")
        df = _message_df_from_guests(rsvp)
        count = build_queue_from_guests(df, DEFAULT_RSVP_TEMPLATE, event_id=event_id)
        audit_log(event_id, "event_brain", None, "quick_send_rsvp_reminder", f"queued={count}")
        return {"ok": True, "kind": "message", "message": f"{count} mensagem(ns) de RSVP foram enfileiradas."}

    if action_type == "checkin_followup":
        rsvp = get_rsvp(event_id, "confirmed")
        checkins = get_checkins(event_id)
        checked_ids = set(checkins.loc[checkins["checked_in"].fillna(0).astype(int) == 1, "guest_id"].astype(int).tolist()) if not checkins.empty else set()
        pending = rsvp[~rsvp["guest_id"].astype(int).isin(checked_ids)] if not rsvp.empty else pd.DataFrame()
        count = build_queue_from_guests(_message_df_from_guests(pending), DEFAULT_CHECKIN_TEMPLATE, event_id=event_id)
        audit_log(event_id, "event_brain", None, "quick_checkin_followup", f"queued={count}")
        return {"ok": True, "kind": "message", "message": f"{count} mensagem(ns) para confirmados sem check-in foram enfileiradas."}

    priority = "critical" if insight.get("severity") == "critical" else "high" if insight.get("severity") == "warning" else "medium"
    task_title = f"Event Brain · {title}"
    task_description = f"{message}\n\nRecomendação: {recommendation}".strip()

    if action_type == "generate_seating_suggestions":
        task_description += "\n\nAção sugerida: abrir a página Sugestões, revisar distribuição e aplicar manualmente."
    elif action_type == "create_tables" and list_tables(event_id).empty:
        task_description += "\n\nAção sugerida: cadastrar mesas com capacidade antes de distribuir convidados."

    task_id = create_task(event_id, task_title, task_description, priority=priority)
    audit_log(event_id, "event_brain", task_id, "quick_create_task", action_type)
    return {"ok": True, "kind": "task", "message": f"Tarefa criada para acompanhamento: #{task_id}."}


def executive_state_label(insights: list[dict]) -> tuple[str, str]:
    severities = [item.get("severity") for item in insights]
    if "critical" in severities:
        return "Atenção crítica", "Existem pontos que precisam de ação antes da operação."
    if "warning" in severities:
        return "Monitoramento ativo", "O evento está operacional, mas ainda há recomendações importantes."
    return "Operação saudável", "Não há bloqueios relevantes neste momento."
