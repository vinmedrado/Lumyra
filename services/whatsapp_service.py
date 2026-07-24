from __future__ import annotations

import json
import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv

from repositories.database import connect, enqueue_messages, ensure_default_event, list_messages, log_event, update_message_status

load_dotenv()


def _event_id(event_id: int | None) -> int:
    return int(event_id) if event_id else ensure_default_event()


def get_whatsapp_config() -> dict:
    return {"api_url": os.getenv("EVOLUTION_API_URL", "").strip(), "api_key": os.getenv("EVOLUTION_API_KEY", "").strip(), "instance": os.getenv("EVOLUTION_INSTANCE", os.getenv("EVOLUTION_INSTANCE_NAME", "")).strip()}


def normalize_phone(value) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if not digits:
        return ""
    if not digits.startswith("55") and len(digits) in (10, 11):
        digits = "55" + digits
    return digits


def render_template(template: str, nome: str = "", mesa: str = "", grupo: str = "", guest_link: str = "", evento: str = "") -> str:
    return (template or "").replace("{nome}", nome or "").replace("{mesa}", mesa or "").replace("{grupo}", grupo or "").replace("{guest_link}", guest_link or "").replace("{link}", guest_link or "").replace("{evento}", evento or "")


def prepare_message_items(df: pd.DataFrame, template: str, phone_col: str = "telefone", event_id: int | None = None, event_name: str = "Evento") -> list[dict]:
    items: list[dict] = []
    if df is None or df.empty:
        return items
    for _, row in df.fillna("").iterrows():
        guest_id = row.get("id")
        nome = str(row.get("nome_original") or row.get("nome") or row.get("guest_name") or "").strip()
        grupo = str(row.get("grupo") or row.get("group_name") or nome).strip()
        mesa = str(row.get("mesa_final") or row.get("final_table") or row.get("mesa_corrigida") or "").strip()
        phone = normalize_phone(row.get(phone_col, row.get("phone", "")))
        if not nome:
            continue
        guest_link = ""
        if ("{guest_link}" in template or "{link}" in template) and event_id and str(guest_id).isdigit():
            from services.guest_portal_service import get_guest_link
            guest_link = get_guest_link(int(event_id), int(guest_id))
        message = render_template(template, nome=nome, mesa=mesa, grupo=grupo, guest_link=guest_link, evento=event_name)
        items.append({"guest_id": int(guest_id) if str(guest_id).isdigit() else None, "grupo": grupo, "nome": nome, "telefone": phone, "mesa": mesa, "template": template, "mensagem": message})
    return items


def preview_messages(df: pd.DataFrame, template: str, phone_col: str = "telefone", event_id: int | None = None, event_name: str = "Evento") -> pd.DataFrame:
    items = prepare_message_items(df, template, phone_col, event_id, event_name)
    rows = []
    for item in items:
        valid = bool(item["telefone"]) and len(item["telefone"]) >= 12
        rows.append({"guest_id": item.get("guest_id"), "nome": item.get("nome"), "telefone_normalizado": item.get("telefone"), "mensagem_final": item.get("mensagem"), "validacao": "ok" if valid else "telefone inválido"})
    return pd.DataFrame(rows)


def build_queue_from_guests(df: pd.DataFrame, template: str, phone_col: str = "telefone", event_id: int | None = None) -> int:
    event_id = _event_id(event_id)
    items = prepare_message_items(df, template, phone_col=phone_col, event_id=event_id)
    count = enqueue_messages(event_id, items, skip_sent=True)
    log_event("whatsapp", f"Fila criada com {count} mensagem(ns)", event_id=event_id)
    return count


def send_text(api_url: str, instance: str, api_key: str, number: str, text: str) -> dict:
    payload = {"number": number, "textMessage": {"text": text}}
    headers = {"apikey": api_key, "Content-Type": "application/json"}
    response = requests.post(f"{api_url.rstrip('/')}/message/sendText/{instance}", headers=headers, json=payload, timeout=30)
    return {"ok": response.ok, "status_code": response.status_code, "body": response.text[:1000], "payload": payload, "provider": "evolution"}


def _log_attempt(event_id: int, message_id: int, guest_id, status: str, detail: str, attempt: int, res: dict | None = None) -> None:
    res = res or {}
    with connect() as conn:
        conn.execute("""
            INSERT INTO message_logs(event_id, message_id, guest_id, status, detail, error_message, provider, request_payload, response_status_code, response_body, attempt_number, sent_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CASE WHEN ?='sent' THEN CURRENT_TIMESTAMP ELSE NULL END)
        """, (int(event_id), int(message_id), int(guest_id) if str(guest_id or "").isdigit() else None, status, detail[:500], detail[:500] if status == "error" else None, res.get("provider", "evolution"), json.dumps(res.get("payload", {}), ensure_ascii=False)[:1000], res.get("status_code"), str(res.get("body", ""))[:1000], int(attempt), status))


