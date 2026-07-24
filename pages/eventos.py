import streamlit as st

from components.layout import card_close, card_open, header
from repositories.database import create_event, list_events, update_event
from services.event_context import set_active_event_id


def render():
    header("Eventos", "Crie eventos e selecione o evento ativo do ERP.")
    events = list_events()
    card_open("Novo evento")
    with st.form("form_evento"):
        name = st.text_input("Nome do evento")
        date = st.date_input("Data", value=None)
        location = st.text_input("Local")
        submit = st.form_submit_button("Criar evento", type="primary")
        if submit:
            if not name.strip():
                st.error("Informe o nome do evento.")
            else:
                event_id = create_event(name, str(date or ""), location)
                set_active_event_id(event_id)
                st.success("Evento criado e selecionado.")
                st.rerun()
    card_close()

    card_open("Eventos cadastrados")
    if events.empty:
        st.info("Nenhum evento cadastrado.")
    else:
        st.dataframe(events, use_container_width=True, hide_index=True)
        edit_id = st.selectbox("Editar evento", events["id"].astype(int).tolist(), format_func=lambda x: events.loc[events["id"] == x, "name"].iloc[0])
        row = events[events["id"] == edit_id].iloc[0]
        with st.form("editar_evento"):
            name = st.text_input("Nome", value=str(row.get("name") or ""))
            date = st.text_input("Data", value=str(row.get("date") or ""))
            location = st.text_input("Local", value=str(row.get("location") or ""))
            c1, c2 = st.columns(2)
            if c1.form_submit_button("Salvar alterações", type="primary"):
                update_event(int(edit_id), name, date, location)
                st.success("Evento atualizado.")
                st.rerun()
            if c2.form_submit_button("Selecionar como ativo"):
                set_active_event_id(int(edit_id))
                st.success("Evento ativo atualizado.")
                st.rerun()
    card_close()
