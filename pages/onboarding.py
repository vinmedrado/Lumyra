from __future__ import annotations
import streamlit as st
from components.ui.section_header import section_header
from components.ui.action_card import action_card
from repositories.database import connect, init_db, create_event
from services.auth_service import get_current_tenant, require_role


def render() -> None:
    if not require_role(['ADMIN']): st.stop()
    init_db(); tenant=get_current_tenant(); tenant_id=int(tenant['id'])
    section_header('Primeiros passos', 'Configure a operação SaaS sem sair do Streamlit atual.', '🚀')
    with connect() as conn:
        row=conn.execute('SELECT * FROM onboarding_progress WHERE tenant_id=?',(tenant_id,)).fetchone()
        if not row:
            conn.execute('INSERT INTO onboarding_progress(tenant_id, tenant_created) VALUES (?, 1)',(tenant_id,))
            row=conn.execute('SELECT * FROM onboarding_progress WHERE tenant_id=?',(tenant_id,)).fetchone()
    progress=dict(row)
    steps=[('tenant_created','Tenant criado','Base da assessoria configurada'),('event_created','Evento criado','Cadastro principal do casamento'),('guests_imported','Convidados importados','Lista pronta para RSVP'),('form_created','Formulário criado','Perguntas do portal definidas'),('first_campaign_sent','Primeira campanha','Mensagem inicial enviada')]
    done=sum(1 for key,_,_ in steps if progress.get(key))
    st.progress(done/len(steps), text=f'{done}/{len(steps)} passos concluídos')
    for idx,(key,title,desc) in enumerate(steps, start=1):
        status='Concluído' if progress.get(key) else 'Pendente'
        action_card(f'PASSO {idx}', title, desc, bool(progress.get(key)), '✅' if progress.get(key) else '⭕')
    with st.expander('Ações rápidas de onboarding'):
        name=st.text_input('Nome do evento', 'Casamento Demo')
        if st.button('Criar evento e marcar passo 2'):
            event_id=create_event(name)
            with connect() as conn:
                conn.execute('UPDATE events SET tenant_id=? WHERE id=?',(tenant_id,event_id))
                conn.execute('UPDATE onboarding_progress SET event_created=1, current_step=3, updated_at=CURRENT_TIMESTAMP WHERE tenant_id=?',(tenant_id,))
            st.success('Evento criado e onboarding atualizado.')
            st.rerun()

if __name__ == "__main__":
    render()
