import streamlit as st

from components.layout import header
from components.ui import action_card, empty_state, info_banner, insight_card, metric_card, progress_card, section_header
from pages.common import active_event_id, active_event_label, guests_df
from repositories.database import get_rsvp, list_messages
from services.event_insights import analyze_event
from services.guest_portal_service import responses_dashboard
from services.table_validation_service import guests_without_table


def render():
    event_id = active_event_id()
    header("Painel dos Noivos", f"Um resumo simples, bonito e atualizado do nosso evento: {active_event_label()}")

    guests = guests_df()
    total = 0 if guests.empty else len(guests)
    if total == 0:
        empty_state(
            "Sua lista de convidados ainda não foi importada",
            "Assim que a assessoria importar os convidados, os indicadores de confirmação, transporte, mensagens e mesas aparecerão aqui.",
            icon="🤍",
            cta="Ir para Documentos" if False else None,
        )
        info_banner("Próximo passo", "Peça para a assessoria importar a lista inicial de convidados para começar o acompanhamento do evento.", "premium", "✨")
        return

    rsvp = get_rsvp(event_id)
    confirmed = int((rsvp["status"] == "confirmed").sum()) if not rsvp.empty else 0
    declined = int((rsvp["status"] == "declined").sum()) if not rsvp.empty else 0
    pending = max(0, total - confirmed - declined)
    progress = confirmed / max(total, 1)
    bus = responses_dashboard(event_id, only_bus=True)
    bus_count = 0 if bus.empty else len(bus)
    msgs_sent = list_messages(event_id, "sent")
    msg_count = 0 if msgs_sent.empty else len(msgs_sent)
    no_table = guests_without_table(event_id)

    if progress >= 0.75:
        info_banner("Está ficando lindo!", f"{progress:.0%} dos convidados já confirmaram presença 🎉", "success", "🎉")
    else:
        info_banner("Convites em andamento", f"Ainda faltam {pending} convidados responderem. Tudo aparece aqui conforme as confirmações chegam.", "premium", "💌")

    section_header("Resumo do nosso evento", "Os números importantes em uma visão simples.", "🤍")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Convidados", total, "pessoas na lista", "👥", "premium")
    with c2:
        metric_card("Confirmados", confirmed, f"{progress:.0%} do total", "✅", "success")
    with c3:
        metric_card("Pendentes", pending, "faltam responder", "⏳", "warning" if pending else "success")
    with c4:
        metric_card("Transporte", bus_count, "solicitaram ônibus", "🚌", "info")

    progress_card(
        "Progresso das confirmações",
        progress,
        f"{confirmed} confirmados, {pending} pendentes e {declined} recusaram até agora.",
        "💍",
    )

    left, right = st.columns([1.15, 1])
    with left:
        section_header("O que precisa de atenção", "Pontos que merecem acompanhamento antes do grande dia.", "✨")
        if pending:
            insight_card("Ainda faltam respostas", f"{pending} convidados ainda não confirmaram presença.", "warning", "A assessoria pode enviar um lembrete pelo WhatsApp.", pending)
        if bus_count:
            insight_card("Transporte solicitado", f"{bus_count} pessoas solicitaram transporte.", "info", "Conferir pontos de embarque e horários.", bus_count)
        if len(no_table):
            insight_card("Mesas pendentes", f"Existem {len(no_table)} convidados sem mesa definida.", "warning", "Revisar o mapa de mesas com a assessoria.", len(no_table))
        if not pending and not len(no_table):
            insight_card("Tudo caminhando bem", "Não há pendências importantes neste momento.", "success", "Continue acompanhando as próximas atualizações.")

    with right:
        section_header("Próximos passos", "Uma trilha simples para acompanhar a operação.", "🗓️")
        action_card("PASSO 1", "Lista de convidados", "Lista importada e pronta para acompanhamento.", done=total > 0, icon="👥")
        action_card("PASSO 2", "Confirmações", "Acompanhar convidados que ainda não responderam.", done=pending == 0, icon="✅")
        action_card("PASSO 3", "Transporte", "Validar solicitações e pontos de embarque.", done=bus_count == 0, icon="🚌")
        action_card("PASSO 4", "Mapa de mesas", "Revisar convidados sem mesa definida.", done=len(no_table) == 0, icon="🪑")
        action_card("PASSO 5", "Mensagens", "Acompanhar envios realizados pela assessoria.", done=msg_count > 0, icon="💬")

    section_header("Atualizações recentes", "Alertas amigáveis gerados automaticamente.", "🧠")
    insights = analyze_event(event_id)[:5]
    if not insights:
        empty_state("Nenhuma atualização recente", "Quando houver novas confirmações, pendências ou alertas, eles aparecerão aqui.", "✨")
    else:
        for ins in insights:
            insight_card(
                ins.get("title", "Atualização"),
                ins.get("message", ""),
                ins.get("severity", "info"),
                ins.get("action", ins.get("recommendation", "")),
                ins.get("count"),
            )
