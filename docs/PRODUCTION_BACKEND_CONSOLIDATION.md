# Production Backend Consolidation

Este patch consolida a base técnica criada nos patches SaaS anteriores sem remover o Streamlit e sem alterar a UX existente.

## Principais mudanças

- `db/session.py`, `db/base.py` e `db/models.py` com camada SQLAlchemy pronta para SQLite local e PostgreSQL em produção.
- `user_sessions` para refresh token com rotação e revogação no logout.
- `workers/worker.py` e `workers/tasks.py` para execução separada de jobs.
- `services/job_service.py` com fila, lock, retry, prioridade, `locked_by`, `result_json` e `error_message`.
- `services/scheduler_service.py` agora cria jobs e executa regras agendadas com lock simples.
- `services/workflow_service.py` executa ações reais criando jobs, insights, reenfileiramento e marcação de prioridade.
- `analytics_snapshots` e `services/analytics_snapshot_service.py` para histórico de RSVP, mensagens, financeiro e ocupação de mesas.
- Endpoints principais com paginação/filtros: convidados, logs de mensagens, documentos e despesas.
- Middleware de `request_id` e logs JSON estruturados.
- Docker Compose com `app`, `api`, `worker`, `scheduler` e `postgres`.

## Rodar local com SQLite

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m compileall .
pytest
streamlit run app.py
```

A configuração padrão usa:

```env
DATABASE_URL=sqlite:///data/event_erp.db
```

## Rodar com PostgreSQL

```bash
docker compose up -d postgres
set DATABASE_URL=postgresql+psycopg2://event_erp:event_erp@localhost:5432/event_erp
alembic upgrade head
streamlit run app.py
```

## Rodar FastAPI

```bash
uvicorn backend.main:app --reload --port 8000
```

## Rodar worker

```bash
python -m workers.worker --sleep 10
```

Para processar um único job:

```bash
python -m workers.worker --once
```

## Rodar scheduler

```bash
python -c "from services.scheduler_service import run_scheduler_tick; print(run_scheduler_tick())"
```

## Migrations

```bash
alembic upgrade head
alembic downgrade -1
```

O arquivo `migrations/versions/0004_backend_consolidation.py` adiciona sessões, snapshots históricos e colunas operacionais de jobs/workflows/auditoria.

## Testes

```bash
python -m compileall .
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

## Arquitetura final

```text
Streamlit UI
  ├── pages/
  ├── components/ui/
  └── frontend/api_client.py

FastAPI Backend
  ├── backend/main.py
  ├── backend/routers/
  ├── backend/schemas/
  └── backend/middleware/

Core SaaS
  ├── db/session.py
  ├── db/models.py
  ├── services/job_service.py
  ├── services/scheduler_service.py
  ├── services/workflow_service.py
  ├── services/analytics_snapshot_service.py
  └── workers/

Infra
  ├── Dockerfile
  ├── docker-compose.yml
  ├── alembic.ini
  └── migrations/
```

## Próximos passos reais de produção

- Trocar o modo demo por login obrigatório por tenant.
- Configurar secrets fora do repositório.
- Adicionar backup do PostgreSQL.
- Monitorar worker/scheduler com logs centralizados.
- Separar deploy de Streamlit e API em serviços independentes.
