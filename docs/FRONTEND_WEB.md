# Frontend Web API-first

Este patch adiciona uma camada moderna `frontend_web/` sem remover Streamlit e sem recriar o backend.

## Objetivo

Criar uma demo SaaS vendável e separada por perfis:

- Assessoria/Admin: `/admin`
- Noivos/Clientes: `/client`
- Convidados/Portal público: `/guest/:token`
- Landing page: `/`
- Login/demo: `/login`

## Stack

- React + Vite
- TypeScript
- TailwindCSS
- Wouter
- Axios
- Componentes próprios de design system

## Estrutura

```txt
frontend_web/
  src/
    app/
    pages/
      admin/
      client/
      guest/
    components/
      ui/
      layouts/
    services/
    hooks/
    lib/
    types/
```

## Como rodar local

```bash
cd frontend_web
npm install
npm run dev
```

Acesse:

```txt
http://localhost:5173
```

## Variáveis

Crie `frontend_web/.env` baseado em `frontend_web/.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_DEMO_MODE=true
```

## FastAPI

Rode a API em outro terminal:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## Modo demo

Em `/login`, existem botões:

- Entrar como Assessoria
- Entrar como Noivos
- Ver portal do convidado

O login visual de assessoria/noivos não grava dados. O convite público de demonstração
usa a API e persiste o RSVP no banco local para demonstrar o fluxo ponta a ponta.

## Rotas criadas

### Público

- `/`
- `/login`
- `/guest/:token`

### Admin

- `/admin/dashboard`
- `/admin/events`
- `/admin/guests`
- `/admin/tables`
- `/admin/forms`
- `/admin/campaigns`
- `/admin/whatsapp`
- `/admin/financial`
- `/admin/documents`
- `/admin/analytics`
- `/admin/insights`
- `/admin/audit`
- `/admin/settings`

### Cliente

- `/client/dashboard`
- `/client/guests`
- `/client/rsvp`
- `/client/tables`
- `/client/timeline`
- `/client/documents`
- `/client/financial`
- `/client/messages`

## API Client

O client central fica em:

```txt
frontend_web/src/services/api.ts
```

Ele centraliza:

- auth
- tenants
- events
- guests
- forms
- messages
- campaigns
- insights
- documents
- financial
- analytics

Também possui interceptor para JWT, refresh token e logout automático em expiração.

## Design System

Componentes principais:

- Button
- Card
- MetricCard
- StatusBadge
- ProgressBar
- EmptyState
- PageHeader
- Sidebar
- Topbar
- LoadingState
- ErrorState
- FormInput
- Select
- Modal
- DataTable

## Docker

O `docker-compose.yml` recebeu o serviço `frontend_web` em porta `5173`.

```bash
docker compose up --build frontend_web api
```

## Próximos passos

- Completar as páginas CRUD que ainda usam estados de integração.
- Adicionar testes E2E com Playwright.
- Criar build de produção com domínio e HTTPS.
