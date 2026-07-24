import streamlit as st

from components.layout import card_close, card_open, header
from pages.common import active_event_id, active_event_label
from repositories.database import (
    create_automation_rule,
    delete_automation_rule,
    list_automation_rules,
    list_automation_runs,
    update_automation_rule,
)
from services.automation_service import execute_enabled_rules

TRIGGERS = ["RSVP_confirmed", "RSVP_pending", "event_minus_3_days", "event_minus_1_day", "checkin_missing"]
ACTIONS = ["send_message", "reminder", "create_task"]
DEFAULT_TEMPLATE = "Olá {nome}! Confirme ou atualize seus dados do evento por aqui: {guest_link}"
CONDITIONS = ["todos", "somente_pendentes", "somente_confirmados", "sem_mesa", "sem_checkin"]
TRIGGER_LABELS = {
    "RSVP_confirmed": "Quando RSVP for confirmado",
    "RSVP_pending": "Quando houver RSVP pendente",
    "event_minus_3_days": "3 dias antes do evento",
    "event_minus_1_day": "1 dia antes do evento",
    "checkin_missing": "Convidado confirmado sem check-in",
}
ACTION_LABELS = {"send_message": "Enviar mensagem", "reminder": "Lembrete", "create_task": "Criar tarefa"}


def _rule_card(event_id: int, row) -> None:
    status_badge = "badge-ok" if int(row.enabled) else "badge-warn"
    status_text = "ativa" if int(row.enabled) else "inativa"
    st.markdown(
        f"""
        <div class='rule-card'>
          <div class='brain-title'>{row.name}</div>
          <div class='brain-message'>{TRIGGER_LABELS.get(row.trigger, row.trigger)} → {ACTION_LABELS.get(row.action, row.action)}</div>
          <div class='brain-rec'>Condição: <b>{row.condition or 'todos'}</b> · <span class='badge {status_badge}'>{status_text}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1, 1, 1])
    if c1.button("Ativar" if not int(row.enabled) else "Desativar", key=f"toggle_rule_{row.id}"):
        update_automation_rule(event_id, int(row.id), enabled=not bool(row.enabled))
        st.success("Status da regra atualizado.")
        st.rerun()
    if c2.button("Duplicar", key=f"clone_rule_{row.id}"):
        create_automation_rule(event_id, f"Cópia · {row.name}", row.trigger, row.action, template=row.template or DEFAULT_TEMPLATE, enabled=False, condition=row.condition or "todos")
        st.success("Regra duplicada como inativa.")
        st.rerun()
    if c3.button("Excluir", key=f"delete_rule_{row.id}"):
        delete_automation_rule(event_id, int(row.id))
        st.warning("Regra excluída.")
        st.rerun()


def render():
    event_id = active_event_id()
    header("Automação Visual", f"Crie e controle regras sem código para o evento: {active_event_label()}")

    rules = list_automation_rules(event_id)
    total = 0 if rules.empty else len(rules)
    active = 0 if rules.empty else int(rules["enabled"].fillna(0).astype(int).sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Regras", total)
    c2.metric("Ativas", active)
    c3.metric("Inativas", total - active)

    card_open("Criar regra visual")
    st.caption("Escolha um gatilho, uma condição e uma ação. A execução sempre respeita o evento ativo e o multi-evento.")
    with st.form("create_rule"):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Nome da regra", "Lembrete RSVP pendente")
        trigger_label = c2.selectbox("Quando acontecer", list(TRIGGER_LABELS.values()))
        action_label = c3.selectbox("Então faça", list(ACTION_LABELS.values()))
        trigger = next(k for k, v in TRIGGER_LABELS.items() if v == trigger_label)
        action = next(k for k, v in ACTION_LABELS.items() if v == action_label)
        condition = st.selectbox("Aplicar em", CONDITIONS, help="Filtro simples e seguro. Nenhuma regra consulta dados fora do evento ativo.")
        template = st.text_area("Mensagem / descrição da ação", DEFAULT_TEMPLATE, height=90)
        enabled = st.toggle("Criar regra já ativa", value=True)
        submitted = st.form_submit_button("Criar regra", type="primary")
        if submitted:
            create_automation_rule(event_id, name, trigger, action, template=template, enabled=enabled, condition=condition)
            st.success("Regra criada.")
            st.rerun()
    card_close()

    left, right = st.columns([1.1, 1])
    with left:
        card_open("Regras cadastradas")
        if rules.empty:
            st.info("Nenhuma regra cadastrada.")
        else:
            for row in rules.itertuples(index=False):
                _rule_card(event_id, row)
        card_close()

    with right:
        card_open("Editar regra selecionada")
        if rules.empty:
            st.info("Crie uma regra para editar.")
        else:
            options = {f"#{int(r.id)} · {r.name}": r._asdict() for r in rules.itertuples(index=False)}
            selected = st.selectbox("Regra", list(options.keys()))
            row = options[selected]
            new_enabled = st.toggle("Ativa", value=bool(row.get("enabled")))
            new_trigger = st.selectbox("Trigger", TRIGGERS, index=TRIGGERS.index(row.get("trigger")) if row.get("trigger") in TRIGGERS else 0)
            new_action = st.selectbox("Ação", ACTIONS, index=ACTIONS.index(row.get("action")) if row.get("action") in ACTIONS else 0)
            new_condition = st.selectbox("Condição", CONDITIONS, index=CONDITIONS.index(row.get("condition")) if row.get("condition") in CONDITIONS else 0)
            new_template = st.text_area("Template da regra", row.get("template") or DEFAULT_TEMPLATE, height=90)
            if st.button("Salvar alterações", type="primary"):
                update_automation_rule(event_id, int(row["id"]), enabled=new_enabled, trigger=new_trigger, action=new_action, condition=new_condition, template=new_template)
                st.success("Regra atualizada.")
                st.rerun()
        card_close()

    card_open("Executar automações")
    dry_run = st.toggle("Simular sem criar fila/tarefa", value=True)
    if st.button("Executar regras ativas", type="primary"):
        result = execute_enabled_rules(event_id, dry_run=dry_run)
        st.dataframe(result, use_container_width=True, hide_index=True)
        st.success("Execução finalizada." if not dry_run else "Simulação finalizada.")
    runs = list_automation_runs(event_id)
    if not runs.empty:
        st.write("Histórico")
        st.dataframe(runs, use_container_width=True, hide_index=True)
    card_close()
