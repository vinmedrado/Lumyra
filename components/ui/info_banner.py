import html
import streamlit as st


def info_banner(title: str, message: str, tone: str = "info", icon: str = "💡") -> None:
    css = {"info":"info", "success":"success", "warning":"warning", "danger":"danger", "premium":"premium"}.get(tone, "info")
    st.markdown(
        f"""
        <div class="ui-banner ui-banner-{css}">
          <div class="ui-banner-icon">{html.escape(str(icon))}</div>
          <div><div class="ui-banner-title">{html.escape(str(title))}</div><div class="ui-banner-msg">{html.escape(str(message))}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
