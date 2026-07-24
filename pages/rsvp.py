import streamlit as st

from components.layout import card_close, card_open, header
from pages.common import active_event_id, active_event_label
from repositories.database import get_rsvp, upsert_rsvp


def render():
    event_id = active_event_id()
    header("RSVP", f"Confirmações do evento: {active_event_label()}")
    df_all = get_rsvp(event_id)
    total = len(df_all)
    counts = df_all["status"].value_counts().to_dict() if not df_all.empty else {}
    cols = st.columns(4)
    for col, (label, key) in zip(cols, [("Confirmados", "confirmed"), ("Recusados", "declined"), ("Pendentes", "pending"), ("Talvez", "maybe")]):
        with col:
            st.markdown(f"<div class='kpi'><div class='kpi-label'>{label}</div><div class='kpi-value'>{counts.get(key, 0)}</div></div>", unsafe_allow_html=True)

    card_open("Atualizar RSVP")
    if df_all.empty:
        st.info("Cadastre convidados para controlar RSVP.")
    else:
        options = {f"#{int(r.guest_id)} · {r.guest_name or r.name} · {r.group_name or 'sem grupo'}": int(r.guest_id) for r in df_all.itertuples()}
        with st.form("rsvp_form"):
            label = st.selectbox("Convidado", list(options.keys()))
            status = st.selectbox("Status", ["pending", "confirmed", "declined", "maybe"], index=0)
            source = st.selectbox("Origem", ["manual", "whatsapp", "import", "assessoria_vip"])
            notes = st.text_area("Observações")
            if st.form_submit_button("Salvar RSVP", type="primary"):
                upsert_rsvp(event_id, options[label], status, source, notes)
                st.success("RSVP atualizado.")
                st.rerun()
    card_close()

    card_open("Lista de RSVP")
    filtro = st.selectbox("Filtrar status", ["todos", "pending", "confirmed", "declined", "maybe"])
    df = get_rsvp(event_id, filtro)
    busca = st.text_input("Buscar por nome/grupo", "")
    if busca and not df.empty:
        mask = df["guest_name"].fillna(df["name"]).astype(str).str.contains(busca, case=False, na=False) | df["group_name"].fillna("").astype(str).str.contains(busca, case=False, na=False)
        df = df[mask]
    st.dataframe(df, use_container_width=True, hide_index=True)
    card_close()
