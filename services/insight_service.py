from __future__ import annotations

import pandas as pd

from repositories.database import get_rsvp, get_checkins, list_tables, load_guests_df, count_critical_table_conflicts


def generate_event_insights(event_id: int) -> dict:
    guests = load_guests_df(event_id)
    rsvp = get_rsvp(event_id)
    checkins = get_checkins(event_id)
    tables = list_tables(event_id)
    total = len(guests)
    confirmed = int((rsvp["status"] == "confirmed").sum()) if not rsvp.empty else 0
    declined = int((rsvp["status"] == "declined").sum()) if not rsvp.empty else 0
    present = int(checkins["checked_in"].fillna(0).astype(int).sum()) if not checkins.empty else 0
    with_table = int(guests["mesa_final"].fillna("").astype(str).ne("").sum()) if not guests.empty else 0
    total_capacity = int(tables["capacity"].fillna(0).astype(int).sum()) if not tables.empty and "capacity" in tables else 0
    group_distribution = pd.DataFrame()
    if not guests.empty:
        group_distribution = guests.groupby("grupo", dropna=False).size().reset_index(name="convidados").sort_values("convidados", ascending=False)
    return {
        "total_guests": total,
        "confirmation_rate": confirmed / total if total else 0,
        "decline_rate": declined / total if total else 0,
        "presence_rate": present / total if total else 0,
        "table_efficiency": with_table / total_capacity if total_capacity else 0,
        "with_table": with_table,
        "without_table": total - with_table,
        "critical_conflicts": count_critical_table_conflicts(event_id),
        "group_distribution": group_distribution,
    }


def generate_interpretive_insights(event_id: int, persist: bool = False) -> list[dict]:
    """Gera leituras executivas em português simples para apoiar decisão operacional."""
    from repositories.database import create_intelligent_insight, get_event_profile

    metrics = generate_event_insights(event_id)
    profile = get_event_profile(event_id)
    total = metrics.get("total_guests", 0)
    confirmation = metrics.get("confirmation_rate", 0)
    presence = metrics.get("presence_rate", 0)
    without_table = metrics.get("without_table", 0)
    critical = metrics.get("critical_conflicts", 0)
    risk = profile.get("operational_risk", "low") if profile else "low"

    insights: list[dict] = []
    if total == 0:
        insights.append({
            "severity": "info",
            "title": "Evento sem base operacional",
            "message": "Ainda não há convidados cadastrados para gerar leitura inteligente.",
            "action_suggestion": "Importe um PDF ou cadastre convidados manualmente.",
        })
    else:
        if confirmation < 0.40:
            insights.append({
                "severity": "critical",
                "title": "Confirmação muito baixa",
                "message": f"Seu evento está abaixo da média de confirmação esperada: apenas {confirmation:.1%} dos convidados estão confirmados.",
                "action_suggestion": "Enviar lembrete segmentado para convidados com RSVP pendente.",
            })
        elif confirmation < 0.65:
            insights.append({
                "severity": "warning",
                "title": "Confirmação precisa de atenção",
                "message": f"A taxa de confirmação está em {confirmation:.1%}. Ainda há espaço para recuperar pendências antes do evento.",
                "action_suggestion": "Rodar automação de lembrete e priorizar grupos sem confirmação.",
            })
        else:
            insights.append({
                "severity": "info",
                "title": "Confirmação saudável",
                "message": f"A taxa de confirmação está em {confirmation:.1%}, indicando boa previsibilidade operacional.",
                "action_suggestion": "Foque em check-in, cronograma e validação final das mesas.",
            })

        if without_table > 0:
            insights.append({
                "severity": "warning" if without_table < max(3, total * 0.10) else "critical",
                "title": "Convidados sem mesa",
                "message": f"Existem {without_table} convidado(s) sem mesa definida. Isso pode afetar a operação no dia do evento.",
                "action_suggestion": "Use o motor de sugestões e valide grupos antes de aplicar.",
            })
        if critical:
            insights.append({
                "severity": "critical",
                "title": "Conflitos críticos detectados",
                "message": f"Foram encontrados {critical} conflito(s) crítico(s) na distribuição de mesas.",
                "action_suggestion": "Abra Validação e corrija os pontos críticos antes do envio final.",
            })
        if presence and presence < 0.50 and confirmation >= 0.60:
            insights.append({
                "severity": "warning",
                "title": "Presença abaixo das confirmações",
                "message": f"A presença registrada está em {presence:.1%}, abaixo do nível esperado para o volume confirmado.",
                "action_suggestion": "Monitore check-ins faltantes no Command Center e acione a equipe de recepção.",
            })
        if risk in {"high", "critical"}:
            insights.append({
                "severity": "critical" if risk == "critical" else "warning",
                "title": "Risco operacional elevado",
                "message": f"O perfil adaptativo classificou este evento como risco {risk}.",
                "action_suggestion": "Priorize pendências de RSVP, mesas e tarefas críticas.",
            })

    if persist:
        for item in insights:
            create_intelligent_insight(event_id, item["severity"], item["title"], item["message"], item["action_suggestion"])
    return insights
