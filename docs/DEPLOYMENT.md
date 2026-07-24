# Lumyra — Deployment

## Local com SQLite

```bash
cp .env.example .env
pip install -r requirements.txt
python scripts/seed_demo_data.py
uvicorn backend.main:app --reload
streamlit run app.py
cd frontend_web && npm install && npm run dev
```

## Local com Docker/SQLite persistente

```bash
cp .env.example .env
docker compose up --build
```

O volume `app_data` mantém o banco compartilhado entre API, Streamlit, worker e
scheduler. O serviço PostgreSQL está isolado no profile `postgres` enquanto a
migração descrita em `ADR-001-PERSISTENCE-CONSOLIDATION.md` não for concluída.

## Portfólio

Ajuste variáveis:

- `APP_ENV=demo`
- `SECRET_KEY` forte
- `DATABASE_URL=sqlite:////app/data/event_erp.sqlite3`
- `STORAGE_PATH` persistente
- provider real de WhatsApp

### Frontend no Netlify

O `netlify.toml` da raiz já define `frontend_web` como base, executa
`npm run build`, publica `dist` e trata as rotas da SPA.

No painel do Netlify, configure antes do deploy:

- `VITE_API_BASE_URL=https://api.seu-dominio`
- `VITE_WS_URL=wss://api.seu-dominio/ws`
- `VITE_DEMO_MODE=true`

FastAPI, worker, scheduler e banco não executam no Netlify. Publique esses
componentes em um provedor de containers e inclua a URL final do Netlify em
`CORS_ALLOWED_ORIGINS`.

## Produção futura

PostgreSQL só deve ser habilitado após todos os repositórios usarem SQLAlchemy e
a suíte passar nos dois bancos.

## Migrations

```bash
alembic upgrade head
```

## Workers

```bash
python -m workers.worker --sleep 10
```

## Scheduler

```bash
python -c "from services.scheduler_service import run_scheduler_tick; run_scheduler_tick()"
```

## Healthcheck

- API: `/health`
- WebSocket: `/ws`
- Streamlit: porta `8501`
- Frontend: porta `5173` no compose
