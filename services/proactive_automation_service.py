from __future__ import annotations

import json

from repositories.database import create_proactive_action, list_proactive_actions
from services.benchmarking_service import compare_event_with_history
from services.insight_service import generate_event_insights


def suggest_proactive_actions(event_id: int) -> dict:
    metrics = generate_event_insights(event_id)
    benchmark = compare_event_with_history(event_id, persist=False)
    created = []

    if metrics.get("confirmation_rate", 0) < 0.60 and metrics.get("total_guests", 0) > 0:
        created.append(create_proactive_action(
            event_id, "send_rsvp_reminder", "high", "Enviar lembrete para RSVP pendente",
            "A confirmação está abaixo do ideal. Gere mensagens inteligentes para convidados pendentes.",
            json.dumps({"target_status": "pending"}, ensure_ascii=False),
        ))
    if metrics.get("without_table", 0) > 0:
        created.append(create_proactive_action(
            event_id, "generate_seating_suggestions", "critical" if metrics.get("without_table", 0) > 5 else "high",
            "Gerar sugestões para convidados sem mesa",
            f"Existem {metrics.get('without_table', 0)} convidado(s) sem mesa definida.",
            json.dumps({"without_table": metrics.get("without_table", 0)}, ensure_ascii=False),
        ))
    if metrics.get("critical_conflicts", 0) > 0:
        created.append(create_proactive_action(
            event_id, "resolve_table_conflicts", "critical", "Resolver conflitos críticos de mesas",
            "O motor de validação detectou conflitos críticos que podem afetar a operação.",
            json.dumps({"critical_conflicts": metrics.get("critical_conflicts", 0)}, ensure_ascii=False),
        ))
    for item in benchmark.get("insights", []):
        if item.get("severity") in {"warning", "critical"}:
            created.append(create_proactive_action(
                event_id, "benchmark_response", "high" if item["severity"] == "warning" else "critical",
                item["title"], item["message"], json.dumps(item, ensure_ascii=False),
            ))
    return {"created_or_existing_ids": created, "actions": list_proactive_actions(event_id), "benchmark": benchmark}
