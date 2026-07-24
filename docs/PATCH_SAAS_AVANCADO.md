# PATCH SaaS Avançado

Este patch adiciona uma camada avançada de plataforma SaaS sem remover o Streamlit existente.

## Incluído

- Backend FastAPI em `backend/`
- Schemas Pydantic para auth, eventos, convidados, formulários, campanhas e financeiro
- Autenticação JWT com refresh token
- Middleware de `current_user` e `current_tenant`
- Workflow engine com regras e execuções
- Scheduler simples com lock para evitar duplicação
- Analytics profissionais de evento e campanhas
- Onboarding SaaS em Streamlit
- Importação avançada CSV/XLSX/VCF com preview, validação, dedupe e merge
- API client em `frontend/api_client.py`
- Auditoria avançada com filtros
- Docker preparado para Streamlit + FastAPI + Postgres

## Como rodar Streamlit

```bash
streamlit run app.py
```

## Como rodar FastAPI

```bash
uvicorn backend.main:app --reload --port 8000
```

Login seed:

- email: `admin@local`
- senha: `admin123`

## Como testar

```bash
python -m compileall .
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

## Próximos passos SaaS real

- Trocar `SECRET_KEY` em produção
- Configurar domínio e HTTPS
- Criar política real de CORS
- Adicionar worker separado para scheduler
- Evoluir Alembic para migrations versionadas por release
