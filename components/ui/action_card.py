import html
import streamlit as st


def action_card(step: str, title: str, description: str, done: bool = False, icon: str = "✅") -> None:
    css = "ui-action-done" if done else "ui-action-open"
    marker = "Concluído" if done else "Pendente"
    st.markdown(
        f"""
        <div class="ui-action-card {css}">
          <div class="ui-action-step">{html.escape(str(step))}</div>
          <div class="ui-action-body"><b>{html.escape(str(icon))} {html.escape(str(title))}</b><span>{html.escape(str(description))}</span></div>
          <div class="ui-action-marker">{marker}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
