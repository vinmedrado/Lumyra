import streamlit as st
from components.layout import header
from pages.common import active_event_id, active_event_label
from services.document_service import CATEGORIES, delete_document, list_documents, save_document
from services.financial_service import list_vendors


def render():
    event_id=active_event_id(); header('Central de Documentos', f'Arquivos do evento: {active_event_label()}')
    vendors=list_vendors(event_id)
    with st.form('upload_doc'):
        file=st.file_uploader('Arquivo', type=['pdf','xlsx','xls','csv','docx','png','jpg','jpeg'])
        name=st.text_input('Nome visível')
        cat=st.selectbox('Categoria', CATEGORIES)
        desc=st.text_area('Descrição')
        vid=None
        if not vendors.empty:
            vid=st.selectbox('Fornecedor vinculado opcional',[None]+vendors['id'].astype(int).tolist(), format_func=lambda x:'Nenhum' if x is None else vendors.loc[vendors['id']==x,'name'].iloc[0])
        if st.form_submit_button('Salvar documento') and file is not None:
            try:
                save_document(event_id,file,name,cat,desc,vid); st.success('Documento salvo.'); st.rerun()
            except Exception as exc: st.error(str(exc))
    docs=list_documents(event_id)
    if docs.empty: st.info('Nenhum documento enviado ainda.'); return
    for r in docs.itertuples():
        with st.expander(f"{r.name} · {getattr(r,'category','outro')}"):
            st.write(getattr(r,'description','') or 'Sem descrição.')
            st.caption(f"Arquivo original: {getattr(r,'original_filename','') or r.name}")
            path=Path(getattr(r,'file_path',''))
            if path.exists():
                st.download_button('Baixar arquivo', path.read_bytes(), file_name=getattr(r,'original_filename','documento') or 'documento')
            else: st.warning('Arquivo físico não encontrado no storage local.')
            if st.button('Excluir documento', key=f'docdel{r.id}'):
                delete_document(event_id, int(r.id)); st.warning('Documento removido da listagem.'); st.rerun()
