import streamlit as st

from components.layout import APP_VERSION, inject_css
from core.paths import ensure_dirs
from repositories.database import init_db, list_events
from core.context import get_current_event_id, set_current_event_id
from services.auth_service import ROLE_LABELS, get_current_user, login_simulado, require_role

ensure_dirs()
init_db()

st.set_page_config(page_title="Lumyra · Modern Event Operations Platform", page_icon="✦", layout="wide")
inject_css()

PAGES = {
    "Dashboard": ("pages.dashboard", ("ADMIN",)),
    "Painel dos Noivos": ("pages.client_dashboard", ("CLIENT", "ADMIN")),
    "Eventos": ("pages.eventos", ("ADMIN",)),
    "Convidados": ("pages.convidados", ("ADMIN",)),
    "Mesas": ("pages.mesas", ("ADMIN",)),
    "RSVP": ("pages.rsvp", ("ADMIN",)),
    "Check-in": ("pages.checkin", ("STAFF", "ADMIN")),
    "Inteligência": ("pages.inteligencia", ("ADMIN",)),
    "Automações": ("pages.automacoes", ("ADMIN",)),
    "Live Dashboard": ("pages.live_dashboard", ("ADMIN",)),
    "Command Center": ("pages.command_center", ("ADMIN",)),
    "Benchmarking": ("pages.benchmarking", ("ADMIN",)),
    "Mensagens": ("pages.mensagens", ("ADMIN",)),
    "Central de Contatos": ("pages.contatos", ("ADMIN",)),
    "Campanhas": ("pages.campanhas_whatsapp", ("ADMIN",)),
    "Portal do Convidado": ("pages.portal_convidado", ("ADMIN",)),
    "Formulários": ("pages.forms", ("ADMIN",)),
    "Financeiro": ("pages.financial", ("ADMIN", "CLIENT")),
    "Documentos": ("pages.documents", ("ADMIN", "CLIENT")),
    "Validação": ("pages.validacao", ("ADMIN",)),
    "Sugestões": ("pages.sugestoes", ("ADMIN",)),
    "Tarefas": ("pages.tarefas", ("ADMIN",)),
    "Cronograma": ("pages.cronograma", ("ADMIN",)),
    "Importação": ("pages.importacao", ("ADMIN",)),
    "Integrações": ("pages.integracoes", ("ADMIN",)),
    "Logs": ("pages.logs", ("ADMIN",)),
    "System Health": ("pages.system_health", ("ADMIN",)),
    "Analytics": ("pages.analytics_dashboard", ("ADMIN", "CLIENT")),
    "Analytics de Campanhas": ("pages.campaign_analytics", ("ADMIN",)),
    "Onboarding": ("pages.onboarding", ("ADMIN",)),
    "Auditoria": ("pages.audit_logs", ("ADMIN",)),
}

NAV_GROUPS = {
    "OPERAÇÃO": ["Dashboard", "Eventos", "Convidados", "Mesas", "RSVP", "Check-in"],
    "COMUNICAÇÃO": ["Campanhas", "Mensagens", "Central de Contatos", "Portal do Convidado", "Formulários"],
    "GESTÃO": ["Financeiro", "Documentos", "Cronograma", "Tarefas", "Importação", "Integrações", "Logs", "Validação", "Sugestões"],
    "INTELIGÊNCIA": ["Inteligência", "Command Center", "Live Dashboard", "Benchmarking", "Automações", "Analytics", "Analytics de Campanhas", "System Health", "Auditoria"],
    "NOIVOS": ["Painel dos Noivos", "Onboarding"],
}

PAGE_ICONS = {
    "Dashboard": "🏠", "Eventos": "💍", "Convidados": "👥", "Mesas": "🪑", "RSVP": "✅", "Check-in": "🎟️",
    "Campanhas": "📣", "Mensagens": "💬", "Central de Contatos": "📇", "Portal do Convidado": "🔗", "Formulários": "📝",
    "Financeiro": "💳", "Documentos": "📂", "Cronograma": "🗓️", "Tarefas": "📌", "Importação": "⬆️", "Integrações": "🔌", "Logs": "📜", "Validação": "🧪", "Sugestões": "✨",
    "Inteligência": "🧠", "Command Center": "🎛️", "Live Dashboard": "📡", "Benchmarking": "📊", "Automações": "⚙️", "System Health": "🩺", "Analytics": "📈", "Analytics de Campanhas": "📣", "Auditoria": "🛡️", "Onboarding": "🚀", "Painel dos Noivos": "🤍",
}


def _event_selector() -> str:
    events = list_events()
    if events.empty:
        st.sidebar.caption("Evento ativo: nenhum evento cadastrado")
        return "Nenhum evento"
    options = {f"#{int(r.id)} · {r.name}": int(r.id) for r in events.itertuples()}
    current = get_current_event_id()
    labels = list(options.keys())
    current_label = next((label for label, event_id in options.items() if event_id == current), labels[0])
    selected_label = st.sidebar.selectbox("Evento ativo", labels, index=labels.index(current_label))
    set_current_event_id(options[selected_label])
    return selected_label


def render_sidebar() -> str:
    st.sidebar.markdown("""
    <div class='sidebar-brand'>
      <div class='sidebar-title'>✦ Lumyra</div>
      <div class='sidebar-subtitle'>Modern Event Operations Platform</div>
    </div>
    """, unsafe_allow_html=True)
    event_label = _event_selector()

    current = get_current_user()
    keys = list(ROLE_LABELS.keys())
    role = st.sidebar.selectbox(
        "Modo demo · perfil",
        keys,
        index=keys.index(current.get("role", "ADMIN")) if current.get("role", "ADMIN") in keys else 0,
        format_func=lambda r: ROLE_LABELS[r],
        help="Em produção o perfil virá do login real. No demo, o seletor permite testar permissões.",
    )
    if role != current.get("role"):
        login_simulado(role)
        current = get_current_user()

    st.sidebar.markdown(
        f"""
        <div class='sidebar-profile'>
          <div><b>Perfil ativo</b></div>
          <div>{ROLE_LABELS[current['role']]}</div>
          <div class='small-muted'>{current['name']}</div>
          <div class='small-muted'>Evento: {event_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    allowed = {label for label, (_, roles) in PAGES.items() if current["role"] in roles}
    flat_options: list[str] = []
    for category, labels in NAV_GROUPS.items():
        category_labels = [label for label in labels if label in allowed]
        if not category_labels:
            continue
        st.sidebar.markdown(f"<div class='sidebar-category'>{category}</div>", unsafe_allow_html=True)
        for label in category_labels:
            flat_options.append(label)

    if not flat_options:
        st.sidebar.warning("Nenhuma página disponível para este perfil.")
        return "Dashboard"

    page_labels = [f"{PAGE_ICONS.get(label, '•')} {label}" for label in flat_options]
    selected = st.sidebar.radio("Navegação", page_labels, label_visibility="collapsed")
    page_label = flat_options[page_labels.index(selected)]
    st.sidebar.markdown(f"<div class='sidebar-footer'>{APP_VERSION}<br>Patch visual incremental</div>", unsafe_allow_html=True)
    return page_label


page_label = render_sidebar()
module_path, roles = PAGES[page_label]
if require_role(roles):
    module = __import__(module_path, fromlist=["render"])
    module.render()
