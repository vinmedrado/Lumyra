import streamlit as st

from components.layout import card_close, card_open, header
from components.ui import empty_state, info_banner, metric_card, progress_card, section_header
from pages.common import active_event_id, active_event_label
from repositories.database import campaign_dashboard_metrics, campaign_report, list_campaign_recipients, list_campaigns, list_contacts
from services.campaign_service import create_whatsapp_campaign, process_campaign, render_contact_template

DEFAULT_TEMPLATE = "Olá {nome}! Confirme as informações do evento. Grupo: {grupo}."


def _safe_cols(df, cols):
    return [c for c in cols if c in df.columns]


def render():
    event_id = active_event_id()
    header("Campanhas", f"Campanhas profissionais de WhatsApp para contatos do evento: {active_event_label()}")

    metrics = campaign_dashboard_metrics(event_id)
    section_header("Resumo das campanhas", "Acompanhe qualidade da base, envios e erros em uma visão rápida.", "📣")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: metric_card("Contatos", metrics.get("total_contacts", 0), "na base", "📇", "premium")
    with c2: metric_card("Válidos", metrics.get("valid_contacts", 0), "prontos", "✅", "success")
    with c3: metric_card("Inválidos", metrics.get("invalid_contacts", 0), "corrigir", "⚠️", "warning")
    with c4: metric_card("Campanhas", metrics.get("campaigns", 0), "criadas", "📣", "info")
    with c5: metric_card("Enviadas", metrics.get("sent_messages", 0), "mensagens", "💬", "success")
    with c6: metric_card("Erros", metrics.get("errors", 0), "falhas", "🚨", "danger" if metrics.get("errors", 0) else "success")

    contacts = list_contacts(event_id, valid="válidos")
    tab_create, tab_send, tab_report = st.tabs(["Criar campanha", "Enviar / Reenviar", "Relatório"])

    with tab_create:
        card_open("Selecionar contatos")
        if contacts.empty:
            empty_state("Nenhum contato válido disponível", "Importe contatos ou corrija telefones antes de criar campanhas.", "📇")
            card_close()
        else:
            c1, c2, c3 = st.columns(3)
            busca = c1.text_input("Buscar contato", "")
            grupos = ["Todos"] + sorted([x for x in contacts["group_name"].fillna("").astype(str).unique() if x])
            grupo = c2.selectbox("Grupo", grupos)
            tag = c3.text_input("Tag contém", "")

            filtered = contacts.copy()
            if grupo != "Todos":
                filtered = filtered[filtered["group_name"].fillna("").astype(str) == grupo]
            if tag:
                filtered = filtered[filtered["tags"].fillna("").astype(str).str.contains(tag, case=False, na=False)]
            if busca:
                mask = False
                for col in ["name", "phone", "email", "group_name", "tags"]:
                    if col in filtered.columns:
                        mask = mask | filtered[col].fillna("").astype(str).str.contains(busca, case=False, na=False)
                filtered = filtered[mask]

            st.dataframe(filtered[_safe_cols(filtered, ["id", "name", "phone", "group_name", "tags", "source"])], use_container_width=True, hide_index=True)
            selected_all = st.toggle("Selecionar todos os filtrados", value=True)
            selected_ids = filtered["id"].astype(int).tolist() if selected_all else st.multiselect(
                "Contatos específicos",
                options=filtered["id"].astype(int).tolist(),
                format_func=lambda cid: f"#{cid} · {filtered.loc[filtered['id'].astype(int)==cid, 'name'].iloc[0]}",
            )
            card_close()

            card_open("Template e preview")
            name = st.text_input("Nome da campanha", value="Campanha WhatsApp")
            template = st.text_area(
                "Template",
                value=DEFAULT_TEMPLATE,
                height=130,
                help="Variáveis disponíveis: {nome}, {grupo}, {telefone}, {email}, {tags}",
            )
            if selected_ids:
                sample = filtered[filtered["id"].astype(int).isin(selected_ids)].head(5)
                st.caption("Preview das primeiras mensagens")
                for _, row in sample.iterrows():
                    st.code(render_contact_template(template, row.to_dict()), language="text")
            if st.button("Criar campanha", type="primary", disabled=not bool(selected_ids)):
                campaign_id = create_whatsapp_campaign(event_id, name, template, filtered, selected_ids)
                st.success(f"Campanha #{campaign_id} criada. Contatos que já receberam o mesmo template são marcados como skipped.")
                st.rerun()
            card_close()

    with tab_send:
        card_open("Fila segura")
        campaigns = list_campaigns(event_id)
        if campaigns.empty:
            empty_state("Nenhuma campanha criada", "Crie uma campanha para gerar fila, preview e relatório de envio.", "📣")
        else:
            options = {"Todas campanhas pendentes": None}
            options.update({f"#{int(r.id)} · {r.name} · {r.status}": int(r.id) for r in campaigns.itertuples()})
            selected = st.selectbox("Campanha", list(options.keys()))
            selected_campaign_id = options[selected]
            if selected_campaign_id:
                summary = campaign_report(event_id, selected_campaign_id)
                r1, r2, r3, r4, r5 = st.columns(5)
                r1.metric("Total", summary["total"])
                r2.metric("Pendentes", summary["pending"])
                r3.metric("Enviados", summary["sent"])
                r4.metric("Erros", summary["error"])
                r5.metric("Ignorados", summary["skipped"])

            c1, c2, c3, c4 = st.columns(4)
            limit = c1.number_input("Limite por execução", min_value=1, max_value=1000, value=20)
            delay = c2.number_input("Intervalo entre envios (seg)", min_value=0.0, max_value=60.0, value=1.5, step=0.5)
            dry_run = c3.toggle("Modo teste / preview", value=True)
            only_errors = c4.toggle("Reenviar só erros", value=False)
            st.caption("O envio real usa a mesma base de fila de mensagens do WhatsApp e registra logs por campanha, destinatário e mensagem.")
            if st.button("Executar", type="primary"):
                result = process_campaign(
                    event_id,
                    campaign_id=selected_campaign_id,
                    limit=int(limit),
                    delay_seconds=float(delay),
                    dry_run=dry_run,
                    only_errors=only_errors,
                )
                st.dataframe(result, use_container_width=True, hide_index=True)
                info_banner("Preview gerado" if dry_run else "Processamento finalizado", "Revise o relatório abaixo para validar status, erros e mensagens processadas.", "success" if not dry_run else "info", "✅")
        card_close()

    with tab_report:
        card_open("Campanhas criadas")
        campaigns = list_campaigns(event_id)
        if campaigns.empty:
            empty_state("Nenhuma campanha neste evento", "As campanhas criadas aparecerão aqui com status e histórico.", "📣")
        else:
            st.dataframe(campaigns, use_container_width=True, hide_index=True)
        card_close()

        card_open("Destinatários e status")
        campaigns = list_campaigns(event_id)
        campaign_filter = None
        if not campaigns.empty:
            options = {"Todas": None}
            options.update({f"#{int(r.id)} · {r.name}": int(r.id) for r in campaigns.itertuples()})
            campaign_filter = options[st.selectbox("Filtrar campanha", list(options.keys()))]
        status = st.selectbox("Status", ["todos", "pending", "sent", "error", "skipped"])
        recipients = list_campaign_recipients(event_id, campaign_id=campaign_filter, status=status)
        if recipients.empty:
            empty_state("Nenhum destinatário encontrado", "Ajuste os filtros ou crie uma campanha com contatos válidos.", "🔎")
        else:
            st.dataframe(recipients, use_container_width=True, hide_index=True)
        card_close()
