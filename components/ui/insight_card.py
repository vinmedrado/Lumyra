import html
import streamlit as st


def insight_card(title: str, message: str, severity: str = "info", action: str = "", count=None) -> None:
    icons = {"critical": "🚨", "warning": "⚠️", "info": "✅", "success": "✨"}
    css = {"critical": "danger", "warning": "warning", "info": "info", "success": "success"}.get(severity, "info")
    count_html = f"<span class='ui-pill'>{html.escape(str(count))}</span>" if count not in (None, "") else ""
    action_html = f"<div class='ui-insight-action'>{html.escape(str(action))}</div>" if action else ""
    st.markdown(
        f"""
        <div class="ui-insight-card ui-insight-{css}">
          <div class="ui-insight-title">{icons.get(severity, '•')} {html.escape(str(title))} {count_html}</div>
          <div class="ui-insight-message">{html.escape(str(message))}</div>
          {action_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
