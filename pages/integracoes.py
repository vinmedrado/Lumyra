import streamlit as st

from components.layout import card_close, card_open, header
from services.assessoria_service import connect_assessoria, context_exists, sync_assessoria
from services.whatsapp_service import get_whatsapp_config
from pages.common import active_event_id, active_event_label, guests_df


def render():
    event_id = active_event_id()
    header("Integrações", f"Assessoria VIP e Evolution API · {active_event_label()}")
    card_open("Assessoria VIP")
    st.write("Status:", "conectada" if context_exists() else "pendente")
    c1, c2 = st.columns(2)
    if c1.button("Conectar Assessoria VIP"):
        try:
            connect_assessoria(event_id=event_id)
            st.success("Contexto capturado.")
        except Exception as exc:
            st.error(f"Erro ao conectar: {exc}")
    if c2.button("Sincronizar mesas com Assessoria"):
        try:
            result = sync_assessoria(guests_df(), event_id=event_id)
            st.success("Sincronização executada.")
            st.json(result)
        except Exception as exc:
            st.error(f"Erro ao sincronizar: {exc}")
    card_close()

    card_open("WhatsApp / Evolution API")
    cfg = get_whatsapp_config()
    st.write("EVOLUTION_API_URL:", "configurado" if cfg["api_url"] else "não configurado")
    st.write("EVOLUTION_API_KEY:", "configurado" if cfg["api_key"] else "não configurado")
    st.write("EVOLUTION_INSTANCE:", cfg["instance"] or "não configurado")
    st.info("Configure esses valores no arquivo .env. Não commite .env real no GitHub.")
    card_close()
