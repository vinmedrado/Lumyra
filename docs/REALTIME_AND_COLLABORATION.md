# Realtime, Notificações e Colaboração

Este patch adiciona uma camada incremental de experiência viva para a plataforma, sem remover Streamlit, FastAPI ou o frontend React existente.

## Arquitetura WebSocket

- `backend/realtime/manager.py`: gerencia conexões, rooms por tenant e rooms por evento.
- `backend/realtime/websocket_router.py`: expõe `/ws` com autenticação opcional por JWT e fallback por `tenant_id` para demo.
- `backend/realtime/events.py`: padroniza payloads realtime.

Eventos suportados:

- `guest_updated`
- `rsvp_updated`
- `message_sent`
- `message_failed`
- `financial_updated`
- `insight_created`
- `job_completed`
- `notification_created`
- `activity_created`
- `presence_updated`

## Frontend realtime

- `frontend_web/src/services/realtime.ts`: client WebSocket com reconexão automática e fallback visual.
- `frontend_web/src/hooks/useRealtime.ts`: hook para dashboards e command center.
- `LiveIndicator`: badge de conexão ao vivo.

## Notification Center

Backend:

- `services/notification_service.py`
- `backend/routers/notifications.py`
- tabela `notifications`

Frontend:

- `NotificationBell`
- `/admin/notifications`
- toasts/dropdown preparados para eventos realtime

## Activity Feed

Backend:

- `services/activity_service.py`
- tabela `activity_feed`

Frontend:

- `/admin/activity`
- timeline operacional
- pronto para receber broadcast realtime

## Presença online e colaboração

Backend:

- `services/presence_service.py`
- tabela `online_users`
- tabela `entity_locks`

Recursos:

- usuários online por tenant
- `last_seen`
- página atual
- lock otimista simples para entidades editáveis

## Dark mode e polish visual

- `ThemeProvider`
- toggle no topbar
- persistência em `localStorage`
- suporte Tailwind `darkMode: 'class'`
- loading skeletons, transitions e hover states

## Command Center Realtime

Nova rota:

- `/admin/command-center`

Mostra:

- status live
- eventos recebidos
- usuários online
- alertas vivos
- activity feed
- jobs e workflows em visão executiva

## Docker/deploy

O WebSocket roda dentro do próprio serviço FastAPI (`api`) no endpoint `/ws`.

No compose atual:

- `api`: FastAPI + WebSocket
- `frontend_web`: React/Vite servido por Nginx
- `worker`: workers de jobs
- `scheduler`: scheduler
- `postgres`: banco
- `nginx`: reverse proxy opcional em profile production

Variável relevante no frontend:

```env
VITE_API_BASE_URL=http://localhost:8000
```

O client converte automaticamente `http` para `ws` ao conectar no WebSocket.

## Como testar

Backend:

```bash
python -m compileall .
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

Frontend:

```bash
cd frontend_web
npm install
npm run build
npm run lint
```

## Próximos passos reais

- Persistir todos os broadcasts em outbox para entrega garantida.
- Adicionar Redis Pub/Sub para múltiplas réplicas da API.
- Trocar lock otimista simples por versão de linha (`updated_at` + `version`).
- Criar E2E com Playwright para portal convidado e notification center.
