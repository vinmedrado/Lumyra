import pandas as pd
import streamlit as st

from repositories.database import list_groups, list_tables, load_guests_df
from services.event_context import get_active_event, get_active_event_id

BASE_COLUMNS = ["id", "nome", "nome_original", "categoria", "tipo", "grupo", "mesa_atual", "mesa_corrigida", "mesa_final", "status_mesa", "telefone"]


def active_event_id() -> int:
    return get_active_event_id()


def active_event_label() -> str:
    event = get_active_event()
    return f"{event.get('name', 'Evento')}" + (f" · {event.get('date')}" if event.get('date') else "")


def guests_df() -> pd.DataFrame:
    df = load_guests_df(active_event_id())
    for col in BASE_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df


def table_names() -> list[str]:
    df = list_tables(active_event_id())
    return df["name"].dropna().astype(str).tolist() if not df.empty else []


def group_names() -> list[str]:
    df = list_groups(active_event_id())
    return df["name"].dropna().astype(str).tolist() if not df.empty else []


def apply_guest_filters(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    c1, c2, c3 = st.columns(3)
    with c1:
        busca = st.text_input("Buscar por nome", "")
    with c2:
        mesa = st.selectbox("Filtrar mesa", ["Todas"] + sorted([x for x in df["mesa_final"].dropna().astype(str).unique() if x]))
    with c3:
        grupo = st.selectbox("Filtrar grupo", ["Todos"] + sorted([x for x in df["grupo"].dropna().astype(str).unique() if x]))
    out = df.copy()
    if busca:
        mask = out["nome_original"].fillna(out["nome"]).astype(str).str.contains(busca, case=False, na=False)
        out = out[mask]
    if mesa != "Todas":
        out = out[out["mesa_final"].astype(str) == mesa]
    if grupo != "Todos":
        out = out[out["grupo"].astype(str) == grupo]
    return out
