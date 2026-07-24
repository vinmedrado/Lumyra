import streamlit as st

from components.layout import card_close, card_open, header
from pages.common import active_event_id, active_event_label
from repositories.database import get_checkins, set_checkin


def render():
    event_id = active_event_id()
    header("Check-in", f"Operação de entrada do evento: {active_event_label()}")
    df = get_checkins(event_id)
    total = len(df)
    presentes = int(df["checked_in"].fillna(0).astype(int).sum()) if not df.empty else 0
    pct = round((presentes / total) * 100, 1) if total else 0
    c1, c2, c3 = st.columns(3)
    for col, (label, value) in zip([c1, c2, c3], [("Total esperado", total), ("Total presente", presentes), ("Presença", f"{pct}%")]):
        with col:
            st.markdown(f"<div class='kpi'><div class='kpi-label'>{label}</div><div class='kpi-value'>{value}</div></div>", unsafe_allow_html=True)

    card_open("Busca rápida")
    filtro = st.selectbox("Status", ["todos", "presentes", "ausentes"])
    busca = st.text_input("Buscar convidado", "")
    work = get_checkins(event_id, filtro)
    if busca and not work.empty:
        mask = work["guest_name"].fillna(work["name"]).astype(str).str.contains(busca, case=False, na=False) | work["group_name"].fillna("").astype(str).str.contains(busca, case=False, na=False)
        work = work[mask]
    st.dataframe(work, use_container_width=True, hide_index=True)
    card_close()

    card_open("Ação de check-in")
    if df.empty:
        st.info("Cadastre convidados para realizar check-in.")
    else:
        options = {f"#{int(r.guest_id)} · {r.guest_name or r.name} · Mesa {r.final_table or '-'}": int(r.guest_id) for r in df.itertuples()}
        selected = st.selectbox("Convidado", list(options.keys()))
        notes = st.text_input("Observação")
        col1, col2 = st.columns(2)
        if col1.button("Realizar check-in", type="primary"):
            set_checkin(event_id, options[selected], True, "manual", notes)
            st.success("Check-in realizado.")
            st.rerun()
        if col2.button("Desfazer check-in"):
            set_checkin(event_id, options[selected], False, "manual", notes)
            st.warning("Check-in desfeito.")
            st.rerun()
    st.caption("Estrutura preparada para QR Code futuramente sem adicionar dependência externa nesta fase.")
    card_close()
