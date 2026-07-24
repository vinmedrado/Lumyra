from __future__ import annotations
import pandas as pd
import streamlit as st
from components.ui.metric_card import metric_card
from components.ui.section_header import section_header
from components.ui.empty_state import empty_state
from pages.common import active_event_id, active_event_label
from services.analytics_service import campaign_analytics
from services.auth_service import require_role


def render() -> None:
    if not require_role(['ADMIN']): st.stop()
    section_header('Analytics de Campanhas', f'Desempenho de mensagens · {active_event_label()}', '💬')
    data=campaign_analytics(active_event_id())
    if not data['campaigns']:
        empty_state('Nenhuma campanha criada', 'Crie uma campanha para acompanhar envio, resposta e erros.', '💬')
        st.stop()
    status={r['status']:r['c'] for r in data['recipients_by_status']}
    logs={r['status']:r['c'] for r in data['logs_by_status']}
    c1,c2,c3,c4=st.columns(4)
    with c1: metric_card('Campanhas', len(data['campaigns']), 'total criado', '📣','info')
    with c2: metric_card('Enviadas', status.get('sent',0), 'destinatários', '✅','success')
    with c3: metric_card('Pendentes', status.get('pending',0), 'na fila', '⏳','warning')
    with c4: metric_card('Erros', status.get('error',0)+logs.get('error',0), 'precisam revisão', '🚨','danger')
    df=pd.DataFrame(data['campaigns'])
    st.dataframe(df[['id','name','status','created_at']] if {'id','name','status','created_at'}.issubset(df.columns) else df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    render()
