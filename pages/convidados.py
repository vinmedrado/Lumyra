import streamlit as st

from components.layout import card_close, card_open, header
from repositories.database import create_guest, delete_guest, update_guest
from services.storage_service import export_csv, save_payload
from pages.common import BASE_COLUMNS, active_event_id, active_event_label, apply_guest_filters, guests_df, group_names, table_names


def _guest_form_defaults(row=None):
    row = row or {}
    return {
        "nome": row.get("nome", ""),
        "nome_original": row.get("nome_original", row.get("nome", "")),
        "categoria": row.get("categoria", ""),
        "tipo": row.get("tipo", ""),
        "grupo": row.get("grupo", ""),
        "mesa_atual": row.get("mesa_atual", ""),
        "mesa_corrigida": row.get("mesa_corrigida", ""),
        "mesa_final": row.get("mesa_final", ""),
        "status_mesa": row.get("status_mesa", ""),
        "telefone": row.get("telefone", ""),
    }


def render():
    event_id = active_event_id()
    df = guests_df()
    header("Convidados", f"CRUD completo de convidados do evento: {active_event_label()}")

    with st.expander("Criar convidado", expanded=False):
        tables = [""] + table_names()
        groups = [""] + group_names()
        with st.form("novo_convidado"):
            c1, c2, c3 = st.columns(3)
            nome = c1.text_input("Nome")
            telefone = c2.text_input("Telefone")
            categoria = c3.text_input("Categoria")
            c4, c5, c6 = st.columns(3)
            grupo = c4.selectbox("Grupo", groups) if groups else c4.text_input("Grupo")
            mesa = c5.selectbox("Mesa", tables) if tables else c5.text_input("Mesa")
            tipo = c6.text_input("Tipo")
            if st.form_submit_button("Criar convidado", type="primary"):
                create_guest(event_id, {"nome": nome, "nome_original": nome, "telefone": telefone, "categoria": categoria, "grupo": grupo, "mesa_final": mesa, "mesa_corrigida": mesa, "tipo": tipo})
                st.success("Convidado criado.")
                st.rerun()

    card_open("Filtros e tabela")
    filtered = apply_guest_filters(df)
    st.dataframe(filtered[BASE_COLUMNS], use_container_width=True, hide_index=True)
    csv_path = export_csv(filtered, event_id=event_id)
    with open(csv_path, "rb") as f:
        st.download_button("Baixar CSV filtrado", data=f, file_name="convidados_evento.csv", mime="text/csv")
    card_close()

    card_open("Edição rápida")
    if df.empty:
        st.info("Nenhum convidado cadastrado.")
    else:
        guest_id = st.selectbox("Selecione o convidado", df["id"].astype(int).tolist(), format_func=lambda x: df.loc[df["id"] == x, "nome_original"].iloc[0])
        row = df[df["id"] == guest_id].iloc[0].to_dict()
        d = _guest_form_defaults(row)
        tables = [""] + table_names()
        groups = [""] + group_names()
        with st.form("editar_convidado"):
            c1, c2, c3 = st.columns(3)
            d["nome"] = c1.text_input("Nome interno", value=str(d["nome"] or ""))
            d["nome_original"] = c2.text_input("Nome original", value=str(d["nome_original"] or ""))
            d["telefone"] = c3.text_input("Telefone", value=str(d["telefone"] or ""))
            c4, c5, c6 = st.columns(3)
            d["grupo"] = c4.selectbox("Grupo", groups, index=groups.index(d["grupo"]) if d["grupo"] in groups else 0) if groups else c4.text_input("Grupo", value=str(d["grupo"] or ""))
            d["mesa_final"] = c5.selectbox("Mesa final", tables, index=tables.index(d["mesa_final"]) if d["mesa_final"] in tables else 0) if tables else c5.text_input("Mesa final", value=str(d["mesa_final"] or ""))
            d["categoria"] = c6.text_input("Categoria", value=str(d["categoria"] or ""))
            d["mesa_corrigida"] = d["mesa_final"]
            d["status_mesa"] = "com_mesa" if d["mesa_final"] else "sem_mesa"
            c7, c8 = st.columns(2)
            if c7.form_submit_button("Salvar alterações", type="primary"):
                update_guest(event_id, int(guest_id), d)
                st.success("Convidado atualizado.")
                st.rerun()
            if c8.form_submit_button("Excluir convidado"):
                delete_guest(event_id, int(guest_id))
                st.warning("Convidado excluído.")
                st.rerun()
    card_close()
