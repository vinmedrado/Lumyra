import streamlit as st

from components.layout import card_close, card_open, header
from components.ui import empty_state, info_banner, metric_card, section_header, status_badge
from repositories.database import list_messages
from services.whatsapp_service import build_queue_from_guests, get_whatsapp_config, prepare_message_items, process_pending
from pages.common import active_event_id, active_event_label, guests_df

DEFAULT_TEMPLATE = "Olá {nome}! Tudo bem? Sua mesa no evento é: {mesa}. Grupo: {grupo}. Confirme sua presença aqui: {guest_link}"


def render():
    event_id = active_event_id()
    df = guests_df()
    header("Mensagens WhatsApp", f"Templates, preview, fila e envio do evento: {active_event_label()}")

    section_header("Preparação da mensagem", "Veja o resultado antes de criar fila ou enviar.", "💬")
    card_open("Template e preview")
    template = st.text_area("Template", value=DEFAULT_TEMPLATE, height=120, help="Variáveis disponíveis: {nome}, {mesa}, {grupo}, {guest_link}")
    items = prepare_message_items(df, template, event_id=event_id)
    preview = items[:5]
    if preview:
        st.caption("Prévia das 5 primeiras mensagens")
        for item in preview:
            st.markdown(f"<div class='ui-insight-card ui-insight-info'><div class='ui-insight-title'>📱 {item.get('nome', 'Convidado')} · {item.get('telefone', '')}</div><div class='ui-insight-message'>{item['mensagem']}</div></div>", unsafe_allow_html=True)
    else:
        empty_state("Nenhum convidado disponível", "Cadastre ou importe convidados para gerar prévias de WhatsApp.", "📱")
    if st.button("Criar fila sem duplicar enviados", type="primary", disabled=not bool(items)):
        count = build_queue_from_guests(df, template, event_id=event_id)
        st.success(f"{count} mensagem(ns) adicionada(s) à fila. Enviados anteriormente foram ignorados.")
        st.rerun()
    card_close()

    section_header("Fila de envio", "Status visual, filtros rápidos e histórico de processamento.", "📣")
    card_open("Fila e filtros")
    status = st.selectbox("Status", ["todos", "pending", "sent", "error"])
    queue = list_messages(event_id, status)
    if not queue.empty:
        m1, m2, m3 = st.columns(3)
        with m1: metric_card("Na fila", len(list_messages(event_id, "pending")), "aguardando envio", "⏳", "warning")
        with m2: metric_card("Enviadas", len(list_messages(event_id, "sent")), "processadas", "✅", "success")
        with m3: metric_card("Erros", len(list_messages(event_id, "error")), "revisar", "🚨", "danger")
        busca = st.text_input("Buscar por nome/grupo/telefone", "")
        if busca:
            mask = False
            for col in ["group_name", "guest_name", "phone"]:
                mask = mask | queue[col].fillna("").astype(str).str.contains(busca, case=False, na=False)
            queue = queue[mask]
        st.dataframe(queue, use_container_width=True, hide_index=True)
    else:
        empty_state("Nenhuma mensagem para este filtro", "Crie uma fila a partir do template para acompanhar envios, erros e tentativas.", "💬")
    card_close()

    section_header("Execução", "Envie em lote com segurança, limite e modo preview.", "🚀")
    card_open("Envio")
    cfg = get_whatsapp_config()
    st.caption("Configuração lida do .env: EVOLUTION_API_URL, EVOLUTION_API_KEY e EVOLUTION_INSTANCE/EVOLUTION_INSTANCE_NAME.")
    c1, c2, c3 = st.columns(3)
    limit = c1.number_input("Limite por execução", min_value=1, max_value=500, value=10)
    dry_run = c2.toggle("Modo teste / preview", value=True)
    only_errors = c3.toggle("Reenviar apenas erros", value=False)
    if st.button("Executar envio", type="primary"):
        result = process_pending(limit=int(limit), dry_run=dry_run, event_id=event_id, only_errors=only_errors)
        st.dataframe(result, use_container_width=True, hide_index=True)
        if dry_run:
            st.info("Modo teste: nenhuma mensagem foi enviada.")
        else:
            st.success("Processamento finalizado.")
    with st.expander("Diagnóstico da configuração"):
        st.write({"api_url_configurada": bool(cfg["api_url"]), "api_key_configurada": bool(cfg["api_key"]), "instance_configurada": bool(cfg["instance"])})
    card_close()
