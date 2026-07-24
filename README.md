# Lumyra

**Modern Event Operations Platform**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=111)
![TypeScript](https://img.shields.io/badge/TypeScript-API--first-3178C6?logo=typescript&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Portfolio%20Mode-003B57?logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Deploy--ready-2496ED?logo=docker&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-Realtime-8B5CF6)
[![Netlify](https://img.shields.io/badge/Live%20Demo-Netlify-00C7B7?logo=netlify&logoColor=white)](https://lumyra-events.netlify.app)

Lumyra é uma plataforma SaaS para operação de eventos sociais e corporativos, conectando assessorias, noivos/clientes e convidados em uma experiência moderna com RSVP, WhatsApp, formulários dinâmicos, mapa de mesas, financeiro, documentos, analytics, workflows, workers e colaboração em tempo real.

> Projeto preparado para portfólio premium, demonstração técnica, GitHub público e evolução futura para produto SaaS real.

> Estado atual: os fluxos de login, dashboards, convidados e RSVP público usam a
> API real. Parte dos módulos administrativos e da área dos noivos ainda representa
> o roadmap com estados de integração. Consulte a
> [auditoria técnica](docs/PROJECT_AUDIT.md).

## Live Demo

**[Abrir Lumyra no Netlify](https://lumyra-events.netlify.app)**

O deploy público executa o frontend em modo de portfólio, sem backend hospedado.
Use os acessos de demonstração na tela de login ou abra o
[convite familiar interativo](https://lumyra-events.netlify.app/guest/lumyra-demo-invitation-token).
As interações públicas são simuladas somente no navegador e não armazenam dados.
Cada atualização da branch `main` validada no GitHub dispara automaticamente um
novo build de produção no Netlify.

---

## Features

- **Frontend React API-first** com Vite, TypeScript, Tailwind e design system próprio.
- **Streamlit admin preservado** para operação interna e demos técnicas rápidas.
- **FastAPI backend** com rotas para autenticação, eventos, convidados, formulários, campanhas, financeiro, documentos, insights e healthcheck.
- **SQLite consistente para o portfólio**, compartilhado pelo legado e pela camada SQLAlchemy.
- **Multi-tenant** com tenants, usuários, roles e isolamento por cliente.
- **JWT auth** com access token, refresh token e sessões.
- **WebSocket realtime** para dashboards vivos, notificações, presença online e command center.
- **Workers e scheduler** para campanhas, retries, snapshots de analytics, insights e exportações.
- **Notification Center** e **Activity Feed** para colaboração operacional.
- **Portal dos noivos** com experiência premium, emocional e não técnica.
- **Portal público do convidado** mobile-first para RSVP e respostas dinâmicas.
- **WhatsApp auditável** com templates, logs, retries e status por convidado.
- **Documentos e financeiro** com estrutura preparada para produção.
- **Demo mode** para apresentação sem depender de login real.

---

## Architecture

```text
frontend_web/     React + Vite + TypeScript + Tailwind
backend/          FastAPI + routers + schemas + JWT + WebSocket
services/         Business services, analytics, scheduler, notifications
workers/          Background worker and task execution
db/               SQLAlchemy engine, session, Base and models
migrations/       Alembic migrations
pages/            Streamlit admin/internal panel
storage/          Local file storage structure, ignored by Git
docs/             Technical documentation and screenshots
```

```text
React UI ──HTTP/JWT──▶ FastAPI ──Repositories──▶ SQLite (portfolio)
   │                       │                         │
   └──WebSocket────────────┘                         │
                           │                         │
                    Workers/Scheduler ───────────────┘
```

---

## Screenshots

> Galeria em preparação para a primeira publicação. O release de portfólio deve
> incluir capturas reais da landing, dashboard admin, área dos noivos, convite
> digital, analytics e command center realtime.

---

## Running Locally

### Backend / Streamlit

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python scripts/seed_demo_data.py
uvicorn backend.main:app --reload
```

Em outro terminal:

```bash
streamlit run app.py
```

### Frontend

```bash
cd frontend_web
npm ci
npm run dev
```

Acesse:

- React demo: `http://localhost:5173`
- FastAPI: `http://localhost:8000`
- Streamlit admin: `http://localhost:8501`

---

## Docker Setup

```bash
cp .env.example .env
docker compose up --build
```

Serviços principais:

- `frontend_web`: React build servido via Nginx
- `api`: FastAPI + WebSocket
- `streamlit_admin`: painel interno Streamlit
- `worker`: execução de jobs
- `scheduler`: criação periódica de jobs/automações
- `app_data`: volume persistente do SQLite compartilhado

O serviço PostgreSQL existe somente no profile de migração e não é iniciado no
modo padrão:

```bash
docker compose --profile postgres up postgres
```

---

## API

Principais grupos de endpoints:

- `/auth/login`, `/auth/logout`, `/auth/me`, `/auth/refresh`
- `/events`
- `/guests`, `/guests/import`, `/guests/export`
- `/forms`, `/forms/responses`
- `/campaigns`, `/messages/logs`
- `/expenses`, `/vendors`
- `/documents`
- `/insights`
- `/analytics`
- `/public/guest/{token}`, `/public/guest/{token}/rsvp`
- `/health`

---

## Realtime

O backend possui WebSocket com rooms por tenant/evento e eventos como:

- `guest_updated`
- `rsvp_updated`
- `message_sent`
- `message_failed`
- `financial_updated`
- `insight_created`
- `job_completed`
- `notification_created`

---

## Frontend

O frontend moderno fica em `frontend_web/` e inclui:

- landing page SaaS
- login e demo mode
- área da assessoria/admin
- área dos noivos/clientes
- portal público do convidado
- design system Lumyra
- dark mode
- notification center
- realtime indicator

---

## Backend

O backend FastAPI convive com o Streamlit legado e fornece a API oficial para
evolução API-first. No modo de portfólio, o legado e o SQLAlchemy compartilham o
mesmo SQLite. A migração para PostgreSQL ainda está em andamento.

---

## Workers

Workers processam jobs como:

- envio de campanha WhatsApp
- retry de mensagens com erro
- geração de insights
- snapshots históricos de analytics
- exportações

---

## Deployment

O Docker Compose atual entrega o modo de portfólio com SQLite persistente. A
migração completa para PostgreSQL está documentada em
`docs/ADR-001-PERSISTENCE-CONSOLIDATION.md`.

Para produção real, ainda será necessário:

- `APP_ENV=production`
- `SECRET_KEY` forte
- conclusão da migração SQLAlchemy/PostgreSQL
- storage persistente
- domínio + HTTPS
- provider real de WhatsApp

Leia `docs/DEPLOYMENT.md`.

---

## Quality Gates

```bash
python -m pytest -q

cd frontend_web
npm run lint
npm run typecheck
npm run test
npm run build
npm audit --omit=dev --audit-level=high
```

Os mesmos gates são executados pelo GitHub Actions em pushes para `main` e pull
requests.

---

## Roadmap

- RBAC granular por permissão.
- Integração real com gateway de pagamento.
- Storage S3-compatible.
- Observabilidade com OpenTelemetry.
- Deploy previews e promoção automatizada após a CI.
- Testes E2E com Playwright.
- Billing e assinatura por tenant.

---

## Demo Mode

Contas sugeridas para demonstração local após seed:

| Perfil | E-mail | Senha |
|---|---|---|
| Assessoria | `admin@lumyra.demo` | `admin123` |
| Noivos | `noivos@lumyra.demo` | `admin123` |
| Staff | `staff@lumyra.demo` | `admin123` |

Também há botões visuais de demo no frontend React para apresentação rápida sem login real.



# 🎵 Experiência Interativa para Convidados

O Lumyra transforma a gestão de eventos em uma experiência moderna, emocional e interativa para os convidados.

Os convidados não são apenas participantes do evento — eles passam a fazer parte da celebração.

## Playlist do Casamento com Spotify

- Integração via link da playlist do Spotify
- Geração automática de QR Code
- Preview incorporado da playlist
- Experiência mobile-first
- Acesso rápido via QR Code
- Interface premium para convidados

## Sugestões Musicais Colaborativas

Os convidados podem sugerir músicas diretamente pelo portal do evento.

### Funcionalidades para convidados
- Sugestão de músicas
- Nome da música e artista
- Mensagem personalizada opcional
- Feedback visual após envio

### Funcionalidades para noivos/administração
- Aprovar ou recusar sugestões
- Curadoria musical do evento
- Controle de músicas adicionadas
- Gestão da participação dos convidados

## Experiência Mobile

Toda a experiência foi otimizada para smartphones, permitindo interação rápida durante:
- convites digitais
- pista de dança
- recepção
- celebração em tempo real

## Visão do Produto

O Lumyra evolui além da gestão operacional tradicional e se posiciona como uma plataforma moderna de experiências premium para eventos.


## 💌 Convites individuais e familiares

O Lumyra suporta dois formatos de convite no portal do convidado:

- **Convite individual**: ideal para convidados que irão sozinhos, como `Marina Oliveira`.
- **Convite família/grupo**: ideal para famílias ou grupos, como `Luzia & Família`.

No convite familiar, o portal exibe as pessoas vinculadas ao mesmo convite e permite confirmar presença individualmente para cada integrante. Isso deixa o fluxo mais próximo da realidade de casamentos e eventos sociais premium.

Também foram refinados os contrastes visuais do portal para manter leitura clara sobre o layout roxo premium do Lumyra.
