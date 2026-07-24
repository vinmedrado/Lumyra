from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta
from urllib.parse import quote

import pandas as pd
from dotenv import load_dotenv

from repositories.database import (
    audit_log, connect, ensure_default_event, ensure_guest_public_link, event_is_closed, get_guest_public_link_by_token,
    init_db,
    list_guest_public_links, list_guest_portal_responses, load_guests_df,
    upsert_guest_portal_response, upsert_contact,
)
from services.form_service import get_guest_answers, responses_for_event

load_dotenv()
DEFAULT_EXPIRATION_DAYS = int(os.getenv("GUEST_PORTAL_LINK_EXPIRATION_DAYS", "45"))
DEMO_GUEST_TOKEN = "lumyra-demo-invitation-token"


def get_public_base_url() -> str:
    return os.getenv("GUEST_PORTAL_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def build_guest_url(token: str) -> str:
    return f"{get_public_base_url()}/guest/{quote(token)}"


def generate_guest_token() -> str:
    return secrets.token_urlsafe(32)


def ensure_demo_guest_portal() -> str:
    """Create a deterministic, synthetic invitation used only by Demo Mode."""
    init_db()
    with connect() as conn:
        event_id = ensure_default_event(conn)
        conn.execute(
            """
            UPDATE events
            SET tenant_id=COALESCE(tenant_id, 1),
                name=CASE WHEN name='Evento Principal' THEN 'Casamento Ana & João' ELSE name END,
                date=CASE WHEN COALESCE(date, '')='' THEN '2026-09-19' ELSE date END,
                location=CASE WHEN COALESCE(location, '')='' THEN 'Espaço Jardim Aurora' ELSE location END
            WHERE id=?
            """,
            (event_id,),
        )
        guest = conn.execute(
            "SELECT id FROM guests WHERE event_id=? AND name=? LIMIT 1",
            (event_id, "Marina Oliveira"),
        ).fetchone()
        if guest:
            guest_id = int(guest["id"])
        else:
            guest_id = int(
                conn.execute(
                    """
                    INSERT INTO guests(
                        event_id, tenant_id, name, original_name, phone, invitation_type,
                        invitation_label, category
                    ) VALUES (?, 1, ?, ?, ?, 'individual', ?, 'Amigos')
                    """,
                    (
                        event_id,
                        "Marina Oliveira",
                        "Marina Oliveira",
                        "5511999000001",
                        "Marina Oliveira",
                    ),
                ).lastrowid
            )
    expires_at = (datetime.now() + timedelta(days=365)).isoformat(timespec="seconds")
    ensure_guest_public_link(event_id, guest_id, DEMO_GUEST_TOKEN, expires_at)
    with connect() as conn:
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            """
            INSERT OR IGNORE INTO event_playlists(
                tenant_id, event_id, provider, playlist_url, title, description,
                etiquette_message, is_active, created_at, updated_at
            ) VALUES (1, ?, 'spotify', ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                event_id,
                "https://open.spotify.com/",
                "Playlist do casamento",
                "Uma seleção colaborativa para celebrar Ana & João.",
                "Escolha músicas que combinem com o clima da celebração.",
                now,
                now,
            ),
        )
    return DEMO_GUEST_TOKEN


def ensure_link_for_guest(event_id: int, guest_id: int, expiration_days: int = DEFAULT_EXPIRATION_DAYS) -> str:
    token = generate_guest_token()
    expires_at = (datetime.now() + timedelta(days=int(expiration_days))).isoformat(timespec="seconds")
    ensure_guest_public_link(event_id, guest_id, token, expires_at)
    return token


def generate_links_for_event(event_id: int, overwrite: bool = False, expiration_days: int = DEFAULT_EXPIRATION_DAYS) -> int:
    guests = load_guests_df(event_id)
    if guests.empty:
        return 0
    current = list_guest_public_links(event_id)
    existing_guest_ids = set(current["guest_id"].astype(int).tolist()) if not current.empty and "guest_id" in current else set()
    count = 0
    for _, row in guests.iterrows():
        guest_id = int(row["id"])
        if not overwrite and guest_id in existing_guest_ids:
            continue
        ensure_link_for_guest(event_id, guest_id, expiration_days)
        count += 1
    audit_log(event_id, "guest_public_link", None, "bulk_generate", f"links={count}; overwrite={overwrite}")
    return count


def get_guest_link(event_id: int, guest_id: int) -> str:
    links = list_guest_public_links(event_id)
    if not links.empty:
        hit = links[links["guest_id"].astype(int) == int(guest_id)]
        if not hit.empty:
            return build_guest_url(str(hit.iloc[0]["token"]))
    token = ensure_link_for_guest(event_id, guest_id)
    return build_guest_url(token)


def get_guest_portal_context(token: str) -> dict:
    link = get_guest_public_link_by_token(token)
    if not link:
        return {"ok": False, "error": "Link não encontrado."}
    expires_at = str(link.get("expires_at") or "").strip()
    if expires_at:
        try:
            if datetime.fromisoformat(expires_at) < datetime.now():
                return {"ok": False, "error": "Este link expirou. Solicite um novo link para a assessoria."}
        except ValueError:
            pass
    if event_is_closed(int(link["event_id"])):
        return {"ok": False, "error": "Este evento já foi encerrado e não aceita novas alterações."}
    previous = get_previous_response(int(link["event_id"]), int(link["guest_id"]))
    return {"ok": True, "link": link, "previous_response": previous}


def _invitation_members(link: dict) -> list[dict]:
    event_id = int(link["event_id"])
    invitation_type = str(link.get("invitation_type") or "individual")
    group_name = str(link.get("group_name") or "").strip()
    with connect() as conn:
        if invitation_type == "family" and group_name:
            rows = conn.execute(
                """
                SELECT id, name, invitation_type, invitation_label, group_name, category
                FROM guests
                WHERE event_id=? AND COALESCE(tenant_id, 1)=?
                  AND group_name=?
                ORDER BY id
                """,
                (event_id, int(link.get("tenant_id") or 1), group_name),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, name, invitation_type, invitation_label, group_name, category
                FROM guests
                WHERE event_id=? AND id=?
                """,
                (event_id, int(link["guest_id"])),
            ).fetchall()

    members = []
    for row in rows:
        item = dict(row)
        previous = get_previous_response(event_id, int(item["id"]))
        item["status"] = previous.get("confirm_presence") or "pending"
        members.append(item)
    return members


