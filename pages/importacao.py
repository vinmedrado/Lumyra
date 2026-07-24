import streamlit as st

from components.layout import card_close, card_open, header
from services.pdf_importer import process_pdf
from pages.common import active_event_id, active_event_label, guests_df


def render():
    event_id = active_event_id()
    header("Importação", f"Importação de PDF vinculada ao evento: {active_event_label()}")
    card_open("Importar lista via PDF")
    uploaded = st.file_uploader("Selecione o PDF exportado da Assessoria VIP", type=["pdf"])
    if st.button("Processar PDF", type="primary", disabled=uploaded is None):
        try:
            payload = process_pdf(uploaded, event_id=event_id)
            st.success(f"PDF processado com sucesso: {len(payload.get('convidados', []))} convidado(s).")
            st.rerun()
        except Exception as exc:
            st.error(f"Erro ao processar PDF: {exc}")
    card_close()
    card_open("Prévia do evento ativo")
    st.dataframe(guests_df().head(200), use_container_width=True, hide_index=True)
    card_close()
