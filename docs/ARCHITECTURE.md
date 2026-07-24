# Lumyra — Architecture

Lumyra usa uma arquitetura incremental, preservando o Streamlit admin e adicionando uma camada API-first moderna.

## Camadas

- **frontend_web/**: React + Vite + TypeScript para demo SaaS moderna.
- **backend/**: FastAPI como backend oficial.
- **pages/**: Streamlit admin preservado para operação interna.
- **services/**: regras de negócio compartilhadas.
- **db/**: SQLAlchemy, session e modelos.
- **workers/**: execução assíncrona de jobs.
- **migrations/**: Alembic.

## Fluxo

1. React autentica via FastAPI.
2. FastAPI valida JWT e tenant.
3. Serviços acessam dados via SQLAlchemy/repositories.
4. Workers processam tarefas de background.
5. WebSocket transmite eventos realtime para frontend.

## Multi-tenant

Entidades principais recebem `tenant_id`. Usuários só devem acessar dados do tenant ativo.

## Realtime

O backend publica eventos em rooms por tenant/evento. O frontend mantém reconexão automática e fallback visual.
