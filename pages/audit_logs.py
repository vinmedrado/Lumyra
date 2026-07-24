from __future__ import annotations
import pandas as pd
import streamlit as st
from components.ui.section_header import section_header
from components.ui.empty_state import empty_state
from repositories.database import connect, init_db
from services.auth_service import get_current_tenant, require_role


def render() -> None:
    if not require_role(['ADMIN']): st.stop()
    section_header('Auditoria avançada', 'Rastreabilidade de ações, entidades e severidade.', '🛡️')
    init_db(); tenant_id=int(get_current_tenant()['id'])
    c1,c2,c3,c4=st.columns(4)
    with c1: action=st.text_input('Ação')
    with c2: entity=st.text_input('Entidade')
    with c3: severity=st.selectbox('Severidade',['Todas','info','warning','critical','error'])
    with c4: limit=st.number_input('Limite', 50, 1000, 200)
    where=['tenant_id=?']; params=[tenant_id]
    if action: where.append('action LIKE ?'); params.append(f'%{action}%')
    if entity: where.append('entity_type LIKE ?'); params.append(f'%{entity}%')
    if severity!='Todas': where.append('COALESCE(severity,\'info\')=?'); params.append(severity)
    with connect() as conn:
        rows=[dict(r) for r in conn.execute(f"SELECT * FROM audit_logs WHERE {' AND '.join(where)} ORDER BY created_at DESC LIMIT ?", (*params, int(limit))).fetchall()]
    if not rows:
        empty_state('Nenhum log encontrado', 'Ajuste os filtros ou execute ações no sistema para gerar auditoria.', '🧾')
    else:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

if __name__ == "__main__":
    render()
