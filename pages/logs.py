import streamlit as st

from components.layout import card_close, card_open, header
from core.paths import LOG_DIR
from repositories.database import read_logs
from pages.common import active_event_id, active_event_label


def render():
    event_id = active_event_id()
    header("Logs", f"Monitoramento por evento: {active_event_label()}")
    logs = read_logs(event_id)
    tabs = st.tabs(["Aplicação", "Mensagens", "Importações", "Erros", "Auditoria", "Arquivo app.log"])
    with tabs[0]:
        card_open("Logs internos")
        st.dataframe(logs["app_logs"], use_container_width=True, hide_index=True)
        card_close()
    with tabs[1]:
        card_open("Message logs")
        st.dataframe(logs["message_logs"], use_container_width=True, hide_index=True)
        card_close()
    with tabs[2]:
        card_open("Importações")
        st.dataframe(logs["imports"], use_container_width=True, hide_index=True)
        st.dataframe(logs["import_logs"], use_container_width=True, hide_index=True)
        card_close()
    with tabs[3]:
        card_open("Erros")
        st.dataframe(logs["error_logs"], use_container_width=True, hide_index=True)
        card_close()
    with tabs[4]:
        card_open("Auditoria")
        st.dataframe(logs.get("audit_logs"), use_container_width=True, hide_index=True)
        card_close()
    with tabs[5]:
        card_open("logs/app.log")
        path = LOG_DIR / "app.log"
        if path.exists():
            st.code(path.read_text(encoding="utf-8", errors="ignore")[-12000:], language="text")
        else:
            st.info("Arquivo ainda não gerado.")
        card_close()
