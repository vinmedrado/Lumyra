import pandas as pd
import streamlit as st

from components.layout import card_close, card_open, header
from components.ui import empty_state, info_banner, insight_card, metric_card, progress_card, section_header
from pages.common import active_event_id, active_event_label, guests_df
from repositories.database import (
    get_event_profile,
    get_live_dashboard_data,
    list_adaptive_weights,
    list_intelligent_insights,
    list_messages,
    list_orchestrator_decisions,
    set_checkin,
    update_guest_table,
)
from services.adaptive_engine import get_learning_summary, update_scores_from_real_data
from services.event_brain import analyze_event, create_proactive_suggestions, summarize_event
from services.orchestrator import get_command_center_alerts, run_orchestrator
from services.quick_action_service import execute_quick_action, get_action_label
from services.whatsapp_service import build_queue_from_guests


def _show_df(df, empty_msg: str):
    if df is None or df.empty:
        empty_state(empty_msg, "Quando houver dados, eles aparecerão aqui com filtros e histórico.", "✨")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


def _render_insight_actions(event_id: int, insights: list[dict]) -> None:
    for idx, insight in enumerate(insights[:5]):
        severity = insight.get("severity", "info")
        insight_card(
            insight.get("title", "Insight"),
            insight.get("message", ""),
            severity,
            insight.get("recommendation", ""),
        )
        if st.button(get_action_label(insight.get("action_type", "")), key=f"cc_insight_action_{idx}"):
            result = execute_quick_action(event_id, insight)
            st.success(result.get("message", "Ação executada."))
            st.rerun()


def render():
    event_id = active_event_id()
    header("Command Center", f"Central operacional inteligente: {active_event_label()}")

    data = get_live_dashboard_data(event_id)
    profile = get_event_profile(event_id)
    brain = summarize_event(event_id)
    insights = analyze_event(event_id)
    section_header("Operação ao vivo", "Indicadores rápidos para decisões durante o evento.", "🎛️")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1_col = c1
    with c1_col: metric_card("Esperados", data.get("total_guests", 0), "convidados", "👥", "premium")
    with c2: metric_card("Presentes", data.get("present", 0), "check-ins", "🎟️", "success")
    with c3: metric_card("Presença", f"{data.get('presence_rate', 0) * 100:.1f}%", "ao vivo", "📡", "info")
    with c4: metric_card("Risco", profile.get("operational_risk", "low") if profile else brain.get("main_status", "info"), "operacional", "⚠️", "warning")
    with c5: metric_card("Pendentes", len(list_messages(event_id, "pending")), "mensagens", "💬", "warning")

    info_banner("Event Brain ao vivo", f"{brain.get('main_insight')} Recomendação: {brain.get('main_recommendation')}", "premium", "🧠")

    left, right = st.columns([1.1, 1])
    with left:
        section_header("Ações rápidas", "Atalhos úteis para resolver pendências sem sair do Command Center.", "⚡")
        card_open("Enviar mensagem e gerar ações")
        template = st.text_area("Mensagem rápida com portal", "Olá {nome}! Confirme ou atualize seus dados do evento por aqui: {guest_link}", height=80)
        df = guests_df()
        only_no_table = st.checkbox("Enviar apenas para convidados sem mesa", value=False)
        if only_no_table and not df.empty:
            df = df[df["mesa_final"].fillna("").astype(str).str.strip().eq("")]
        cta1, cta2, cta3 = st.columns(3)
        if cta1.button("Enfileirar mensagem", type="primary"):
            count = build_queue_from_guests(df, template, event_id=event_id)
            st.success(f"{count} mensagem(ns) enfileirada(s), respeitando anti-duplicidade.")
            st.rerun()
        if cta2.button("Gerar ações proativas"):
            actions = create_proactive_suggestions(event_id)
            _show_df(actions, "Nenhuma ação proativa necessária agora.")
        if cta3.button("Atualizar perfis"):
            result = update_scores_from_real_data(event_id)
            st.success(result.notes)
            st.rerun()
        card_close()

        card_open("Ajuste rápido de operação")
        guests = guests_df()
        if guests.empty:
            st.info("Cadastre convidados para usar ações rápidas.")
        else:
            options = {f"#{int(r.id)} · {r.nome_original or r.nome}": int(r.id) for r in guests.itertuples()}
            selected = st.selectbox("Convidado", list(options.keys()))
            q1, q2 = st.columns(2)
            if q1.button("Marcar presença"):
                set_checkin(event_id, options[selected], True, notes="Ação rápida Command Center")
                st.success("Check-in registrado.")
                st.rerun()
            new_table = q2.text_input("Mover para mesa")
            if st.button("Ajustar mesa selecionada") and new_table.strip():
                update_guest_table(event_id, options[selected], new_table.strip(), "ajuste_command_center")
                st.success("Mesa ajustada.")
                st.rerun()
        card_close()

        card_open("Orquestrador central")
        dry_run = st.toggle("Modo simulação", value=True)
        if st.button("Executar orquestrador"):
            result = run_orchestrator(event_id, dry_run=dry_run)
            st.success("Orquestrador executado em modo simulação." if dry_run else "Orquestrador executado e ações registradas.")
            _show_df(result.get("automation_results"), "Nenhuma automação processada.")
        card_close()

    with right:
        card_open("Insights acionáveis")
        _render_insight_actions(event_id, insights)
        card_close()
        card_open("Alertas ativos")
        _show_df(get_command_center_alerts(event_id), "Nenhum alerta crítico no momento.")
        card_close()

    tab1, tab2, tab3, tab4 = st.tabs(["Insights persistidos", "Perfil do evento", "Pesos", "Histórico"])
    with tab1:
        _show_df(list_intelligent_insights(event_id, 50), "Ainda não há insights persistidos.")
    with tab2:
        st.json(profile or brain)
        st.metric("Convidados de alta prioridade", get_learning_summary(event_id).get("high_priority", 0))
    with tab3:
        _show_df(list_adaptive_weights(event_id), "Pesos ainda não calculados.")
    with tab4:
        _show_df(list_orchestrator_decisions(event_id, 100), "Sem histórico de decisões.")
