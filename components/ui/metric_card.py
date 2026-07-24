import html
import streamlit as st


def metric_card(label: str, value, caption: str = "", icon: str = "📌", tone: str = "neutral") -> None:
    tones = {
        "neutral": "ui-card-neutral",
        "success": "ui-card-success",
        "warning": "ui-card-warning",
        "danger": "ui-card-danger",
        "info": "ui-card-info",
        "premium": "ui-card-premium",
    }
    css = tones.get(tone, tones["neutral"])
    st.markdown(
        f"""
        <div class="ui-metric-card {css}">
          <div class="ui-metric-top"><span class="ui-metric-icon">{html.escape(str(icon))}</span><span>{html.escape(str(label))}</span></div>
          <div class="ui-metric-value">{html.escape(str(value))}</div>
          <div class="ui-metric-caption">{html.escape(str(caption))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
