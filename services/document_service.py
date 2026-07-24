from __future__ import annotations
import shutil
from pathlib import Path
from uuid import uuid4
import pandas as pd
from core.paths import DATA_DIR
from repositories.database import connect, init_db

MAX_FILE_MB = 25
CATEGORIES = ["contrato", "lista", "financeiro", "fornecedor", "outro"]

def _doc_dir(event_id:int) -> Path:
    path = DATA_DIR / "documents" / str(int(event_id))
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_document(event_id:int, uploaded_file, name:str="", category:str="outro", description:str="", vendor_id:int|None=None) -> int:
    init_db(); category = category if category in CATEGORIES else "outro"
    original = getattr(uploaded_file, 'name', 'documento') or 'documento'
    content = uploaded_file.getvalue() if hasattr(uploaded_file, 'getvalue') else uploaded_file.read()
    if len(content) > MAX_FILE_MB * 1024 * 1024:
        raise ValueError(f"Arquivo excede {MAX_FILE_MB}MB.")
    suffix = Path(original).suffix.lower()
    stored = f"{uuid4().hex}{suffix}"
    path = _doc_dir(event_id) / stored
    path.write_bytes(content)
    label = (name or Path(original).stem).strip()
    with connect() as conn:
        cur = conn.execute("""INSERT INTO event_documents(event_id,name,file_path,original_filename,stored_filename,category,description,vendor_id,is_deleted)
                              VALUES(?,?,?,?,?,?,?,?,0)""", (int(event_id), label, str(path), original, stored, category, description.strip(), vendor_id))
        return int(cur.lastrowid)

def list_documents(event_id:int, include_deleted:bool=False)->pd.DataFrame:
    init_db()
    sql="""SELECT d.*, v.name AS vendor_name FROM event_documents d LEFT JOIN vendors v ON v.id=d.vendor_id WHERE d.event_id=?"""
    params=[int(event_id)]
    if not include_deleted:
        sql += " AND COALESCE(d.is_deleted,0)=0"
    sql += " ORDER BY d.uploaded_at DESC, d.id DESC"
    with connect() as conn:
        rows=conn.execute(sql, tuple(params)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])

def delete_document(event_id:int, document_id:int) -> None:
    init_db()
    with connect() as conn:
        conn.execute("UPDATE event_documents SET is_deleted=1 WHERE id=? AND event_id=?", (int(document_id), int(event_id)))

def get_document(event_id:int, document_id:int) -> dict|None:
    init_db()
    with connect() as conn:
        row=conn.execute("SELECT * FROM event_documents WHERE id=? AND event_id=? AND COALESCE(is_deleted,0)=0", (int(document_id), int(event_id))).fetchone()
    return dict(row) if row else None
