import streamlit as st

from components.layout import card_close, card_open, header
from pages.common import active_event_id, active_event_label
from repositories.database import create_timeline_item, delete_timeline_item, list_timeline, update_timeline_item


def render():
    event_id = active_event_id()
    header("Cronograma", f"Timeline operacional: {active_event_label()}")
    card_open("Adicionar item")
    with st.form("timeline_form"):
        time = st.text_input("Horário", placeholder="18:30")
        title = st.text_input("Título")
        description = st.text_area("Descrição")
        owner = st.text_input("Responsável")
        status = st.selectbox("Status", ["planned", "running", "done", "delayed"])
        if st.form_submit_button("Salvar item", type="primary"):
            if not time.strip() or not title.strip():
                st.error("Informe horário e título.")
            else:
                create_timeline_item(event_id, time, title, description, owner, status)
                st.success("Item criado.")
                st.rerun()
    card_close()

    card_open("Linha do tempo")
    status_filter = st.selectbox("Filtrar status", ["todos", "planned", "running", "done", "delayed"])
    df = list_timeline(event_id, status_filter)
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        item_id = st.selectbox("Atualizar item", df["id"].astype(int).tolist(), format_func=lambda x: f"{df.loc[df['id'] == x, 'time'].iloc[0]} · {df.loc[df['id'] == x, 'title'].iloc[0]}")
        row = df[df["id"] == item_id].iloc[0]
        new_status = st.selectbox("Novo status", ["planned", "running", "done", "delayed"], index=["planned", "running", "done", "delayed"].index(row["status"]))
        c1, c2 = st.columns(2)
        if c1.button("Atualizar status"):
            update_timeline_item(event_id, int(item_id), status=new_status)
            st.success("Cronograma atualizado.")
            st.rerun()
        if c2.button("Excluir item"):
            delete_timeline_item(event_id, int(item_id))
            st.warning("Item excluído.")
            st.rerun()
    card_close()
