from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from repositories.database import (
    audit_log,
    create_proactive_action,
    get_live_dashboard_data,
    get_rsvp,
    list_guest_profiles,
    list_tables,
    load_guests_df,
)
from services.table_validation_service import validate_tables


@dataclass(frozen=True)
class BrainInsight:
    severity: str
    title: str
    message: str
    recommendation: str
    action_type: str = "operational_review"

    def as_dict(self) -> dict:
        return {
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "recommendation": self.recommendation,
            "action_type": self.action_type,
        }


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def analyze_event(event_id: int) -> list[dict]:
    """Analisa o evento ativo e devolve recomendações legíveis.

    A função não usa consulta global: todos os dados são carregados com event_id.
    """
    guests = load_guests_df(event_id)
    rsvp = get_rsvp(event_id)
    validations = validate_tables(event_id)
    live = get_live_dashboard_data(event_id)
    profiles = list_guest_profiles(event_id)
    tables = list_tables(event_id)

    insights: list[BrainInsight] = []
    total = len(guests)
    if total == 0:
        return [BrainInsight("info", "Evento sem convidados", "Ainda não há convidados importados/cadastrados neste evento.", "Importe um PDF ou cadastre convidados antes de rodar a operação.").as_dict()]

    confirmed = int((rsvp["status"] == "confirmed").sum()) if not rsvp.empty and "status" in rsvp else 0
    pending = int((rsvp["status"] == "pending").sum()) if not rsvp.empty and "status" in rsvp else total
    confirmation_rate = confirmed / total if total else 0
    if confirmation_rate < 0.35:
        insights.append(BrainInsight(
            "critical",
            "Baixa taxa de confirmação",
            f"Apenas {_pct(confirmation_rate)} dos convidados estão confirmados. Isso aumenta risco de mesas vazias e incerteza operacional.",
            "Dispare uma mensagem de confirmação com link do Portal do Convidado para pendentes.",
            "send_rsvp_reminder",
        ))
    elif confirmation_rate < 0.65:
        insights.append(BrainInsight(
            "warning",
            "Confirmação ainda em evolução",
            f"A taxa de confirmação está em {_pct(confirmation_rate)}. O evento ainda precisa de acompanhamento ativo.",
            "Priorize convidados pendentes de grupos grandes e sem telefone validado.",
            "prioritize_followup",
        ))

    without_table = int(guests["mesa_final"].fillna("").astype(str).str.strip().eq("").sum()) if "mesa_final" in guests else total
    if without_table:
        insights.append(BrainInsight(
            "warning" if without_table < total * 0.25 else "critical",
            "Convidados sem mesa",
            f"Há {without_table} convidado(s) sem mesa definida no evento ativo.",
            "Use Sugestões para preencher mesas respeitando grupos e capacidade.",
            "generate_seating_suggestions",
        ))

    critical_conflicts = 0
    if validations is not None and not validations.empty and "severidade" in validations:
        critical_conflicts = int((validations["severidade"] == "critical").sum())
        warnings = int((validations["severidade"] == "warning").sum())
        if critical_conflicts:
            insights.append(BrainInsight(
                "critical",
                "Conflitos críticos em mesas",
                f"Foram detectados {critical_conflicts} conflito(s) crítico(s) na distribuição de mesas.",
                "Abra Validação e corrija lotação, duplicidades ou mesas inválidas antes do evento.",
                "review_table_conflicts",
            ))
        elif warnings:
            insights.append(BrainInsight(
                "warning",
                "Ajustes recomendados em mesas",
                f"Foram encontrados {warnings} alerta(s) de mesa que podem afetar a operação.",
                "Revise grupos separados, mesas vazias e convidados sem mesa.",
                "review_table_warnings",
            ))

    if live.get("presence_rate", 0) > 0 and live.get("presence_rate", 0) < 0.45:
        insights.append(BrainInsight(
            "warning",
            "Presença abaixo do esperado no check-in",
            f"O check-in atual registra {_pct(float(live.get('presence_rate', 0)))} de presença.",
            "No Command Center, acione convidados confirmados ainda sem check-in.",
            "checkin_followup",
        ))

    if not profiles.empty and "behavioral_type" in profiles:
        at_risk = int((profiles["behavioral_type"] == "at_risk").sum())
        if at_risk:
            insights.append(BrainInsight(
                "warning",
                "Convidados com risco de não resposta",
                f"O perfil inteligente marcou {at_risk} convidado(s) como alto risco de falta ou silêncio.",
                "Filtre esses convidados no Benchmarking/Perfis e faça abordagem personalizada.",
                "profile_followup",
            ))

    if tables.empty:
        insights.append(BrainInsight("info", "Mesas ainda não estruturadas", "Nenhuma mesa foi cadastrada para este evento.", "Cadastre mesas com capacidade antes de aplicar sugestões.", "create_tables"))

    if not insights:
        insights.append(BrainInsight("info", "Operação saudável", "Não há alertas relevantes no momento. O evento está com boa consistência operacional.", "Continue monitorando RSVP, mensagens e check-in no Command Center.", "monitor"))
    return [item.as_dict() for item in insights]


def summarize_event(event_id: int) -> dict:
    guests = load_guests_df(event_id)
    rsvp = get_rsvp(event_id)
    live = get_live_dashboard_data(event_id)
    total = len(guests)
    confirmed = int((rsvp["status"] == "confirmed").sum()) if not rsvp.empty and "status" in rsvp else 0
    pending = int((rsvp["status"] == "pending").sum()) if not rsvp.empty and "status" in rsvp else total
    insights = analyze_event(event_id)
    top = insights[0]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_guests": total,
        "confirmed": confirmed,
        "pending": pending,
        "presence_rate": live.get("presence_rate", 0),
        "main_status": top.get("severity"),
        "main_insight": top.get("message"),
        "main_recommendation": top.get("recommendation"),
        "insights": insights,
    }


def create_proactive_suggestions(event_id: int) -> pd.DataFrame:
    rows = []
    for insight in analyze_event(event_id):
        if insight["severity"] in {"warning", "critical"}:
            priority = "critical" if insight["severity"] == "critical" else "high"
            action_id = create_proactive_action(
                event_id,
                insight.get("action_type", "event_brain"),
                priority,
                insight["title"],
                f"{insight['message']} Recomendação: {insight['recommendation']}",
                payload_json=str(insight),
            )
            audit_log(event_id, "event_brain", action_id, "proactive_suggestion", insight["title"])
            rows.append({"id": action_id, **insight, "priority": priority})
    return pd.DataFrame(rows)
