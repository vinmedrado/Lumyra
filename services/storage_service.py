from __future__ import annotations

import re
import shutil
from pathlib import Path
from uuid import uuid4

from core.settings import get_settings

_SAFE = re.compile(r"[^a-zA-Z0-9._-]+")


def _safe_name(filename: str) -> str:
    name = Path(filename or "arquivo").name.strip() or "arquivo"
    return _SAFE.sub("_", name)[:120]


def tenant_root(tenant_id: int | str) -> Path:
    root = get_settings().storage_root / "tenants" / f"tenant_{tenant_id}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_file(file_obj, original_filename: str, tenant_id: int | str = 1, folder: str = "documents") -> dict:
    target_dir = tenant_root(tenant_id) / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    safe = _safe_name(original_filename)
    stored = f"{uuid4().hex}_{safe}"
    path = target_dir / stored
    if hasattr(file_obj, "getbuffer"):
        path.write_bytes(file_obj.getbuffer())
    elif hasattr(file_obj, "read"):
        data = file_obj.read()
        path.write_bytes(data if isinstance(data, bytes) else str(data).encode("utf-8"))
    else:
        src = Path(str(file_obj))
        shutil.copyfile(src, path)
    return {"original_filename": safe, "stored_filename": stored, "file_path": str(path)}


def delete_file(file_path: str) -> bool:
    path = Path(file_path)
    if path.exists() and path.is_file():
        path.unlink()
        return True
    return False


def get_file_url(file_path: str) -> str:
    return str(file_path)


def ensure_storage() -> bool:
    settings = get_settings()
    for sub in [settings.storage_root, settings.storage_root / "tenants", settings.storage_root / "exports"]:
        sub.mkdir(parents=True, exist_ok=True)
    return settings.storage_root.exists()
