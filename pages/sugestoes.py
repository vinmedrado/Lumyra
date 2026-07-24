import pandas as pd
import streamlit as st

from components.layout import card_close, card_open, header
from pages.common import active_event_id, active_event_label
from services.seating_suggestion_service import apply_suggestions, generate_suggestions


def render():
    event_id = active_event_id()
    header("Sugestões de Mesas", f"Distribuição inteligente do evento: {active_event_label()}")
    card_open("Gerar sugestões")
    st.write("O algoritmo tenta manter grupos juntos, respeitar capacidade e preencher convidados sem mesa.")
    if st.button("Gerar sugestões", type="primary"):
        st.session_state["seating_suggestions"] = generate_suggestions(event_id)
    suggestions = st.session_state.get("seating_suggestions", [])
    if suggestions:
        df = pd.DataFrame(suggestions)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.warning("As sugestões não são aplicadas automaticamente. Revise antes de confirmar.")
        if st.button("Aplicar sugestões revisadas"):
            count = apply_suggestions(event_id, suggestions)
            st.success(f"{count} sugestão(ões) aplicada(s).")
            st.session_state.pop("seating_suggestions", None)
            st.rerun()
    else:
        st.info("Clique em gerar para montar uma proposta de distribuição.")
    card_close()
