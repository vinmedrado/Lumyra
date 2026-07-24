import time
import streamlit as st

from components.layout import card_close, card_open, header
from pages.common import active_event_id, active_event_label
from repositories.database import get_live_dashboard_data


def render():
    event_id = active_event_id()
    header("Live Dashboard", f"Operação em tempo real do evento: {active_event_label()}")
    ctop1, ctop2 = st.columns([1, 3])
    refresh = ctop1.toggle("Auto-refresh 10s", value=False)
    data = get_live_dashboard_data(event_id)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total esperado", data["total_guests"])
    c2.metric("Presentes", data["present"])
    c3.metric("Presença", f"{data['presence_rate'] * 100:.1f}%")
    c4.metric("Mensagens enviadas", data["sent_messages"])

    left, right = st.columns([1.2, 1])
    with left:
        card_open("Convidados faltantes")
        missing = data["missing_guests"]
        if missing.empty:
            st.success("Nenhum convidado pendente de check-in.")
        else:
            cols = [c for c in ["guest_name", "group_name", "final_table", "phone"] if c in missing.columns]
            st.dataframe(missing[cols], use_container_width=True, hide_index=True)
        card_close()
    with right:
        card_open("Status das mesas")
        tables = data["table_status"]
        if tables.empty:
            st.info("Cadastre mesas e convidados para ver ocupação.")
        else:
            show = tables[[c for c in ["name", "capacity", "occupied", "available"] if c in tables.columns]]
            st.dataframe(show, use_container_width=True, hide_index=True)
            chart = show.set_index("name")[["occupied"]]
            st.bar_chart(chart)
        card_close()

    if refresh:
        time.sleep(10)
        st.rerun()
