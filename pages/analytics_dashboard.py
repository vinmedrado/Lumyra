from __future__ import annotations
import pandas as pd
import streamlit as st
from components.ui.metric_card import metric_card
from components.ui.section_header import section_header
from components.ui.empty_state import empty_state
from pages.common import active_event_id, active_event_label
from services.analytics_service import event_analytics
from services.auth_service import require_role


def render() -> None:
    if not require_role(['ADMIN','CLIENT']):
        st.stop()
    section_header('Analytics do Evento', f'Métricas operacionais · {active_event_label()}', '📊')
    data=event_analytics(active_event_id())
    if data['total_guests']==0:
        empty_state('Sem dados para analisar', 'Importe convidados para liberar tendências, confirmações e custos.', '📈')
        st.stop()
    c1,c2,c3,c4=st.columns(4)
    with c1: metric_card('Convidados', data['total_guests'], 'base atual', '👥','info')
    with c2: metric_card('Confirmação', f"{data['confirmation_rate']}%", f"{data['confirmed']} confirmados", '✅','success')
    with c3: metric_card('Erros mensagem', data['message_errors'], 'logs com falha', '⚠️','warning' if data['message_errors'] else 'neutral')
    with c4: metric_card('Custo/confirmado', f"R$ {data['cost_per_confirmed']:.2f}", 'base financeira', '💰','premium')
    st.markdown('### Evolução e distribuição')
    left,right=st.columns(2)
    with left:
        df=pd.DataFrame(data['guests_by_group'])
        if not df.empty: st.bar_chart(df.set_index('group_name'))
    with right:
        df=pd.DataFrame(data['table_occupancy'])
        if not df.empty: st.bar_chart(df.set_index('table_name'))
    st.markdown('### Timeline operacional')
    st.info('A timeline consolida RSVP, campanhas, financeiro e mesas. Esta base já está pronta para receber snapshots históricos por dia.')

if __name__ == "__main__":
    render()
