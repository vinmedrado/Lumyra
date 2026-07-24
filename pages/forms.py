import streamlit as st
from components.layout import header
from pages.common import active_event_id, active_event_label
from services.form_service import add_field, create_form, delete_field, export_responses_csv, list_fields, list_forms, move_field, responses_for_event, set_active_form, update_field


def render():
    event_id=active_event_id(); header('Formulários Dinâmicos', f'Campos personalizados do portal: {active_event_label()}')
    forms=list_forms(event_id)
    with st.expander('Criar novo formulário', expanded=forms.empty):
        title=st.text_input('Título do formulário', 'Formulário do Convidado')
        active=st.checkbox('Definir como formulário ativo do evento', value=True)
        if st.button('Criar formulário') and title.strip():
            create_form(event_id,title,active); st.success('Formulário criado.'); st.rerun()
    if forms.empty:
        st.info('Nenhum formulário criado ainda.'); return
    labels={f"#{int(r.id)} · {r.title} {'(ativo)' if int(r.is_active or 0) else ''}": int(r.id) for r in forms.itertuples()}
    selected=st.selectbox('Formulário', list(labels.keys())); form_id=labels[selected]
    if st.button('Tornar este o formulário ativo'):
        set_active_form(event_id, form_id); st.success('Formulário ativo atualizado.'); st.rerun()
    st.divider()
    st.subheader('Campos')
    with st.form('add_field'):
        c1,c2,c3=st.columns([2,1,1])
        label=c1.text_input('Label')
        ftype=c2.selectbox('Tipo',['text','select','boolean'])
        required=c3.checkbox('Obrigatório')
        options=st.text_input('Opções do select separadas por vírgula')
        ok=st.form_submit_button('Adicionar campo')
        if ok and label.strip(): add_field(form_id,label,ftype,required,options); st.success('Campo adicionado.'); st.rerun()
    fields=list_fields(form_id)
    if fields.empty: st.info('Nenhum campo neste formulário.')
    else:
        for r in fields.itertuples():
            with st.expander(f"#{int(r.id)} · {r.label} {'✅ ativo' if int(r.is_active or 0) else '⛔ inativo'}"):
                c1,c2,c3,c4=st.columns([2,1,1,1])
                nlabel=c1.text_input('Label', r.label, key=f'l{r.id}')
                nftype=c2.selectbox('Tipo',['text','select','boolean'], index=['text','select','boolean'].index(r.type), key=f't{r.id}')
                nreq=c3.checkbox('Obrigatório', bool(r.required), key=f'r{r.id}')
                nactive=c4.checkbox('Ativo', bool(r.is_active), key=f'a{r.id}')
                noptions=st.text_input('Opções', getattr(r,'options','') or '', key=f'o{r.id}')
                b1,b2,b3,b4=st.columns(4)
                if b1.button('Salvar', key=f's{r.id}'):
                    update_field(r.id,nlabel,nftype,nreq,noptions,nactive); st.success('Campo atualizado.'); st.rerun()
                if b2.button('Subir', key=f'u{r.id}'):
                    move_field(r.id,'up'); st.rerun()
                if b3.button('Descer', key=f'd{r.id}'):
                    move_field(r.id,'down'); st.rerun()
                if b4.button('Excluir/desativar', key=f'x{r.id}'):
                    delete_field(r.id); st.warning('Campo desativado.'); st.rerun()
    st.divider(); st.subheader('Respostas agrupadas por convidado')
    resp=responses_for_event(event_id, grouped=True)
    if resp.empty: st.info('Nenhuma resposta recebida ainda.')
    else:
        st.dataframe(resp, use_container_width=True, hide_index=True)
        st.download_button('Exportar respostas CSV', export_responses_csv(event_id), 'respostas_formulario.csv', 'text/csv')
