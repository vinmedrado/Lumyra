import streamlit as st

from components.layout import card_close, card_open, header
from pages.common import active_event_id, active_event_label
from services.table_validation_service import validate_tables_df


def render():
    event_id = active_event_id()
    header("Validação", f"Auditoria de mesas do evento: {active_event_label()}")
    card_open("Conflitos e alertas")
    df = validate_tables_df(event_id)
    if df.empty:
        st.info("Nenhum item encontrado.")
    else:
        severity = st.selectbox("Severidade", ["todas", "critical", "warning", "info"])
        if severity != "todas":
            df = df[df["severity"] == severity]
        st.dataframe(df, use_container_width=True, hide_index=True)
    card_close()
