from __future__ import annotations

import streamlit as st

from core.settings import get_settings
from repositories.database import connect, init_db
from services.security_service import verify_password

ROLES = ("ADMIN", "CLIENT", "STAFF")
ROLE_LABELS = {
    "ADMIN": "Assessoria / Admin",
    "CLIENT": "Noivos / Cliente",
    "STAFF": "Equipe / Check-in",
}
DEFAULT_NAMES = {
    "ADMIN": "Assessoria",
    "CLIENT": "Noivos",
    "STAFF": "Equipe de Recepção",
}


def _safe_role(role: str | None = None) -> str:
    role = str(role or st.session_state.get("current_role") or "ADMIN").upper()
    return role if role in ROLES else "ADMIN"


def get_current_tenant() -> dict:
    init_db()
    tenant_id = int(st.session_state.get("tenant_id") or 1)
    with connect() as conn:
        row = conn.execute("SELECT * FROM tenants WHERE id=?", (tenant_id,)).fetchone()
    if row:
        return dict(row)
    return {"id": 1, "name": "Assessoria Demo", "slug": "assessoria-demo"}


def set_current_user(role: str, name: str | None = None, user_id: int | None = None, tenant_id: int | None = None, email: str | None = None) -> dict:
    role = _safe_role(role)
    st.session_state["current_role"] = role
    st.session_state["current_user_name"] = (name or DEFAULT_NAMES[role]).strip() or DEFAULT_NAMES[role]
    st.session_state["current_user_id"] = int(user_id or {"ADMIN": 1, "CLIENT": 2, "STAFF": 3}[role])
    st.session_state["tenant_id"] = int(tenant_id or st.session_state.get("tenant_id") or 1)
    if email:
        st.session_state["current_user_email"] = email
    st.session_state["is_authenticated"] = True
    return get_current_user()


def login_simulado(role: str = "ADMIN", name: str | None = None) -> dict:
    return set_current_user(role, name)


def login(email: str, password: str) -> tuple[bool, str]:
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE lower(email)=lower(?) AND COALESCE(is_active, active, 1)=1 LIMIT 1",
            ((email or "").strip(),),
        ).fetchone()
    if not row or not verify_password(password or "", row["password_hash"]):
        return False, "E-mail ou senha inválidos."
    set_current_user(row["role"], row["name"], row["id"], row["tenant_id"] or 1, row["email"])
    try:
        from services.audit_service import log_audit
        log_audit("login", "user", int(row["id"]), tenant_id=int(row["tenant_id"] or 1), user_id=int(row["id"]))
    except Exception:
        pass
    return True, "Login realizado com sucesso."


def logout() -> None:
    for key in ("current_role", "current_user_name", "current_user_id", "current_user_email", "tenant_id", "is_authenticated"):
        st.session_state.pop(key, None)


def get_current_user() -> dict:
    settings = get_settings()
    if "current_role" not in st.session_state:
        if settings.DEMO_MODE:
            set_current_user("ADMIN")
        else:
            return {"id": None, "name": "Visitante", "role": "ANONYMOUS", "label": "Não autenticado", "tenant_id": None}
    role = _safe_role()
    return {
        "id": st.session_state.get("current_user_id", {"ADMIN": 1, "CLIENT": 2, "STAFF": 3}[role]),
        "name": st.session_state.get("current_user_name", DEFAULT_NAMES[role]),
        "email": st.session_state.get("current_user_email", ""),
        "role": role,
        "label": ROLE_LABELS[role],
        "tenant_id": int(st.session_state.get("tenant_id") or 1),
    }


def get_user_role() -> str:
    return str(get_current_user().get("role") or "ADMIN")


def is_admin() -> bool:
    return get_user_role() == "ADMIN"


def is_client() -> bool:
    return get_user_role() == "CLIENT"


def is_staff() -> bool:
    return get_user_role() == "STAFF"


def require_role(role: str | list[str] | tuple[str, ...]) -> bool:
    allowed = {role} if isinstance(role, str) else set(role)
    allowed = {str(x).upper() for x in allowed}
    current = get_user_role()
    if current in allowed:
        return True
    st.error("Acesso restrito para este perfil.")
    st.info(f"Perfil atual: {ROLE_LABELS.get(current, current)}")
    st.caption("No modo demo, altere o perfil no sidebar para visualizar esta área.")
    return False
