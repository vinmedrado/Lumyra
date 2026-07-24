from __future__ import annotations

from typing import Any


def page_response(items: list[dict[str, Any]], total: int, page: int, page_size: int) -> dict:
    return {"ok": True, "page": int(page), "page_size": int(page_size), "total": int(total), "items": items, "data": items}


def normalize_page(page: int = 1, page_size: int = 50) -> tuple[int, int]:
    return max(1, int(page or 1)), min(500, max(1, int(page_size or 50)))
