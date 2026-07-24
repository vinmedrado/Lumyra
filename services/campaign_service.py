from __future__ import annotations

import time

import pandas as pd

from repositories.database import (
    campaign_report,
    create_campaign,
    enqueue_campaign_recipient_message,
    list_campaign_recipients,
    log_event,
    set_campaign_status,
    update_campaign_recipient_status,
    update_message_status,
)
from services.whatsapp_service import get_whatsapp_config, normalize_phone, send_text


def render_contact_template(template: str, contact: dict) -> str:
    return (
        (template or "")
        .replace("{nome}", str(contact.get("name") or contact.get("contact_name") or ""))
        .replace("{grupo}", str(contact.get("group_name") or ""))
        .replace("{telefone}", str(contact.get("phone") or ""))
        .replace("{email}", str(contact.get("email") or ""))
        .replace("{tags}", str(contact.get("tags") or ""))
    )


def create_whatsapp_campaign(event_id: int, name: str, template: str, contacts_df: pd.DataFrame, selected_ids: list[int]) -> int:
    campaign_id = create_campaign(event_id, name, template, selected_ids)
    log_event("campaigns", "Campanha WhatsApp criada", detail=f"campaign_id={campaign_id}; recipients={len(set(selected_ids))}", event_id=event_id)
    return campaign_id


def process_campaign(
    event_id: int,
    campaign_id: int | None = None,
    limit: int = 20,
    delay_seconds: float = 1.0,
    dry_run: bool = True,
    only_errors: bool = False,
) -> pd.DataFrame:
    """Processa campanha usando a fila central `messages` como lastro.

    - pending: envia destinatários ainda não processados.
    - only_errors=True: reabre apenas erros para reenvio controlado.
    - dry_run=True: gera preview sem alterar status.
    """
    status = "error" if only_errors else "pending"
    df = list_campaign_recipients(event_id, campaign_id=campaign_id, status=status)
    if df.empty:
        return pd.DataFrame(columns=["recipient_id", "message_id", "campaign", "contact", "phone", "status", "detail"])

    cfg = get_whatsapp_config()
    selected = df.head(int(limit)).copy()
    rows = []

    if campaign_id and not dry_run:
        set_campaign_status(event_id, int(campaign_id), "running")

    for _, rec in selected.fillna("").iterrows():
        recipient_id = int(rec["id"])
        phone = normalize_phone(rec.get("phone", ""))
        text = render_contact_template(rec.get("template", ""), rec.to_dict())
        if not phone:
            update_campaign_recipient_status(event_id, recipient_id, "error", "Telefone inválido")
            rows.append({"recipient_id": recipient_id, "message_id": rec.get("message_id"), "campaign": rec.get("campaign_name"), "contact": rec.get("contact_name"), "phone": phone, "status": "error", "detail": "Telefone inválido"})
            continue

        if dry_run:
            rows.append({"recipient_id": recipient_id, "message_id": rec.get("message_id"), "campaign": rec.get("campaign_name"), "contact": rec.get("contact_name"), "phone": phone, "status": "preview", "detail": text[:500]})
            continue

        message_id = enqueue_campaign_recipient_message(event_id, recipient_id)
        if not cfg["api_url"] or not cfg["api_key"] or not cfg["instance"]:
            update_campaign_recipient_status(event_id, recipient_id, "error", "Configuração Evolution ausente")
            if message_id:
                update_message_status(event_id, message_id, "error", "Configuração Evolution ausente")
            rows.append({"recipient_id": recipient_id, "message_id": message_id, "campaign": rec.get("campaign_name"), "contact": rec.get("contact_name"), "phone": phone, "status": "error", "detail": "Configuração Evolution ausente"})
            continue

        try:
            res = send_text(cfg["api_url"], cfg["instance"], cfg["api_key"], phone, text)
            status_out = "sent" if res["ok"] else "error"
            detail = str(res)[:500]
            update_campaign_recipient_status(event_id, recipient_id, status_out, detail)
            if message_id:
                update_message_status(event_id, message_id, status_out, detail)
            rows.append({"recipient_id": recipient_id, "message_id": message_id, "campaign": rec.get("campaign_name"), "contact": rec.get("contact_name"), "phone": phone, "status": status_out, "detail": detail[:240]})
            time.sleep(max(float(delay_seconds), 0.0))
        except Exception as exc:
            update_campaign_recipient_status(event_id, recipient_id, "error", str(exc))
            if message_id:
                update_message_status(event_id, message_id, "error", str(exc))
            rows.append({"recipient_id": recipient_id, "message_id": message_id, "campaign": rec.get("campaign_name"), "contact": rec.get("contact_name"), "phone": phone, "status": "error", "detail": str(exc)})

    if campaign_id and not dry_run:
        summary = campaign_report(event_id, int(campaign_id))
        if summary["pending"] == 0 and summary["error"] == 0:
            set_campaign_status(event_id, int(campaign_id), "done")
        elif summary["pending"] == 0 and summary["error"] > 0:
            set_campaign_status(event_id, int(campaign_id), "partial_error")
        else:
            set_campaign_status(event_id, int(campaign_id), "queued")

    log_event("campaigns", "Campanha WhatsApp processada", detail=f"campaign_id={campaign_id}; dry_run={dry_run}; only_errors={only_errors}; limit={limit}", event_id=event_id)
    return pd.DataFrame(rows)