def get_guest_portal_api_context(token: str) -> dict:
    context = get_guest_portal_context(token)
    if not context.get("ok"):
        return context

    link = context["link"]
    members = _invitation_members(link)
    return {
        "ok": True,
        "event": {
            "id": int(link["event_id"]),
            "name": link.get("event_name") or "Evento",
            "date": link.get("event_date") or "",
            "location": link.get("event_location") or "",
        },
        "invitation": {
            "tenant_id": int(link.get("tenant_id") or 1),
            "event_id": int(link["event_id"]),
            "guest_id": int(link["guest_id"]),
            "type": link.get("invitation_type") or "individual",
            "label": link.get("invitation_label") or link.get("guest_name") or link.get("name"),
            "members": members,
        },
        "response": context.get("previous_response") or {},
    }


def submit_invitation_response(token: str, data: dict) -> dict:
    context = get_guest_portal_context(token)
    if not context.get("ok"):
        return context

    link = context["link"]
    allowed_members = {int(item["id"]): item for item in _invitation_members(link)}
    submitted_members = data.get("members") or []
    if not submitted_members:
        return {"ok": False, "error": "Informe a resposta dos convidados."}

    submitted_ids = {int(item.get("guest_id") or 0) for item in submitted_members}
    if not submitted_ids.issubset(allowed_members):
        return {"ok": False, "error": "Um dos convidados não pertence a este convite."}

    event_id = int(link["event_id"])
    link_id = int(link["id"])
    primary_guest_id = int(link["guest_id"])
    for member in submitted_members:
        guest_id = int(member["guest_id"])
        member_data = {
            **data,
            "confirm_presence": member["status"],
            "phone": data.get("phone") if guest_id == primary_guest_id else "",
            "companions_count": 0,
        }
        member_data.pop("members", None)
        upsert_guest_portal_response(event_id, guest_id, link_id, member_data)

    return {
        "ok": True,
        "event_id": event_id,
        "guest_id": primary_guest_id,
        "members": _invitation_members(link),
    }


def get_previous_response(event_id: int, guest_id: int) -> dict:
    df = list_guest_portal_responses(event_id)
    base = {}
    if not df.empty and "guest_id" in df:
        hit = df[df["guest_id"].astype(int) == int(guest_id)]
        if not hit.empty:
            base = hit.iloc[0].fillna("").to_dict()
    base["dynamic_answers"] = get_guest_answers(guest_id)
    return base


def submit_guest_response(token: str, data: dict) -> dict:
    ctx = get_guest_portal_context(token)
    if not ctx.get("ok"):
        return ctx
    link = ctx["link"]
    event_id = int(link["event_id"])
    guest_id = int(link["guest_id"])
    upsert_guest_portal_response(event_id, guest_id, int(link["id"]), data)
    phone = str(data.get("phone") or "").strip()
    if phone:
        try:
            guest_name = str(link.get("guest_name") or link.get("original_name") or "Convidado")
            upsert_contact(event_id, {"guest_id": guest_id, "name": guest_name, "phone": phone, "group_name": str(link.get("group_name") or ""), "source": "portal", "notes": "Telefone atualizado pelo Portal do Convidado.", "tags": "portal"})
        except Exception:
            pass
    return {"ok": True, "event_id": event_id, "guest_id": guest_id, "summary": get_previous_response(event_id, guest_id)}


def links_dashboard(event_id: int) -> pd.DataFrame:
    df = list_guest_public_links(event_id)
    if not df.empty:
        df["guest_link"] = df["token"].apply(build_guest_url)
        df["respondido"] = df.get("submitted_at", "").fillna("").astype(str).ne("")
        if "needs_bus" in df:
            df["needs_bus"] = df["needs_bus"].fillna(0).astype(int)
    return df


def responses_dashboard(event_id: int, only_bus: bool = False) -> pd.DataFrame:
    return list_guest_portal_responses(event_id, only_bus=only_bus)