def process_pending(api_url: str = "", instance: str = "", api_key: str = "", limit: int = 10, dry_run: bool = True, delay_seconds: float = 1.0, event_id: int | None = None, only_errors: bool = False, max_retries: int = 3) -> pd.DataFrame:
    event_id = _event_id(event_id)
    cfg = get_whatsapp_config()
    api_url = api_url or cfg["api_url"]
    api_key = api_key or cfg["api_key"]
    instance = instance or cfg["instance"]
    limit = max(1, int(limit or 10))
    delay_seconds = max(0.0, float(delay_seconds or 0))
    df = list_messages(event_id, "error" if only_errors else "pending")
    if df.empty:
        return pd.DataFrame(columns=["id", "guest_id", "grupo", "status", "detail"])
    selected = df.head(limit).copy()
    results = []
    for _, row in selected.iterrows():
        message_id = int(row["id"])
        phone = normalize_phone(row.get("phone", ""))
        if not phone:
            if not dry_run:
                update_message_status(event_id, message_id, "error", "Telefone vazio/inválido")
            _log_attempt(event_id, message_id, row.get("guest_id"), "error", "Telefone vazio/inválido", 1)
            results.append({"id": message_id, "guest_id": row.get("guest_id"), "grupo": row.get("group_name"), "status": "error", "detail": "Telefone vazio/inválido"})
            continue
        if dry_run:
            results.append({"id": message_id, "guest_id": row.get("guest_id"), "grupo": row.get("group_name"), "status": "preview", "detail": "Dry-run; nada alterado"})
            continue
        if not api_url or not api_key or not instance:
            update_message_status(event_id, message_id, "error", "Configuração Evolution ausente no .env")
            _log_attempt(event_id, message_id, row.get("guest_id"), "error", "Configuração Evolution ausente no .env", 1)
            results.append({"id": message_id, "guest_id": row.get("guest_id"), "grupo": row.get("group_name"), "status": "error", "detail": "Configuração ausente"})
            continue
        last_detail = ""
        for attempt in range(1, max(1, int(max_retries)) + 1):
            try:
                res = send_text(api_url, instance, api_key, phone, row.get("message_text", ""))
                last_detail = f"HTTP {res.get('status_code')}: {res.get('body')}"
                _log_attempt(event_id, message_id, row.get("guest_id"), "sent" if res.get("ok") else "error", last_detail, attempt, res)
                if res.get("ok"):
                    update_message_status(event_id, message_id, "sent", last_detail)
                    results.append({"id": message_id, "guest_id": row.get("guest_id"), "grupo": row.get("group_name"), "status": "sent", "detail": f"Enviado na tentativa {attempt}"})
                    break
            except Exception as exc:
                last_detail = str(exc)
                _log_attempt(event_id, message_id, row.get("guest_id"), "error", last_detail, attempt)
            time.sleep(delay_seconds)
        else:
            update_message_status(event_id, message_id, "error", last_detail)
            results.append({"id": message_id, "guest_id": row.get("guest_id"), "grupo": row.get("group_name"), "status": "error", "detail": last_detail})
    log_event("whatsapp", "Processamento da fila executado", detail=f"limit={limit} dry_run={dry_run} only_errors={only_errors}", event_id=event_id)
    return pd.DataFrame(results)


def get_message_timeline(event_id: int, guest_id: int | None = None) -> pd.DataFrame:
    with connect() as conn:
        sql = """
            SELECT ml.*, m.guest_name, m.phone, m.message_text
            FROM message_logs ml
            LEFT JOIN messages m ON m.id=ml.message_id
            WHERE ml.event_id=?
        """
        params: list = [int(event_id)]
        if guest_id:
            sql += " AND (ml.guest_id=? OR m.guest_id=?)"
            params += [int(guest_id), int(guest_id)]
        sql += " ORDER BY ml.created_at DESC, ml.id DESC"
        rows = conn.execute(sql, tuple(params)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def requeue_failed_messages(event_id: int, limit: int = 100) -> int:
    with connect() as conn:
        rows = conn.execute("SELECT id FROM messages WHERE event_id=? AND status='error' ORDER BY created_at DESC LIMIT ?", (int(event_id), int(limit))).fetchall()
        for r in rows:
            conn.execute("UPDATE messages SET status='pending', error=NULL WHERE id=? AND event_id=?", (int(r["id"]), int(event_id)))
    return len(rows)

# Aliases production worker friendly
def send_pending_messages(event_id: int, limit: int = 50) -> int:
    df = process_pending(event_id=event_id, limit=limit, dry_run=False)
    return int((df.get("status") == "sent").sum()) if not df.empty and "status" in df else 0


def retry_failed_messages(event_id: int, limit: int = 50) -> int:
    return requeue_failed_messages(event_id, limit=limit)
