from __future__ import annotations

import io
import re
from typing import Iterable

import pandas as pd

from repositories.database import bulk_upsert_contacts, list_contacts, record_contact_import_log
from services.phone_utils import is_valid_phone, normalize_phone


def normalize_brazil_phone(value) -> str:
    """Compatibilidade: usa o normalizador oficial de telefone brasileiro."""
    return normalize_phone(value)


def _status_row(row: dict, status: str, reason: str = "") -> dict:
    out = dict(row)
    out["status"] = status
    out["motivo"] = reason
    return out

def _first_available(row: dict, keys: Iterable[str]) -> str:
    lowered = {str(k).strip().lower(): k for k in row.keys()}
    for key in keys:
        if not key:
            continue
        original_key = key if key in row else lowered.get(str(key).strip().lower())
        if original_key is not None and str(row.get(original_key) or "").strip():
            return str(row.get(original_key) or "").strip()
    return ""


def dataframe_to_contacts(df: pd.DataFrame, mapping: dict[str, str] | None, source: str) -> list[dict]:
    mapping = mapping or {}
    contacts: list[dict] = []
    if df is None or df.empty:
        return contacts
    records = df.fillna("").to_dict(orient="records")
    seen: set[str] = set()
    for row in records:
        name = _first_available(row, [mapping.get("name", ""), "nome", "name", "Nome", "Name", "contato", "Contato"])
        phone_raw = _first_available(row, [mapping.get("phone", ""), "telefone", "phone", "Telefone", "Phone", "celular", "Celular", "whatsapp", "WhatsApp"])
        phone = normalize_brazil_phone(phone_raw)
        email = _first_available(row, [mapping.get("email", ""), "email", "Email", "e-mail", "E-mail"])
        group_name = _first_available(row, [mapping.get("group_name", ""), "grupo", "group", "Grupo", "Group"])
        notes = _first_available(row, [mapping.get("notes", ""), "observacoes", "observações", "notes", "Observações", "Notes", "obs", "Obs"])
        if not phone or not is_valid_phone(phone):
            contacts.append({"name": name or phone_raw or "Contato sem telefone", "phone_original": phone_raw, "phone": phone, "email": email, "group_name": group_name, "source": source, "notes": notes, "is_valid": False, "invalid_reason": "telefone inválido ou vazio"})
            continue
        if phone in seen:
            contacts.append({"name": name or phone, "phone_original": phone_raw, "phone": phone, "email": email, "group_name": group_name, "source": source, "notes": notes, "is_valid": True, "invalid_reason": "duplicado no arquivo/colagem", "duplicate_scope": "batch"})
            continue
        seen.add(phone)
        contacts.append({"name": name or phone, "phone_original": phone_raw, "phone": phone, "email": email, "group_name": group_name, "source": source, "notes": notes, "is_valid": True, "invalid_reason": ""})
    return contacts


def read_spreadsheet(uploaded_file, file_type: str) -> pd.DataFrame:
    name = str(getattr(uploaded_file, "name", "")).lower()
    if file_type == "csv" or name.endswith(".csv"):
        raw = uploaded_file.getvalue()
        for encoding in ("utf-8-sig", "utf-8", "latin1"):
            try:
                return pd.read_csv(io.BytesIO(raw), encoding=encoding)
            except Exception:
                continue
        return pd.read_csv(io.BytesIO(raw))
    return pd.read_excel(uploaded_file)


def preview_contacts(event_id: int, contacts: list[dict]) -> dict:
    """Classifica contatos antes de importar, considerando duplicidade do evento."""
    existing = list_contacts(event_id)
    existing_by_phone = {}
    if not existing.empty and "phone" in existing.columns:
        for r in existing.fillna("").to_dict(orient="records"):
            existing_by_phone[str(r.get("phone") or "")] = r

    valid: list[dict] = []
    invalid: list[dict] = []
    duplicates: list[dict] = []
    seen_batch: set[str] = set()
    for item in contacts:
        row = dict(item)
        phone = str(row.get("phone") or "").strip()
        row.setdefault("phone_original", row.get("phone") or "")
        if not row.get("is_valid") or not phone or not is_valid_phone(phone):
            row["status"] = "inválido"
            row["motivo"] = row.get("invalid_reason") or "telefone inválido"
            invalid.append(row)
        elif phone in existing_by_phone:
            row["status"] = "duplicado"
            row["motivo"] = "já existe neste evento"
            row["existing_contact_id"] = existing_by_phone[phone].get("id")
            row["existing_name"] = existing_by_phone[phone].get("name")
            duplicates.append(row)
        elif phone in seen_batch:
            row["status"] = "duplicado"
            row["motivo"] = "duplicado nesta importação"
            row["duplicate_scope"] = "batch"
            duplicates.append(row)
        else:
            row["status"] = "válido"
            row["motivo"] = "pronto para importar"
            seen_batch.add(phone)
            valid.append(row)
    return {"valid": valid, "invalid": invalid, "duplicates": duplicates, "total": len(contacts)}


