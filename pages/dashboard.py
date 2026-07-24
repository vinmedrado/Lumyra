import streamlit as st

from components.layout import card_close, card_open, header
from components.ui import action_card, empty_state, info_banner, insight_card, metric_card, progress_card, section_header
from repositories.database import campaign_dashboard_metrics, count_critical_table_conflicts, get_checkins, get_rsvp, list_messages, list_tasks, list_timeline
from services.assessoria_service import context_exists
from services.event_brain import analyze_event
from services.quick_action_service import execute_quick_action, executive_state_label, get_action_label
from pages.common import active_event_id, active_event_label, guests_df


def _brain_card(event_id: int, insight: dict, idx: int) -> None:
    insight_card(
        insight.get("title", "Insight"),
        insight.get("message", ""),
        insight.get("severity", "info"),
        insight.get("recommendation", ""),
    )
    if st.button(get_action_label(insight.get("action_type", "")), key=f"dash_brain_action_{idx}"):
        result = execute_quick_action(event_id, insight)
        st.success(result.get("message", "Ação registrada."))
        st.rerun()


def render():
    event_id = active_event_id()
    df = guests_df()
    header("Dashboard Executivo", f"Visão clara, visual e acionável do evento ativo: {active_event_label()}")

    total = len(df)
    com_mesa = int(df["mesa_final"].fillna("").astype(str).ne("").sum()) if not df.empty and "mesa_final" in df.columns else 0
    sem_mesa = total - com_mesa
    sent = list_messages(event_id, "sent")
    rsvp = get_rsvp(event_id)
    checkins = get_checkins(event_id)
    tasks = list_tasks(event_id)
    timeline = list_timeline(event_id)
    confirmados = int((rsvp["status"] == "confirmed").sum()) if not rsvp.empty else 0
    presentes = int(checkins["checked_in"].fillna(0).astype(int).sum()) if not checkins.empty else 0
    tarefas_pendentes = int(tasks[~tasks["status"].isin(["done", "canceled"])].shape[0]) if not tasks.empty else 0
    atrasados = int((timeline["status"] == "delayed").sum()) if not timeline.empty else 0
    criticos = count_critical_table_conflicts(event_id)
    crm_metrics = campaign_dashboard_metrics(event_id)
    insights = analyze_event(event_id)
    state_title, state_text = executive_state_label(insights)
    progress = confirmados / max(total, 1)

    info_banner(state_title, state_text, "premium" if not criticos else "warning", "🎛️")

    section_header("Indicadores principais", "Resumo operacional sem precisar abrir relatórios técnicos.", "📊")
    cols = st.columns(4)
    card_defs = [
        ("Convidados", total, "total importado", "👥", "premium"),
        ("Confirmados", confirmados, f"{progress:.0%} da lista", "✅", "success"),
        ("Sem mesa", sem_mesa, "precisam de atenção", "🪑", "warning" if sem_mesa else "success"),
        ("Conflitos", criticos, "validação de mesas", "🚨", "danger" if criticos else "success"),
        ("Mensagens", 0 if sent.empty else len(sent), "enviadas", "💬", "info"),
        ("Campanhas", crm_metrics["campaigns"], "criadas", "📣", "info"),
        ("Erros campanha", crm_metrics["errors"], "precisam revisão", "⚠️", "danger" if crm_metrics["errors"] else "success"),
        ("Tarefas", tarefas_pendentes, "em aberto", "📌", "warning" if tarefas_pendentes else "success"),
    ]
    for idx, item in enumerate(card_defs):
        with cols[idx % 4]:
            metric_card(*item)

    progress_card("Progresso de confirmação", progress, f"{confirmados} de {total} convidados confirmados.", "💍")

    section_header("Próximos passos operacionais", "Fluxo guiado para manter o evento evoluindo.", "🧭")
    s1, s2 = st.columns(2)
    with s1:
        action_card("PASSO 1", "Importar convidados", "Base inicial necessária para RSVP, mesas e mensagens.", done=total > 0, icon="⬆️")
        action_card("PASSO 2", "Validar contatos", "Reduz falhas nos disparos de WhatsApp.", done=crm_metrics.get("invalid_contacts", 0) == 0, icon="📇")
        action_card("PASSO 3", "Criar formulário", "Substitui Google Forms com respostas dentro do sistema.", done=True, icon="📝")
    with s2:
        action_card("PASSO 4", "Enviar mensagens", "Convites, lembretes e links do portal.", done=(0 if sent.empty else len(sent)) > 0, icon="💬")
        action_card("PASSO 5", "Organizar mesas", "Evita convidados sem mesa ou acima da capacidade.", done=sem_mesa == 0 and criticos == 0, icon="🪑")
        action_card("PASSO 6", "Acompanhar insights", "Alertas automáticos para decisões rápidas.", done=bool(insights), icon="🧠")

    left_top, right_top = st.columns([1.2, 1])
    with left_top:
        section_header("Insights destacados", "Recomendações acionáveis do Event Brain.", "🧠")
        if not insights:
            empty_state("Nenhum insight gerado", "Quando houver pendências, riscos ou oportunidades, elas aparecerão aqui.", "✨")
        for idx, insight in enumerate(insights[:4]):
            _brain_card(event_id, insight, idx)
    with right_top:
        card_open("Status operacional")
        assessoria_status = (
            "<span class='badge badge-ok'>conectada</span>"
            if context_exists()
            else "<span class='badge badge-warn'>pendente</span>"
        )
        st.markdown(f"Assessoria VIP: {assessoria_status}", unsafe_allow_html=True)
        st.markdown("SQLite: <span class='badge badge-ok'>ativo</span>", unsafe_allow_html=True)
        st.markdown("Multi-evento: <span class='badge badge-ok'>filtrado por event_id</span>", unsafe_allow_html=True)
        st.markdown("WhatsApp: <span class='badge badge-warn'>depende do .env</span>", unsafe_allow_html=True)
        card_close()

    c1, c2 = st.columns([1.4, 1])
    with c1:
        card_open("Ocupação por mesa")
        if df.empty:
            empty_state("Nenhum convidado cadastrado ainda", "Importe sua lista para visualizar a ocupação das mesas.", "🪑")
        else:
            ocup = df[df["mesa_final"].fillna("").astype(str).ne("")].groupby("mesa_final").size().reset_index(name="convidados")
            if ocup.empty:
                empty_state("Nenhuma mesa definida", "Assim que as mesas forem preenchidas, o gráfico aparecerá aqui.", "🪑")
            else:
                st.bar_chart(ocup.set_index("mesa_final"))
        card_close()
    with c2:
        card_open("Alertas executivos")
        if not insights:
            empty_state("Sem alertas no momento", "O sistema está pronto para monitorar novas pendências.", "✅")
        else:
            for ins in insights[:5]:
                insight_card(ins.get("title"), ins.get("message"), ins.get("severity", "info"), ins.get("action", ins.get("recommendation", "")), ins.get("count"))
        card_close()

    c3, c4 = st.columns(2)
    with c3:
        card_open("Tarefas críticas/altas")
        if tasks.empty:
            empty_state("Nenhuma tarefa cadastrada", "Crie tarefas para organizar responsabilidades do evento.", "📌")
        else:
            show = tasks[tasks["priority"].isin(["critical", "high"]) & ~tasks["status"].isin(["done", "canceled"])]
            if show.empty:
                empty_state("Sem tarefas críticas", "Nenhuma tarefa de alta prioridade em aberto.", "✅")
            else:
                st.dataframe(show[["title", "priority", "status", "due_date", "owner"]], use_container_width=True, hide_index=True)
        card_close()
    with c4:
        card_open("Cronograma em atraso")
        if timeline.empty:
            empty_state("Nenhum item de cronograma", "Cadastre etapas para acompanhar o planejamento.", "🗓️")
        else:
            show = timeline[timeline["status"] == "delayed"]
            if show.empty:
                empty_state("Cronograma em dia", "Nenhuma etapa atrasada no momento.", "✅")
            else:
                st.dataframe(show[["time", "title", "owner", "status"]], use_container_width=True, hide_index=True)
        card_close()
