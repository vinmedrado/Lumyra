# PATCH Produção, Escalabilidade e Base SaaS

## Objetivo
Este patch adiciona uma camada incremental de produção ao sistema Streamlit existente, preservando UX, páginas e regras atuais.

## Melhorias adicionadas

### PostgreSQL Ready
- `core/settings.py` centraliza variáveis de ambiente.
- `db/session.py` cria engine SQLAlchemy compatível com SQLite local e PostgreSQL produção.
- `DATABASE_URL` passa a controlar o banco.

### Alembic
- `alembic.ini`
- `migrations/env.py`
- migrations iniciais para base SaaS e colunas de tenant/auth.

### Auth persistente
- `services/security_service.py` com `hash_password()` e `verify_password()`.
- `services/auth_service.py` mantém modo demo, mas adiciona login persistente por usuário salvo no banco.
- Seed admin local: `admin@local` / `admin123` para desenvolvimento.

### Multi-tenant
- Tabela `tenants`.
- `tenant_id` incremental em eventos, convidados, formulários, documentos, financeiro, mensagens e campanhas.
- Helper `get_current_tenant()`.

### Storage organizado
- `services/storage_service.py`.
- Estrutura `storage/tenants/tenant_x/documents` e `storage/exports`.
- Nome interno com UUID para evitar sobrescrita.

### Jobs
- Tabela `background_jobs`.
- `services/job_service.py` com criação, atualização, execução assíncrona simples e listagem.

### Auditoria
- `services/audit_service.py`.
- Suporte a `tenant_id`, `user_id`, `metadata_json`.
- Base para registrar login, upload, exclusões, campanha e alterações financeiras.

### Healthcheck
- `pages/system_health.py`.
- `services/health_service.py`.
- Exibe banco, storage, jobs, mensagens, tenants, usuários e eventos.

### Exportações
- `services/export_service.py`.
- CSV para convidados, mesas, financeiro e respostas de formulário.

### Docker
- `Dockerfile`
- `docker-compose.yml` com app + PostgreSQL.

## Como testar local

```bash
python -m compileall .
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
streamlit run app.py
```

## Como rodar com Docker

```bash
cp .env.example .env
docker compose up --build
```

Acesse:

```text
http://localhost:8501
```

## Próximos passos para SaaS real

1. Criar tela de login completa e desativar `DEMO_MODE` em produção.
2. Migrar gradualmente os services legados para SQLAlchemy puro.
3. Adicionar controle de assinatura/plano por tenant.
4. Adicionar worker real para jobs, como Celery/RQ, quando houver volume.
5. Criar suíte de testes de integração com PostgreSQL.
6. Separar ambiente staging/produção com secrets reais.