def import_preview(event_id: int, preview: dict, source: str, duplicate_action: str = "ignore") -> dict:
    """Importa uma prévia tratando duplicados conforme a escolha do usuário.

    duplicate_action:
    - ignore: ignora duplicados existentes/lote
    - update: atualiza contatos existentes do evento pelo telefone
    - import_anyway: tenta importar também os duplicados; como telefone é único por evento,
      duplicados existentes serão atualizados de forma segura.
    """
    duplicate_action = duplicate_action if duplicate_action in {"ignore", "update", "import_anyway"} else "ignore"
    to_import = list(preview.get("valid", []))
    duplicates = list(preview.get("duplicates", []))
    invalid_count = len(preview.get("invalid", []))

    if duplicate_action in {"update", "import_anyway"}:
        to_import.extend(duplicates)

    result = bulk_upsert_contacts(event_id, to_import, source=source)
    ignored_duplicates = 0 if duplicate_action in {"update", "import_anyway"} else len(duplicates)
    result.update({
        "total": int(preview.get("total") or (len(to_import) + invalid_count + ignored_duplicates)),
        "duplicates": len(duplicates),
        "duplicates_ignored": ignored_duplicates,
        "duplicate_action": duplicate_action,
        "invalid": invalid_count,
    })
    record_contact_import_log(event_id, source, result)
    return result


def import_dataframe(event_id: int, df: pd.DataFrame, mapping: dict[str, str], source: str) -> dict:
    contacts = dataframe_to_contacts(df, mapping, source)
    return import_preview(event_id, preview_contacts(event_id, contacts), source=source)


def parse_manual_contacts(text: str) -> list[dict]:
    """Extrai contatos de texto colado por usuários leigos.

    Exemplos aceitos:
    João - 11999999999
    Maria: (11) 98888-8888
    Pedro 11 97777-7777
    """
    contacts: list[dict] = []
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        phone_match = re.search(r"(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?\d{4,5}[-\s.]?\d{4}", line)
        phone_raw = phone_match.group(0) if phone_match else ""
        phone = normalize_brazil_phone(phone_raw)
        name = line
        if phone_match:
            name = (line[:phone_match.start()] + " " + line[phone_match.end():]).strip(" -–—:;,")
        name = re.sub(r"\s+", " ", name).strip() or "Contato"
        contacts.append({
            "name": name,
            "phone": phone,
            "source": "manual",
            "phone_original": phone_raw,
            "is_valid": bool(phone) and is_valid_phone(phone),
            "invalid_reason": "" if phone and is_valid_phone(phone) else "telefone não identificado ou inválido",
        })
    return contacts


def create_excel_template() -> bytes:
    df = pd.DataFrame([
        {"nome": "João Silva", "telefone": "11999999999"},
        {"nome": "Maria Souza", "telefone": "11988888888"},
    ])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="contatos")
    return buffer.getvalue()


def parse_vcf(content: str) -> list[dict]:
    contacts: list[dict] = []
    cards = re.split(r"BEGIN:VCARD", content, flags=re.I)
    for card in cards:
        if not card.strip():
            continue
        name_match = re.search(r"^FN(?:;[^:]*)?:(.+)$", card, flags=re.I | re.M)
        name = name_match.group(1).strip() if name_match else "Contato"
        phones = re.findall(r"^TEL(?:;[^:]*)?:(.+)$", card, flags=re.I | re.M)
        for phone_raw in phones:
            phone = normalize_brazil_phone(phone_raw)
            contacts.append({"name": name, "phone_original": phone_raw, "phone": phone, "source": "vcf", "is_valid": bool(phone) and is_valid_phone(phone), "invalid_reason": "" if phone and is_valid_phone(phone) else "telefone inválido"})
    unique = {}
    invalid = []
    for item in contacts:
        if item.get("phone"):
            unique[item["phone"]] = item
        else:
            invalid.append(item)
    return list(unique.values()) + invalid


def import_vcf(event_id: int, uploaded_file) -> dict:
    raw = uploaded_file.getvalue()
    text = raw.decode("utf-8", errors="ignore") if isinstance(raw, bytes) else str(raw)
    contacts = parse_vcf(text)
    return import_preview(event_id, preview_contacts(event_id, contacts), source="vcf")
