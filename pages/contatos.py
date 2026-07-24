import pandas as pd
import streamlit as st

from components.layout import card_close, card_open, header
from pages.common import active_event_id, active_event_label
from repositories.database import (
    campaign_dashboard_metrics,
    delete_contact,
    list_contacts,
    sync_contacts_from_guests,
    upsert_contact,
)
from services.contact_import_service import (
    create_excel_template,
    dataframe_to_contacts,
    import_preview,
    normalize_brazil_phone,
    parse_manual_contacts,
    parse_vcf,
    preview_contacts,
    read_spreadsheet,
)
from services.phone_utils import is_valid_phone


def _columns_mapper(df: pd.DataFrame) -> dict[str, str]:
    cols = [""] + list(df.columns.astype(str))

    def default_index(names: set[str]) -> int:
        return next((i for i, c in enumerate(cols) if c.strip().lower() in names), 0)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        name = st.selectbox("Nome", cols, index=default_index({"nome", "name", "contato"}))
    with c2:
        phone = st.selectbox("Telefone *", cols, index=default_index({"telefone", "phone", "celular", "whatsapp"}))
    with c3:
        email = st.selectbox("Email", cols, index=default_index({"email", "e-mail"}))
    with c4:
        group = st.selectbox("Grupo", cols, index=default_index({"grupo", "group"}))
    with c5:
        notes = st.selectbox("Observações", cols, index=next((i for i, c in enumerate(cols) if "observ" in c.lower() or c.lower() in {"notes", "obs"}), 0))
    return {"name": name, "phone": phone, "email": email, "group_name": group, "notes": notes}


def _preview_block(title: str, preview: dict, source: str, event_id: int, key: str):
    valid = pd.DataFrame(preview.get("valid", []))
    invalid = pd.DataFrame(preview.get("invalid", []))
    duplicates = pd.DataFrame(preview.get("duplicates", []))
    total = int(preview.get("total") or (len(valid) + len(invalid) + len(duplicates)))

    st.markdown(f"#### {title}")
    st.caption("Etapa 3 de 4 — revise antes de salvar. Nada é gravado sem sua confirmação.")
    a, b, c, d = st.columns(4)
    a.metric("Total lido", total)
    b.metric("✔ Válidos", len(valid))
    c.metric("⚠ Inválidos", len(invalid))
    d.metric("🔁 Duplicados", len(duplicates))

    table_rows = []
    for status, frame in [("válido", valid), ("inválido", invalid), ("duplicado", duplicates)]:
        if not frame.empty:
            tmp = frame.copy()
            tmp["status"] = tmp.get("status", status)
            table_rows.append(tmp)
    if table_rows:
        merged = pd.concat(table_rows, ignore_index=True).fillna("")
        cols = [c for c in ["name", "phone_original", "phone", "status", "motivo", "existing_name", "group_name", "notes"] if c in merged.columns]
        renamed = merged[cols].rename(columns={
            "name": "nome",
            "phone_original": "telefone original",
            "phone": "telefone normalizado",
            "existing_name": "contato já cadastrado",
            "group_name": "grupo",
            "notes": "observações",
        })
        st.dataframe(renamed, use_container_width=True, hide_index=True)

    duplicate_action = "ignore"
    if not duplicates.empty:
        st.markdown("##### O que fazer com duplicados?")
        duplicate_action = st.radio(
            "Escolha uma opção simples",
            options=["ignore", "update", "import_anyway"],
            format_func=lambda x: {
                "ignore": "Ignorar duplicados",
                "update": "Atualizar contato existente",
                "import_anyway": "Importar mesmo assim quando possível",
            }[x],
            horizontal=False,
            key=f"dup_action_{key}",
            help="A chave principal é o telefone normalizado dentro deste evento.",
        )

    can_import = not valid.empty or (duplicate_action in {"update", "import_anyway"} and not duplicates.empty)
    if st.button("Confirmar e salvar contatos", type="primary", key=f"confirm_import_{key}", disabled=not can_import, use_container_width=True):
        result = import_preview(event_id, preview, source=source, duplicate_action=duplicate_action)
        st.success(
            f"Pronto: {result['created_or_updated']} contatos salvos. "
            f"{result.get('duplicates_ignored', 0)} duplicados ignorados. "
            f"{result.get('invalid', 0)} inválidos não foram importados."
        )
        st.info("Próximos passos: criar grupos, transformar contatos em convidados ou enviar uma primeira campanha pelo WhatsApp.")
        st.rerun()


