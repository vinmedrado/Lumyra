from __future__ import annotations

import streamlit as st

from components.layout import header
from components.ui.metric_card import metric_card
from components.ui.info_banner import info_banner
from components.ui.section_header import section_header
from services.auth_service import require_role
from services.health_service import system_health
from services.job_service import list_jobs


def render() -> None:
    if not require_role("ADMIN"):
        return
    header("System Health", "Monitoramento operacional da base SaaS, banco, storage e jobs.")
    health = system_health()
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Banco", "OK" if health["database_ok"] else "Falha", "Conectividade", icon="🗄️", tone="success" if health["database_ok"] else "danger")
    with c2: metric_card("Storage", "OK" if health["storage_ok"] else "Falha", "Arquivos", icon="📦", tone="success" if health["storage_ok"] else "danger")
    with c3: metric_card("Jobs ativos", health["active_jobs"], "Fila atual", icon="⚙️", tone="info")
    with c4: metric_card("Mensagens pendentes", health["pending_messages"], "Aguardando envio", icon="💬", tone="warning")

    c5, c6, c7 = st.columns(3)
    with c5: metric_card("Tenants", health["total_tenants"], "Clientes/assessorias", icon="🏢")
    with c6: metric_card("Usuários", health["total_users"], "Contas cadastradas", icon="👤")
    with c7: metric_card("Eventos", health["total_events"], "Eventos registrados", icon="💍")

    if all([health["database_ok"], health["storage_ok"]]):
        info_banner("Ambiente saudável", "A camada base de produção está respondendo corretamente.", icon="✅", tone="success")
    else:
        info_banner("Atenção necessária", "Verifique DATABASE_URL, STORAGE_PATH e permissões de escrita.", icon="⚠️", tone="warning")

    section_header("Últimos jobs", "Fila simples para automações, exportações e rotinas internas.")
    jobs = list_jobs(limit=25)
    if jobs:
        st.dataframe(jobs, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum job registrado ainda.")
