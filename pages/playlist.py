from __future__ import annotations

import pandas as pd
import streamlit as st

from services.playlist_service import DEFAULT_DESCRIPTION, DEFAULT_ETIQUETTE, DEFAULT_TITLE, get_event_playlist, upsert_event_playlist
from services.music_suggestion_service import list_music_suggestions, update_music_suggestion_status


def render(event_id: int = 1, tenant_id: int = 1) -> None:
    st.title("🎵 Playlist do casamento")
    st.caption("Configure o link da playlist colaborativa exibida para noivos e convidados.")

    current = get_event_playlist(tenant_id=tenant_id, event_id=event_id) or {}
    playlist_url = st.text_input("Link da playlist Spotify", value=current.get("playlist_url") or "https://open.spotify.com/")
    title = st.text_input("Título", value=current.get("title") or DEFAULT_TITLE)
    description = st.text_area("Mensagem para convidados", value=current.get("description") or DEFAULT_DESCRIPTION)
    etiquette = st.text_area("Aviso de respeito musical", value=current.get("etiquette_message") or DEFAULT_ETIQUETTE)
    is_active = st.checkbox("Exibir playlist no portal", value=bool(current.get("is_active", True)))

    if st.button("Salvar playlist", type="primary"):
        try:
            upsert_event_playlist(
                tenant_id=tenant_id,
                event_id=event_id,
                playlist_url=playlist_url,
                title=title,
                description=description,
                etiquette_message=etiquette,
                is_active=is_active,
            )
            st.success("Playlist salva com sucesso.")
        except ValueError as exc:
            st.error(str(exc))

    if playlist_url:
        qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=220x220&margin=12&data=" + playlist_url
        st.image(qr_url, caption="QR Code da playlist")
        st.link_button("Abrir playlist", playlist_url)

    st.divider()
    st.subheader("🎶 Sugestões musicais dos convidados")
    suggestions = list_music_suggestions(tenant_id=tenant_id, event_id=event_id, limit=200)
    if not suggestions:
        st.info("Ainda não existem sugestões musicais para este evento.")
        return

    df = pd.DataFrame(suggestions)[["id", "guest_name", "song_name", "artist_name", "status", "message", "created_at"]]
    st.dataframe(df, use_container_width=True, hide_index=True)

    selected_id = st.selectbox("Selecionar sugestão", options=[item["id"] for item in suggestions])
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Aprovar"):
            update_music_suggestion_status(tenant_id, int(selected_id), "approved")
            st.rerun()
    with col2:
        if st.button("Marcar adicionada"):
            update_music_suggestion_status(tenant_id, int(selected_id), "added")
            st.rerun()
    with col3:
        if st.button("Recusar"):
            update_music_suggestion_status(tenant_id, int(selected_id), "rejected")
            st.rerun()


if __name__ == "__main__":
    render()
