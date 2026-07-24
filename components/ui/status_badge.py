import html
import streamlit as st


def status_badge(label: str, status: str = "info") -> None:
    tone = {"success":"success", "sent":"success", "paid":"success", "confirmed":"success", "warning":"warning", "pending":"warning", "overdue":"danger", "error":"danger", "failed":"danger", "critical":"danger", "info":"info"}.get(status, "info")
    st.markdown(f"<span class='ui-status ui-status-{tone}'>{html.escape(str(label))}</span>", unsafe_allow_html=True)


def badge_html(label: str, status: str = "info") -> str:
    tone = {"success":"success", "sent":"success", "paid":"success", "confirmed":"success", "warning":"warning", "pending":"warning", "overdue":"danger", "error":"danger", "failed":"danger", "critical":"danger", "info":"info"}.get(status, "info")
    return f"<span class='ui-status ui-status-{tone}'>{html.escape(str(label))}</span>"
