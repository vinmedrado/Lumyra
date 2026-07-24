import streamlit as st
from components.layout import header
from pages.common import active_event_id, active_event_label, guests_df
from repositories.database import get_rsvp
from services.financial_service import *


def render():
    event_id=active_event_id(); header('Financeiro do Evento', f'Contratos, despesas e pagamentos: {active_event_label()}')
    total=len(guests_df()); rsvp=get_rsvp(event_id); conf=int((rsvp['status']=='confirmed').sum()) if not rsvp.empty else 0
    k=summary(event_id,total,conf)
    c=st.columns(6)
    c[0].metric('Contratado', f"R$ {k['total_contratado']:,.2f}")
    c[1].metric('Pago', f"R$ {k['total_pago']:,.2f}")
    c[2].metric('Pendente', f"R$ {k['total_pendente']:,.2f}")
    c[3].metric('Vencido', f"R$ {k['total_vencido']:,.2f}")
    c[4].metric('Custo/convidado', f"R$ {k['custo_por_convidado']:,.2f}")
    c[5].metric('Custo/confirmado', f"R$ {k['custo_por_confirmado']:,.2f}")
    tab1,tab2=st.tabs(['Despesas','Fornecedores'])
    with tab2:
        with st.form('vendor'):
            name=st.text_input('Fornecedor'); cat=st.selectbox('Categoria', VENDOR_CATEGORIES); phone=st.text_input('Telefone'); notes=st.text_area('Observações')
            if st.form_submit_button('Adicionar fornecedor') and name.strip(): add_vendor(event_id,name,cat,phone,notes); st.success('Fornecedor salvo.'); st.rerun()
        vendors=list_vendors(event_id); st.dataframe(vendors, use_container_width=True, hide_index=True)
        if not vendors.empty:
            sel=st.selectbox('Editar/excluir fornecedor', vendors['id'].astype(int).tolist(), format_func=lambda x: vendors.loc[vendors['id']==x,'name'].iloc[0])
            row=vendors[vendors['id']==sel].iloc[0]
            n=st.text_input('Nome', row['name'], key='vn'); cat=st.selectbox('Categoria ', VENDOR_CATEGORIES, index=VENDOR_CATEGORIES.index(row.get('category') if row.get('category') in VENDOR_CATEGORIES else 'outro'), key='vc')
            ph=st.text_input('Telefone ', row.get('phone','') or '', key='vp'); nt=st.text_area('Obs ', row.get('notes','') or '', key='vo')
            a,b=st.columns(2)
            if a.button('Salvar fornecedor'): update_vendor(event_id,sel,n,cat,ph,nt); st.success('Atualizado.'); st.rerun()
            if b.button('Excluir fornecedor'): delete_vendor(event_id,sel); st.warning('Excluído.'); st.rerun()
    with tab1:
        vendors=list_vendors(event_id)
        with st.form('expense'):
            vid=None
            if not vendors.empty: vid=st.selectbox('Fornecedor', [None]+vendors['id'].astype(int).tolist(), format_func=lambda x: 'Sem fornecedor' if x is None else vendors.loc[vendors['id']==x,'name'].iloc[0])
            desc=st.text_input('Descrição'); amount=st.number_input('Valor', min_value=0.0, step=100.0); status=st.selectbox('Status', EXPENSE_STATUSES); due=st.text_input('Vencimento YYYY-MM-DD'); paid=st.text_input('Pago em YYYY-MM-DD')
            if st.form_submit_button('Adicionar despesa') and desc.strip(): add_expense(event_id,vid,desc,amount,status,due,paid); st.success('Despesa salva.'); st.rerun()
        fc1,fc2,fc3=st.columns(3)
        fcat=fc1.selectbox('Filtrar categoria',['Todos']+VENDOR_CATEGORIES); fstatus=fc2.selectbox('Filtrar status',['Todos']+EXPENSE_STATUSES); fvendor=fc3.selectbox('Filtrar fornecedor',[None]+([] if vendors.empty else vendors['id'].astype(int).tolist()), format_func=lambda x:'Todos' if x is None else vendors.loc[vendors['id']==x,'name'].iloc[0])
        exp=list_expenses(event_id, vendor_id=fvendor, category=fcat, status=fstatus)
        st.dataframe(exp, use_container_width=True, hide_index=True)
        st.download_button('Exportar CSV', export_expenses_csv(event_id, vendor_id=fvendor, category=fcat, status=fstatus), 'financeiro.csv', 'text/csv')
        if not exp.empty:
            sel=st.selectbox('Editar/excluir despesa', exp['id'].astype(int).tolist(), format_func=lambda x: exp.loc[exp['id']==x,'description'].iloc[0])
            row=exp[exp['id']==sel].iloc[0]
            nd=st.text_input('Descrição ', row.get('description','') or '', key='ed'); na=st.number_input('Valor ', min_value=0.0, value=float(row.get('amount') or 0), key='ea'); ns=st.selectbox('Status ', EXPENSE_STATUSES, index=EXPENSE_STATUSES.index(row.get('status') if row.get('status') in EXPENSE_STATUSES else 'pending'), key='es')
            a,b=st.columns(2)
            if a.button('Salvar despesa'): update_expense(event_id,sel,row.get('vendor_id'),nd,na,ns,row.get('due_date') or '',row.get('paid_at') or ''); st.success('Despesa atualizada.'); st.rerun()
            if b.button('Excluir despesa'): delete_expense(event_id,sel); st.warning('Despesa excluída.'); st.rerun()
