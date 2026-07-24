from __future__ import annotations

import csv
import io
import pandas as pd
from repositories.database import connect, init_db

DEFAULT_FIELDS = [
    ("Vai de ônibus?", "boolean", 0, ""),
    ("Qual ponto?", "text", 0, ""),
    ("Restrição alimentar?", "text", 0, ""),
    ("Levar acompanhante?", "boolean", 0, ""),
]
VALID_TYPES = {"text", "select", "boolean"}


def _bool(v) -> int:
    return 1 if bool(v) else 0


def create_form(event_id: int, title: str, is_active: bool = True) -> int:
    init_db()
    with connect() as conn:
        if is_active:
            conn.execute("UPDATE event_forms SET is_active=0, active=0 WHERE event_id=?", (int(event_id),))
        cur = conn.execute("INSERT INTO event_forms(event_id, title, is_active, active) VALUES (?, ?, ?, ?)", (int(event_id), title.strip(), _bool(is_active), _bool(is_active)))
        return int(cur.lastrowid)


def ensure_default_form(event_id: int) -> int:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT id FROM event_forms WHERE event_id=? AND COALESCE(is_active, active, 1)=1 ORDER BY id DESC LIMIT 1", (int(event_id),)).fetchone()
        if row:
            return int(row["id"])
        cur = conn.execute("INSERT INTO event_forms(event_id, title, is_active, active) VALUES (?, ?, 1, 1)", (int(event_id), "Formulário do Convidado"))
        form_id = int(cur.lastrowid)
        for idx, (label, field_type, required, options) in enumerate(DEFAULT_FIELDS, start=1):
            conn.execute("INSERT INTO event_form_fields(form_id, label, type, required, options, sort_order, is_active) VALUES (?, ?, ?, ?, ?, ?, 1)", (form_id, label, field_type, required, options, idx))
        return form_id


def set_active_form(event_id: int, form_id: int) -> None:
    init_db()
    with connect() as conn:
        conn.execute("UPDATE event_forms SET is_active=0, active=0 WHERE event_id=?", (int(event_id),))
        conn.execute("UPDATE event_forms SET is_active=1, active=1, updated_at=CURRENT_TIMESTAMP WHERE id=? AND event_id=?", (int(form_id), int(event_id)))


def add_field(form_id: int, label: str, field_type: str, required: bool = False, options: str = "") -> int:
    init_db()
    if field_type not in VALID_TYPES:
        raise ValueError("Tipo inválido.")
    with connect() as conn:
        order = conn.execute("SELECT COALESCE(MAX(sort_order),0)+1 AS n FROM event_form_fields WHERE form_id=?", (int(form_id),)).fetchone()["n"]
        cur = conn.execute("INSERT INTO event_form_fields(form_id, label, type, required, options, sort_order, is_active) VALUES (?, ?, ?, ?, ?, ?, 1)", (int(form_id), label.strip(), field_type, _bool(required), options.strip(), int(order)))
        return int(cur.lastrowid)


def update_field(field_id: int, label: str, field_type: str, required: bool = False, options: str = "", is_active: bool = True, sort_order: int | None = None) -> None:
    if field_type not in VALID_TYPES:
        raise ValueError("Tipo inválido.")
    init_db()
    with connect() as conn:
        conn.execute("""
            UPDATE event_form_fields
            SET label=?, type=?, required=?, options=?, is_active=?, sort_order=COALESCE(?, sort_order)
            WHERE id=?
        """, (label.strip(), field_type, _bool(required), options.strip(), _bool(is_active), sort_order, int(field_id)))


def delete_field(field_id: int, hard_delete: bool = False) -> None:
    init_db()
    with connect() as conn:
        if hard_delete:
            conn.execute("DELETE FROM event_form_fields WHERE id=?", (int(field_id),))
        else:
            conn.execute("UPDATE event_form_fields SET is_active=0 WHERE id=?", (int(field_id),))


def move_field(field_id: int, direction: str) -> None:
    init_db()
    delta = -1 if direction == "up" else 1
    with connect() as conn:
        row = conn.execute("SELECT id, form_id, sort_order FROM event_form_fields WHERE id=?", (int(field_id),)).fetchone()
        if not row:
            return
        target = conn.execute(
            "SELECT id, sort_order FROM event_form_fields WHERE form_id=? AND sort_order " + ("<" if delta < 0 else ">") + " ? ORDER BY sort_order " + ("DESC" if delta < 0 else "ASC") + " LIMIT 1",
            (int(row["form_id"]), int(row["sort_order"])),
        ).fetchone()
        if target:
            conn.execute("UPDATE event_form_fields SET sort_order=? WHERE id=?", (int(target["sort_order"]), int(row["id"])))
            conn.execute("UPDATE event_form_fields SET sort_order=? WHERE id=?", (int(row["sort_order"]), int(target["id"])))


def list_forms(event_id: int) -> pd.DataFrame:
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT *, COALESCE(is_active, active, 1) AS is_active FROM event_forms WHERE event_id=? ORDER BY is_active DESC, id DESC", (int(event_id),)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def list_fields(form_id: int, active_only: bool = False) -> pd.DataFrame:
    init_db()
    sql = "SELECT *, COALESCE(is_active, 1) AS is_active FROM event_form_fields WHERE form_id=?"
    params: list = [int(form_id)]
    if active_only:
        sql += " AND COALESCE(is_active,1)=1"
    sql += " ORDER BY sort_order, id"
    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def get_guest_answers(guest_id: int) -> dict[int, str]:
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT field_id, value FROM event_form_responses WHERE guest_id=?", (int(guest_id),)).fetchall()
    return {int(r["field_id"]): str(r["value"] or "") for r in rows}


def save_response(guest_id: int, answers: dict[int, str]) -> None:
    init_db()
    with connect() as conn:
        valid = {int(r["id"]) for r in conn.execute("SELECT id FROM event_form_fields WHERE COALESCE(is_active,1)=1").fetchall()}
        for field_id, value in answers.items():
            if int(field_id) not in valid:
                continue
            conn.execute("""
                INSERT INTO event_form_responses(guest_id, field_id, value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(guest_id, field_id) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
            """, (int(guest_id), int(field_id), str(value)))


def responses_for_event(event_id: int, grouped: bool = False) -> pd.DataFrame:
    init_db()
    with connect() as conn:
        rows = conn.execute("""
            SELECT g.id AS guest_id, g.name AS guest_name, g.group_name, f.title AS form_title, ff.label, fr.value, fr.updated_at
            FROM event_form_responses fr
            JOIN event_form_fields ff ON ff.id = fr.field_id
            JOIN event_forms f ON f.id = ff.form_id
            JOIN guests g ON g.id = fr.guest_id
            WHERE g.event_id=?
            ORDER BY g.group_name, g.name, ff.sort_order
        """, (int(event_id),)).fetchall()
    df = pd.DataFrame([dict(r) for r in rows])
    if grouped and not df.empty:
        return df.pivot_table(index=["guest_id", "guest_name", "group_name"], columns="label", values="value", aggfunc="last").reset_index()
    return df


def export_responses_csv(event_id: int) -> str:
    df = responses_for_event(event_id, grouped=True)
    return df.to_csv(index=False, encoding="utf-8-sig") if not df.empty else ""
