import streamlit as st

from components.layout import card_close, card_open, header
from pages.common import active_event_id, active_event_label
from repositories.database import create_task, delete_task, list_tasks, update_task


def render():
    event_id = active_event_id()
    header("Tarefas", f"Operação da assessoria: {active_event_label()}")
    card_open("Criar tarefa")
    with st.form("task_form"):
        title = st.text_input("Título")
        description = st.text_area("Descrição")
        c1, c2, c3 = st.columns(3)
        status = c1.selectbox("Status", ["pending", "in_progress", "done", "canceled"])
        priority = c2.selectbox("Prioridade", ["low", "medium", "high", "critical"], index=1)
        due_date = c3.date_input("Prazo", value=None)
        owner = st.text_input("Responsável")
        if st.form_submit_button("Salvar tarefa", type="primary"):
            if not title.strip():
                st.error("Informe o título.")
            else:
                create_task(event_id, title, description, status, priority, str(due_date or ""), owner)
                st.success("Tarefa criada.")
                st.rerun()
    card_close()

    card_open("Lista de tarefas")
    c1, c2 = st.columns(2)
    status_filter = c1.selectbox("Filtrar status", ["todos", "pending", "in_progress", "done", "canceled"])
    priority_filter = c2.selectbox("Filtrar prioridade", ["todas", "low", "medium", "high", "critical"])
    df = list_tasks(event_id, status_filter, priority_filter)
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        task_id = st.selectbox("Editar tarefa", df["id"].astype(int).tolist(), format_func=lambda x: df.loc[df["id"] == x, "title"].iloc[0])
        row = df[df["id"] == task_id].iloc[0]
        c1, c2, c3 = st.columns(3)
        new_status = c1.selectbox("Novo status", ["pending", "in_progress", "done", "canceled"], index=["pending", "in_progress", "done", "canceled"].index(row["status"]))
        new_priority = c2.selectbox("Nova prioridade", ["low", "medium", "high", "critical"], index=["low", "medium", "high", "critical"].index(row["priority"]))
        new_owner = c3.text_input("Responsável", value=row.get("owner") or "")
        if st.button("Atualizar tarefa"):
            update_task(event_id, int(task_id), status=new_status, priority=new_priority, owner=new_owner)
            st.success("Tarefa atualizada.")
            st.rerun()
        if st.button("Excluir tarefa selecionada"):
            delete_task(event_id, int(task_id))
            st.warning("Tarefa excluída.")
            st.rerun()
    card_close()
