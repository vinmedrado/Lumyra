import json

from core.paths import ASSESSORIA_CONTEXT, ensure_dirs
from integrations.assessoria_embedded import abrir_login_assessoria
from integrations.assessoria_vip import sincronizar_assessoria
from repositories.database import log_event


def context_exists() -> bool:
    return ASSESSORIA_CONTEXT.exists()


def connect_assessoria(event_id: int | None = None) -> dict:
    ensure_dirs()
    ctx = abrir_login_assessoria()
    if not ctx:
        raise RuntimeError("Contexto não capturado pela janela da Assessoria VIP.")
    with open(ASSESSORIA_CONTEXT, "w", encoding="utf-8") as f:
        json.dump(ctx, f, indent=2, ensure_ascii=False)
    log_event("assessoria_vip", "Contexto da Assessoria VIP capturado", detail=str(ctx.get("event_id", "")), event_id=event_id)
    return ctx


def sync_assessoria(df, event_id: int | None = None):
    result = sincronizar_assessoria(df)
    log_event(
        "assessoria_vip",
        "Sincronização executada",
        detail=f"mesas={result.get('mesas_atualizadas')} convidados={result.get('convidados_movidos')}",
        event_id=event_id,
    )
    return result
