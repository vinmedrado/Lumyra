import html
import streamlit as st


def empty_state(title: str, description: str = "", icon: str = "✨", cta: str | None = None) -> bool:
    st.markdown(
        f"""
        <div class="ui-empty-state">
          <div class="ui-empty-icon">{html.escape(str(icon))}</div>
          <div class="ui-empty-title">{html.escape(str(title))}</div>
          <div class="ui-empty-desc">{html.escape(str(description))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if cta:
        return st.button(cta, use_container_width=True)
    return False
