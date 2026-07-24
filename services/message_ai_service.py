from __future__ import annotations

from datetime import date, datetime
import random

from repositories.database import get_event, get_rsvp

MESSAGE_VARIATIONS = {
    "convite": [
        "Olá {nome}! Você está convidado(a) para o evento. Sua mesa prevista é {mesa}. Grupo: {grupo}.",
        "Oi {nome}! Passando para reforçar seu convite. Mesa: {mesa}. Grupo: {grupo}.",
        "Olá {nome}, será uma alegria ter você conosco. Sua organização atual é mesa {mesa}, grupo {grupo}.",
    ],
    "lembrete": [
        "Olá {nome}! Lembrete carinhoso: o evento está chegando. Sua mesa é {mesa}. Grupo: {grupo}.",
        "Oi {nome}, tudo bem? Passando para lembrar do evento. Mesa: {mesa}; grupo: {grupo}.",
        "Olá {nome}! Falta pouco para o evento. Temos você no grupo {grupo} e mesa {mesa}.",
    ],
    "confirmacao": [
        "Olá {nome}! Pode confirmar sua presença no evento? Sua mesa prevista é {mesa}.",
        "Oi {nome}! Estamos fechando a organização das mesas. Você confirma presença? Grupo: {grupo}.",
        "Olá {nome}, precisamos atualizar sua confirmação. Você conseguirá comparecer? Mesa prevista: {mesa}.",
    ],
}


def days_until_event(event_id: int) -> int | None:
    event = get_event(event_id)
    raw = str(event.get("date") or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            target = datetime.strptime(raw[:10], fmt).date()
            return (target - date.today()).days
        except ValueError:
            continue
    return None


def _safe(value: str | None, fallback: str = "-") -> str:
    value = str(value or "").strip()
    return value if value else fallback


def gerar_mensagem_automatica(event_id: int, guest: dict, tipo: str = "convite", variation_seed: int | None = None) -> str:
    tipo = tipo if tipo in MESSAGE_VARIATIONS else "convite"
    options = MESSAGE_VARIATIONS[tipo]
    rng = random.Random(variation_seed if variation_seed is not None else int(guest.get("id") or guest.get("guest_id") or 0))
    template = rng.choice(options)
    nome = _safe(guest.get("nome_original") or guest.get("guest_name") or guest.get("nome") or guest.get("name"), "convidado(a)")
    mesa = _safe(guest.get("mesa_final") or guest.get("final_table") or guest.get("table_name"), "a confirmar")
    grupo = _safe(guest.get("grupo") or guest.get("group_name"), "geral")
    text = template.format(nome=nome, mesa=mesa, grupo=grupo)
    days = days_until_event(event_id)
    if days is not None:
        if days > 3 and tipo == "convite":
            text += f" Faltam {days} dia(s)."
        elif 0 <= days <= 3:
            text += " O evento está bem próximo, por isso estamos validando os últimos detalhes."
        elif days < 0:
            text += " Estamos atualizando os registros pós-evento."
    if int(guest.get("id") or guest.get("guest_id") or 0):
        try:
            from services.guest_portal_service import get_guest_link
            link = get_guest_link(event_id, int(guest.get("id") or guest.get("guest_id")))
            text += f"\n\nConfirme sua presença e logística aqui: {link}"
        except Exception:
            pass
    return text


def gerar_template_dinamico(event_id: int, tipo: str, grupo: str = "", rsvp_status: str = "pending") -> str:
    days = days_until_event(event_id)
    grupo_txt = f" do grupo {grupo}" if grupo else ""
    if tipo == "lembrete" or (days is not None and 0 <= days <= 3):
        return "Olá {nome}! Lembrete: o evento está chegando. Sua mesa é {mesa}. Grupo: {grupo}."
    if rsvp_status == "confirmed":
        return "Olá {nome}! Sua presença está confirmada. Mesa: {mesa}. Grupo: {grupo}."
    if rsvp_status == "declined":
        return "Olá {nome}! Registramos sua ausência. Obrigado por avisar."
    if tipo == "confirmacao":
        return f"Olá {{nome}}! Estamos confirmando presença{grupo_txt}. Você consegue comparecer? Mesa prevista: {{mesa}}."
    return "Olá {nome}! Você está convidado(a). Mesa prevista: {mesa}. Grupo: {grupo}. Confirme sua presença aqui: {guest_link}"


def gerar_lote_por_rsvp(event_id: int, tipo: str = "confirmacao", status: str = "pending") -> list[dict]:
    df = get_rsvp(event_id, status)
    items = []
    if df.empty:
        return items
    for _, row in df.fillna("").iterrows():
        guest = row.to_dict()
        template = gerar_template_dinamico(event_id, tipo, str(guest.get("group_name") or ""), str(guest.get("status") or "pending"))
        from services.guest_portal_service import get_guest_link
        guest_link = get_guest_link(event_id, int(guest.get("guest_id")))
        message = template.format(
            nome=_safe(guest.get("guest_name"), "convidado(a)"),
            mesa=_safe(guest.get("final_table"), "a confirmar"),
            grupo=_safe(guest.get("group_name"), "geral"),
            guest_link=guest_link,
        )
        items.append({
            "guest_id": int(guest.get("guest_id")),
            "grupo": guest.get("group_name", ""),
            "nome": guest.get("guest_name", ""),
            "telefone": guest.get("phone", ""),
            "mesa": guest.get("final_table", ""),
            "template": template,
            "mensagem": message,
        })
    return items
