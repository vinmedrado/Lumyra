from __future__ import annotations

import streamlit as st

from components.layout import card_close, card_open, header
from pages.common import active_event_id, active_event_label
from services.guest_portal_service import generate_links_for_event, get_public_base_url, links_dashboard, responses_dashboard


def render():
    event_id = active_event_id()
    header("Portal do Convidado", f"Links próprios, respostas e logística do evento: {active_event_label()}")

    card_open("Configuração")
    st.caption("O link público usa GUEST_PORTAL_BASE_URL no .env. Padrão local: http://127.0.0.1:8000")
    st.code(f"Base atual: {get_public_base_url()}", language="text")
    c1, c2, c3 = st.columns([1, 1, 2])
    expiration_days = c1.number_input("Expiração em dias", min_value=1, max_value=365, value=45)
    overwrite = c2.toggle("Regerar links existentes", value=False)
    if c3.button("Gerar links para convidados", type="primary"):
        count = generate_links_for_event(event_id, overwrite=overwrite, expiration_days=int(expiration_days))
        st.success(f"{count} link(s) gerado(s)/atualizado(s).")
        st.rerun()
    card_close()

    links = links_dashboard(event_id)
    responses = responses_dashboard(event_id)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Links gerados", 0 if links.empty else len(links))
    c2.metric("Respostas recebidas", 0 if responses.empty else len(responses))
    c3.metric("Precisam de ônibus", 0 if responses.empty or "needs_bus" not in responses else int(responses["needs_bus"].fillna(0).astype(int).sum()))
    pendentes = 0 if links.empty else int((~links.get("respondido", False)).sum())
    c4.metric("Pendentes", pendentes)

    card_open("Links gerados")
    if links.empty:
        st.info("Ainda não há links gerados para este evento.")
    else:
        view = links.copy()
        cols = [c for c in ["guest_name", "group_name", "final_table", "phone", "guest_link", "expires_at", "used_at", "respondido"] if c in view.columns]
        st.dataframe(view[cols], use_container_width=True, hide_index=True)
    card_close()

    card_open("Respostas recebidas")
    if responses.empty:
        st.info("Nenhuma resposta recebida ainda.")
    else:
        status = st.selectbox("Filtrar por presença", ["todos", "confirmed", "declined", "maybe", "pending"])
        only_bus = st.toggle("Mostrar apenas quem precisa de ônibus", value=False)
        filtered = responses.copy()
        if status != "todos":
            filtered = filtered[filtered["confirm_presence"] == status]
        if only_bus and "needs_bus" in filtered:
            filtered = filtered[filtered["needs_bus"].fillna(0).astype(int) == 1]
        st.dataframe(filtered, use_container_width=True, hide_index=True)
    card_close()

    card_open("Operação do portal público")
    st.markdown("""
    Para abrir o formulário público localmente:

    ```bash
    uvicorn public_app:app --reload
    ```

    Depois envie o link gerado pelo WhatsApp usando a variável `{guest_link}` no template.
    """)
    card_close()