def _post_import_suggestions(event_id: int):
    contacts = list_contacts(event_id)
    if contacts.empty:
        return
    with st.expander("Sugestões automáticas para continuar", expanded=True):
        group_count = 0
        if "group_name" in contacts.columns:
            group_count = len([x for x in contacts["group_name"].fillna("").astype(str).unique() if x.strip()])
        st.write(f"Encontrei **{len(contacts)} contatos** neste evento e **{group_count} grupos** preenchidos.")
        c1, c2, c3 = st.columns(3)
        c1.button("Criar grupos automaticamente", use_container_width=True, disabled=group_count == 0, help="Use os nomes de grupo dos contatos para organizar melhor o evento.")
        c2.button("Enviar primeira campanha", use_container_width=True, help="Abra a página Campanhas para selecionar contatos e enviar WhatsApp.")
        c3.button("Transformar contatos em convidados", use_container_width=True, help="Ação planejada para converter contatos selecionados em convidados.")

def _guided_mobile_import():
    card_open("Importar contatos do celular")
    st.caption("Etapa 1 de 4 — escolha como o cliente vai enviar os contatos.")
    st.write("Para quem não sabe mexer com planilha, peça um arquivo de contatos do celular (`.vcf`).")
    with st.expander("iPhone — caminho mais simples"):
        st.markdown("""
1. Abra **Contatos** ou **iCloud Contatos**.
2. Selecione os contatos.
3. Toque em **Compartilhar** / **Exportar vCard**.
4. Envie o arquivo `.vcf` para importar aqui.
        """.strip())
    with st.expander("Android — caminho mais simples"):
        st.markdown("""
1. Abra **Contatos**.
2. Toque em **Corrigir e gerenciar** ou **Gerenciar contatos**.
3. Escolha **Exportar para arquivo**.
4. Envie o arquivo `.vcf` para importar aqui.
        """.strip())
    st.info("O sistema sempre mostra uma prévia com válidos, inválidos e duplicados antes de salvar.")
    card_close()

