import streamlit as st

from components.layout import card_close, card_open, header
from pages.common import active_event_id, active_event_label, guests_df
from repositories.database import list_guest_scores, audit_log
from services.message_ai_service import gerar_mensagem_automatica, gerar_template_dinamico, gerar_lote_por_rsvp
from services.score_service import recalculate_scores
from services.insight_service import generate_event_insights
from repositories.database import enqueue_messages


def render():
    event_id = active_event_id()
    df = guests_df()
    header("Inteligência Operacional", f"Mensagens inteligentes, score de convidados e insights do evento: {active_event_label()}")

    tab1, tab2, tab3 = st.tabs(["Motor de mensagens", "Score do convidado", "Insights"])

    with tab1:
        card_open("Gerador de mensagens inteligentes")
        c1, c2, c3 = st.columns(3)
        tipo = c1.selectbox("Tipo", ["convite", "lembrete", "confirmacao"])
        status = c2.selectbox("RSVP alvo", ["pending", "confirmed", "maybe", "declined"])
        grupo = c3.text_input("Grupo opcional", "")
        template = gerar_template_dinamico(event_id, tipo, grupo, status)
        st.text_area("Template sugerido", value=template, height=90)
        items = gerar_lote_por_rsvp(event_id, tipo, status)
        st.caption(f"Convidados elegíveis pelo RSVP selecionado: {len(items)}")
        if items:
            st.write("Preview")
            for item in items[:5]:
                st.code(item["mensagem"], language="text")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Criar fila com mensagens inteligentes", type="primary", disabled=not bool(items)):
                count = enqueue_messages(event_id, items, skip_sent=True)
                audit_log(event_id, "message_ai", None, "enqueue", f"tipo={tipo}; status={status}; count={count}")
                st.success(f"{count} mensagem(ns) criada(s) sem duplicar enviados.")
                st.rerun()
        with col_b:
            if not df.empty:
                guest_options = {f"#{int(row['id'])} · {row.get('nome_original') or row.get('nome')}": row.to_dict() for _, row in df.fillna("").iterrows()}
                selected = st.selectbox("Preview por convidado", list(guest_options.keys()))
                row = guest_options[selected]
                st.code(gerar_mensagem_automatica(event_id, row, tipo), language="text")
        card_close()

    with tab2:
        card_open("Score heurístico de convidados")
        if st.button("Recalcular scores", type="primary"):
            recalculate_scores(event_id)
            st.success("Scores recalculados.")
            st.rerun()
        scores = list_guest_scores(event_id)
        if scores.empty:
            st.info("Nenhum score calculado ainda. Clique em Recalcular scores.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Prob. média de presença", f"{scores['attendance_probability'].mean() * 100:.1f}%")
            c2.metric("Prioridade média", f"{scores['priority_score'].mean():.1f}")
            c3.metric("Engajamento médio", f"{scores['engagement_score'].mean():.1f}")
            st.dataframe(scores, use_container_width=True, hide_index=True)
        card_close()

    with tab3:
        card_open("Insights executivos")
        insights = generate_event_insights(event_id)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Taxa confirmação", f"{insights['confirmation_rate'] * 100:.1f}%")
        c2.metric("Taxa presença", f"{insights['presence_rate'] * 100:.1f}%")
        c3.metric("Eficiência mesas", f"{insights['table_efficiency'] * 100:.1f}%")
        c4.metric("Conflitos críticos", insights["critical_conflicts"])
        st.write("Distribuição por grupo")
        groups = insights["group_distribution"]
        if groups.empty:
            st.info("Sem grupos cadastrados.")
        else:
            st.dataframe(groups, use_container_width=True, hide_index=True)
            st.bar_chart(groups.set_index("grupo"))
        card_close()
