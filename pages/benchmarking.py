import streamlit as st

from components.layout import card_close, card_open, header
from pages.common import active_event_id, active_event_label
from repositories.database import (
    list_global_event_insights,
    list_guest_profiles,
    list_proactive_actions,
    update_proactive_action_status,
)
from services.benchmarking_service import compare_event_with_history
from services.global_memory_service import snapshot_event_to_global_memory, get_global_memory_summary
from services.guest_profile_service import rebuild_guest_profiles
from services.proactive_automation_service import suggest_proactive_actions


def _show_df(df, empty_msg: str):
    if df is None or df.empty:
        st.info(empty_msg)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


def render():
    event_id = active_event_id()
    header("Benchmarking & Memória Global", f"Aprendizado entre eventos e ações proativas: {active_event_label()}")

    c1, c2, c3 = st.columns(3)
    if c1.button("Salvar snapshot na memória", type="primary"):
        snapshot_event_to_global_memory(event_id, source="manual")
        st.success("Snapshot salvo na memória global.")
        st.rerun()
    if c2.button("Recalcular perfis de convidados"):
        profiles = rebuild_guest_profiles(event_id)
        st.success(f"{len(profiles)} perfil(is) atualizado(s).")
        st.rerun()
    if c3.button("Gerar ações proativas"):
        result = suggest_proactive_actions(event_id)
        st.success(f"{len(result['created_or_existing_ids'])} ação(ões) sugerida(s) ou já existentes.")
        st.rerun()

    summary = get_global_memory_summary(event_id)
    benchmarks = summary.get("benchmarks", {})
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Eventos históricos", summary.get("events_count", 0))
    k2.metric("Confirmação hist.", f"{benchmarks.get('confirmation_rate', 0) * 100:.1f}%")
    k3.metric("Presença hist.", f"{benchmarks.get('presence_rate', 0) * 100:.1f}%")
    k4.metric("Eficiência mesas hist.", f"{benchmarks.get('table_efficiency', 0) * 100:.1f}%")

    tab1, tab2, tab3, tab4 = st.tabs(["Comparativo", "Memória global", "Perfis", "Ações proativas"])

    with tab1:
        card_open("Insights comparativos")
        persist = st.toggle("Persistir insights gerados", value=False)
        result = compare_event_with_history(event_id, persist=persist)
        st.write("Métricas do evento atual")
        st.json(result.get("current", {}))
        insights = result.get("insights", [])
        if not insights:
            st.info("Nenhum desvio relevante encontrado no benchmarking.")
        for item in insights:
            severity = item.get("severity", "info")
            text = f"**{item.get('title')}** — {item.get('message')}\n\nAção sugerida: {item.get('action_suggestion', '')}"
            if severity == "critical":
                st.error(text)
            elif severity == "warning":
                st.warning(text)
            else:
                st.info(text)
        card_close()

    with tab2:
        card_open("Base histórica de eventos")
        _show_df(list_global_event_insights(limit=500), "Ainda não há memória global salva.")
        card_close()

    with tab3:
        card_open("Perfil comportamental dos convidados")
        profiles = list_guest_profiles(event_id)
        if not profiles.empty:
            f1, f2 = st.columns(2)
            behavior = f1.selectbox("Tipo comportamental", ["Todos"] + sorted(profiles["behavioral_type"].dropna().unique().tolist()))
            pattern = f2.selectbox("Padrão de presença", ["Todos"] + sorted(profiles["attendance_pattern"].dropna().unique().tolist()))
            if behavior != "Todos":
                profiles = profiles[profiles["behavioral_type"] == behavior]
            if pattern != "Todos":
                profiles = profiles[profiles["attendance_pattern"] == pattern]
        _show_df(profiles, "Nenhum perfil calculado. Clique em Recalcular perfis de convidados.")
        card_close()

    with tab4:
        card_open("Ações sugeridas automaticamente")
        actions = list_proactive_actions(event_id)
        if actions.empty:
            st.info("Nenhuma ação proativa sugerida ainda.")
        else:
            _show_df(actions, "")
            options = {f"#{int(r.id)} · {r.priority} · {r.title}": int(r.id) for r in actions.itertuples()}
            selected = st.selectbox("Atualizar ação", list(options.keys()))
            new_status = st.selectbox("Novo status", ["suggested", "accepted", "dismissed", "done"])
            if st.button("Salvar status da ação"):
                update_proactive_action_status(event_id, options[selected], new_status)
                st.success("Status atualizado.")
                st.rerun()
        card_close()
