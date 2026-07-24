from __future__ import annotations

import pandas as pd

from repositories.database import (
    audit_log,
    create_intelligent_insight,
    create_task,
    get_event_profile,
    list_intelligent_insights,
    list_orchestrator_decisions,
    record_orchestrator_decision,
)
from services.adaptive_engine import update_scores_from_real_data
from services.automation_service import execute_enabled_rules
from services.insight_service import generate_event_insights, generate_interpretive_insights
from services.table_validation_service import validate_tables
from services.benchmarking_service import compare_event_with_history
from services.guest_profile_service import rebuild_guest_profiles
from services.proactive_automation_service import suggest_proactive_actions


def run_orchestrator(event_id: int, dry_run: bool = True) -> dict:
    """Orquestra aprendizado, insights, validações e regras do evento ativo."""
    decisions: list[dict] = []
    status = "dry_run" if dry_run else "executed"

    adaptive = update_scores_from_real_data(event_id)
    summary = f"Motor adaptativo atualizou {adaptive.updated_scores} score(s). Risco operacional: {adaptive.risk_level}."
    record_orchestrator_decision(event_id, "adaptive_engine", status, summary, adaptive.notes)
    decisions.append({"type": "adaptive_engine", "status": status, "summary": summary})

    insights = generate_interpretive_insights(event_id, persist=not dry_run)
    summary = f"{len(insights)} insight(s) interpretativo(s) gerado(s)."
    record_orchestrator_decision(event_id, "insights", status, summary, str(insights))
    decisions.append({"type": "insights", "status": status, "summary": summary})

    conflicts = validate_tables(event_id)
    critical = [c for c in conflicts if c.get("severity") == "critical"]
    if critical:
        details = f"{len(critical)} conflito(s) crítico(s) detectado(s) nas mesas."
        if not dry_run:
            create_intelligent_insight(
                event_id,
                "critical",
                "Conflitos críticos de mesas",
                details,
                "Abra a página Validação e resolva os conflitos antes do evento.",
            )
            create_task(
                event_id,
                "Resolver conflitos críticos de mesas",
                details,
                priority="critical",
                owner="Assessoria",
            )
        record_orchestrator_decision(event_id, "table_validation", status, details, str(critical[:5]))
        decisions.append({"type": "table_validation", "status": status, "summary": details})

    automation = execute_enabled_rules(event_id, dry_run=dry_run)
    processed = int(automation["processed_count"].sum()) if not automation.empty and "processed_count" in automation else 0
    summary = f"Automações processaram {processed} item(ns)."
    record_orchestrator_decision(event_id, "automation_rules", status, summary, automation.to_json(orient="records", force_ascii=False) if not automation.empty else "[]")
    decisions.append({"type": "automation_rules", "status": status, "summary": summary})

    profiles = rebuild_guest_profiles(event_id)
    summary = f"Perfil comportamental atualizado para {len(profiles)} convidado(s)."
    record_orchestrator_decision(event_id, "guest_profile", status, summary, "")
    decisions.append({"type": "guest_profile", "status": status, "summary": summary})

    benchmark = compare_event_with_history(event_id, persist=not dry_run)
    summary = f"Benchmarking comparou o evento com {benchmark.get('memory', {}).get('events_count', 0)} evento(s) histórico(s)."
    record_orchestrator_decision(event_id, "benchmarking", status, summary, str(benchmark.get("insights", [])))
    decisions.append({"type": "benchmarking", "status": status, "summary": summary})

    proactive = suggest_proactive_actions(event_id) if not dry_run else {"created_or_existing_ids": [], "actions": None}
    summary = f"{len(proactive.get('created_or_existing_ids', []))} ação(ões) proativa(s) sugerida(s)."
    record_orchestrator_decision(event_id, "proactive_actions", status, summary, "")
    decisions.append({"type": "proactive_actions", "status": status, "summary": summary})

    profile = get_event_profile(event_id)
    audit_log(event_id, "orchestrator", None, "run", f"dry_run={dry_run}; decisions={len(decisions)}")
    return {
        "status": status,
        "decisions": decisions,
        "profile": profile,
        "automation_results": automation,
        "latest_insights": list_intelligent_insights(event_id, 10),
        "history": list_orchestrator_decisions(event_id, 20),
    }


def get_command_center_alerts(event_id: int) -> pd.DataFrame:
    insights = generate_event_insights(event_id)
    alerts = []
    if insights.get("critical_conflicts", 0) > 0:
        alerts.append({"severity": "critical", "alert": "Existem conflitos críticos de mesas.", "action": "Abrir Validação"})
    if insights.get("confirmation_rate", 0) < 0.55 and insights.get("total_guests", 0) > 0:
        alerts.append({"severity": "warning", "alert": "Taxa de confirmação abaixo do ideal.", "action": "Enviar lembrete para RSVP pendente"})
    if insights.get("without_table", 0) > 0:
        alerts.append({"severity": "warning", "alert": f"{insights['without_table']} convidado(s) sem mesa.", "action": "Gerar sugestões de distribuição"})
    if insights.get("presence_rate", 0) >= 0.80:
        alerts.append({"severity": "info", "alert": "Presença alta registrada no check-in.", "action": "Monitorar capacidade das mesas"})
    return pd.DataFrame(alerts)