def render():
    event_id = active_event_id()
    header("Central de Contatos", f"CRM do evento: {active_event_label()}")

    metrics = campaign_dashboard_metrics(event_id)
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Contatos", metrics["total_contacts"])
    k2.metric("Válidos", metrics["valid_contacts"])
    k3.metric("Inválidos", metrics["invalid_contacts"])
    k4.metric("Campanhas", metrics["campaigns"])
    k5.metric("Enviadas", metrics["sent_messages"])
    k6.metric("Erros", metrics["errors"])

    tab_importar, tab_manual, tab_lista = st.tabs(["Importar contatos", "Cadastro manual", "Contatos"])

    with tab_importar:
        st.markdown("### Fluxo simples em 4 etapas")
        st.caption("1. escolher método → 2. importar → 3. revisar → 4. confirmar")
        _guided_mobile_import()

        card_open("Importar por Excel simples")
        st.caption("Etapa 2 de 4 — baixe o modelo ou envie uma planilha com nome e telefone.")
        st.write("Baixe o modelo, preencha apenas **nome** e **telefone**, depois envie o arquivo aqui.")
        st.download_button(
            "Baixar modelo",
            data=create_excel_template(),
            file_name="modelo_contatos_evento.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        uploaded_simple = st.file_uploader("Enviar Excel ou CSV", type=["xlsx", "csv"], key="simple_contacts_file")
        if uploaded_simple:
            source = "csv" if uploaded_simple.name.lower().endswith(".csv") else "excel"
            try:
                df = read_spreadsheet(uploaded_simple, source)
                mapping = {"name": "nome", "phone": "telefone", "email": "", "group_name": "", "notes": ""}
                contacts = dataframe_to_contacts(df, mapping, source)
                preview = preview_contacts(event_id, contacts)
                _preview_block("Pré-visualização do arquivo", preview, source, event_id, key="simple_file")
            except Exception as exc:
                st.error(f"Não consegui ler o arquivo. Verifique se ele tem as colunas nome e telefone. Detalhe: {exc}")
        card_close()

        card_open("Colar lista de contatos")
        st.caption("Etapa 2 de 4 — cole uma lista simples quando o cliente mandar contatos por mensagem.")
        st.write("Cole uma lista simples. Um contato por linha.")
        st.code("João - 11999999999\nMaria - 11988888888", language="text")
        pasted = st.text_area("Lista de contatos", height=150, placeholder="João - 11999999999\nMaria - 11988888888")
        if st.button("Analisar lista colada", key="analyze_pasted"):
            preview = preview_contacts(event_id, parse_manual_contacts(pasted))
            st.session_state["contacts_paste_preview"] = preview
        if "contacts_paste_preview" in st.session_state:
            _preview_block("Pré-visualização da lista colada", st.session_state["contacts_paste_preview"], "manual", event_id, key="pasted")
        card_close()

        card_open("Importar arquivo do celular (.vcf)")
        st.caption("Etapa 2 de 4 — envie o arquivo exportado do celular.")
        vcf = st.file_uploader("Enviar arquivo .vcf", type=["vcf"], key="vcf_file")
        if vcf:
            raw = vcf.getvalue()
            text = raw.decode("utf-8", errors="ignore") if isinstance(raw, bytes) else str(raw)
            preview = preview_contacts(event_id, parse_vcf(text))
            _preview_block("Pré-visualização do VCF", preview, "vcf", event_id, key="vcf")
        card_close()

        card_open("Importação avançada")
        st.caption("Use quando a planilha tiver nomes de colunas diferentes ou informações extras.")
        uploaded = st.file_uploader("Arquivo .xlsx ou .csv", type=["xlsx", "csv"], key="contacts_file_advanced")
        if uploaded:
            source = "csv" if uploaded.name.lower().endswith(".csv") else "excel"
            try:
                df = read_spreadsheet(uploaded, source)
                st.caption("Prévia do arquivo")
                st.dataframe(df.head(20), use_container_width=True, hide_index=True)
                mapping = _columns_mapper(df)
                if not mapping.get("phone"):
                    st.warning("Escolha qual coluna representa o telefone antes de importar.")
                else:
                    contacts = dataframe_to_contacts(df, mapping, source)
                    preview = preview_contacts(event_id, contacts)
                    _preview_block("Pré-visualização da importação avançada", preview, source, event_id, key="advanced_file")
            except Exception as exc:
                st.error(f"Erro ao ler arquivo: {exc}")
        card_close()

        card_open("Sincronizar convidados existentes")
        st.caption("Cria contatos a partir dos convidados que já possuem telefone, sem duplicar por telefone no evento ativo.")
        if st.button("Sincronizar convidados → contatos"):
            result = sync_contacts_from_guests(event_id)
            st.success(f"Sincronização finalizada: {result}")
            st.rerun()
        card_close()

        _post_import_suggestions(event_id)

    with tab_manual:
        card_open("Adicionar contato")
        with st.form("manual_contact_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Nome *")
            phone = c2.text_input("Telefone/WhatsApp *", placeholder="11999999999")
            c3, c4 = st.columns(2)
            email = c3.text_input("Email")
            group_name = c4.text_input("Grupo")
            tags = st.text_input("Tags", placeholder="familia, vip, ônibus")
            notes = st.text_area("Observações", height=80)
            submitted = st.form_submit_button("Salvar contato", type="primary")
        if submitted:
            phone_norm = normalize_brazil_phone(phone)
            if not name.strip() or not phone_norm or not is_valid_phone(phone_norm):
                st.error("Informe nome e um telefone brasileiro válido.")
            else:
                upsert_contact(event_id, {"name": name, "phone": phone_norm, "email": email, "group_name": group_name, "tags": tags, "notes": notes, "source": "manual"})
                st.success("Contato salvo.")
                st.rerun()
        card_close()

    with tab_lista:
        card_open("Lista de contatos")
        df = list_contacts(event_id)
        if df.empty:
            st.info("Nenhum contato cadastrado neste evento.")
        else:
            c1, c2, c3 = st.columns(3)
            busca = c1.text_input("Buscar", "")
            grupos = ["Todos"] + sorted([x for x in df["group_name"].fillna("").astype(str).unique() if x])
            grupo = c2.selectbox("Grupo", grupos)
            valid = c3.selectbox("Status", ["todos", "válidos", "inválidos"])
            out = list_contacts(event_id, group_name=grupo, valid=valid)
            if busca and not out.empty:
                mask = False
                for col in ["name", "phone", "email", "group_name", "tags"]:
                    if col in out.columns:
                        mask = mask | out[col].fillna("").astype(str).str.contains(busca, case=False, na=False)
                out = out[mask]
            st.dataframe(out, use_container_width=True, hide_index=True)
            with st.expander("Excluir contato"):
                options = {f"#{int(r.id)} · {r.name} · {r.phone}": int(r.id) for r in out.itertuples()} if not out.empty else {}
                if options:
                    selected = st.selectbox("Contato", list(options.keys()))
                    if st.button("Excluir contato selecionado"):
                        delete_contact(event_id, options[selected])
                        st.success("Contato excluído.")
                        st.rerun()
        card_close()
