"""Contexto global do evento ativo.

Este módulo centraliza a seleção do evento para impedir consultas globais
acidentais. Em Streamlit, a seleção fica em session_state. Fora do Streamlit,
o fallback sempre retorna um evento válido do banco.
"""
from __future__ import annotations

from repositories.database import ensure_default_event, event_exists, list_events

SESSION_KEY = "active_event_id"


def _session_state():
    try:
        import streamlit as st
        return st.session_state
    except Exception:
        return None


def get_current_event_id() -> int:
    events = list_events()
    default_id = int(events.iloc[0]["id"]) if not events.empty else ensure_default_event()
    session = _session_state()
    current = session.get(SESSION_KEY, default_id) if session is not None else default_id
    try:
        current = int(current)
    except Exception:
        current = default_id
    if not event_exists(current):
        current = default_id
    if session is not None:
        session[SESSION_KEY] = current
    return int(current)


def set_current_event_id(event_id: int) -> int:
    event_id = int(event_id)
    if not event_exists(event_id):
        event_id = ensure_default_event()
    session = _session_state()
    if session is not None:
        session[SESSION_KEY] = event_id
    return event_id


# Compatibilidade com o patch anterior.
def get_active_event_id() -> int:
    return get_current_event_id()


def set_active_event_id(event_id: int) -> int:
    return set_current_event_id(event_id)


def get_active_event() -> dict:
    from repositories.database import get_event
    return get_event(get_current_event_id())
