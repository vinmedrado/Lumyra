import html
import streamlit as st


def progress_card(title: str, value: float, caption: str = "", icon: str = "📈") -> None:
    pct = max(0, min(100, round(float(value) * 100)))
    st.markdown(
        f"""
        <div class="ui-progress-card">
          <div class="ui-progress-head"><span>{html.escape(str(icon))}</span><b>{html.escape(str(title))}</b><span>{pct}%</span></div>
          <div class="ui-progress-track"><div class="ui-progress-fill" style="width:{pct}%"></div></div>
          <div class="ui-progress-caption">{html.escape(str(caption))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
