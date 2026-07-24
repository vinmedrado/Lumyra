import html
import streamlit as st


def section_header(title: str, subtitle: str = "", icon: str = "") -> None:
    st.markdown(
        f"""
        <div class="ui-section-header">
          <div class="ui-section-title">{html.escape(str(icon))} {html.escape(str(title))}</div>
          <div class="ui-section-subtitle">{html.escape(str(subtitle))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
