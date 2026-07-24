from __future__ import annotations

from services.global_memory_service import get_global_memory_summary, snapshot_event_to_global_memory
from services.insight_service import generate_event_insights
from repositories.database import create_intelligent_insight, get_event_profile


def compare_event_with_history(event_id: int, persist: bool = False) -> dict:
    current = snapshot_event_to_global_memory(event_id, source="benchmarking")
    memory = get_global_memory_summary(event_id)
    benchmarks = memory.get("benchmarks", {})
    insights: list[dict] = []
    if not benchmarks:
        insights.append({
            "severity": "info",
            "title": "Base histórica ainda pequena",
            "message": "Este evento já foi salvo na memória global. O benchmarking ficará mais forte conforme novos eventos forem finalizados.",
            "action_suggestion": "Use esta versão como linha de base para os próximos eventos.",
        })
    else:
        comparisons = [
            ("confirmation_rate", "Taxa de confirmação", "p.p."),
            ("presence_rate", "Taxa de presença", "p.p."),
            ("table_efficiency", "Eficiência das mesas", "p.p."),
        ]
        for key, label, _ in comparisons:
            delta = float(current.get(key, 0)) - float(benchmarks.get(key, 0))
            if delta <= -0.10:
                insights.append({"severity": "warning", "title": f"{label} abaixo do histórico", "message": f"{label} está {abs(delta)*100:.1f} pontos percentuais abaixo da média dos eventos anteriores.", "action_suggestion": "Priorize automações proativas e validação operacional."})
            elif delta >= 0.10:
                insights.append({"severity": "info", "title": f"{label} acima do histórico", "message": f"{label} está {delta*100:.1f} pontos percentuais acima da média histórica.", "action_suggestion": "Registre este padrão como referência para próximos eventos."})
        conflict_delta = int(current.get("critical_conflicts", 0)) - float(benchmarks.get("critical_conflicts", 0))
        if conflict_delta > 0:
            insights.append({"severity": "critical", "title": "Conflitos acima da média", "message": f"O evento atual possui mais conflitos críticos que a média histórica ({conflict_delta:.1f} acima).", "action_suggestion": "Abrir Validação e Sugestões antes de disparar mensagens finais."})
    if persist:
        for item in insights:
            create_intelligent_insight(event_id, item["severity"], item["title"], item["message"], item["action_suggestion"])
    return {"current": current, "memory": memory, "insights": insights, "event_profile": get_event_profile(event_id), "raw_metrics": generate_event_insights(event_id)}
