# PATCH Refinamento Produto

## O que foi melhorado
- Autenticação demo com helpers de perfil e fallback seguro.
- Painel dos noivos com UX premium, cards e empty states sem dataframe cru.
- Formulários dinâmicos com CRUD de campos, ativação, ordenação, respostas agrupadas e CSV.
- Portal do convidado com respostas anteriores, campos ativos, validação de link e resumo de envio.
- WhatsApp com preview, dry-run seguro, logs auditáveis, tentativas e reenfileiramento.
- Financeiro com CRUD de fornecedores/despesas, status ampliados, filtros, KPIs e CSV.
- Documentos com categoria, descrição, fornecedor, download, nome interno e exclusão lógica.
- Mapa de mesas com ocupação, conflitos, grupos separados e exportação CSV.
- Insights com severidade, ação, página relacionada e contagem.
- Testes básicos e limpeza de produção.

## Como testar
```bash
python -m compileall .
pytest
streamlit run app.py
uvicorn public_app:app --reload --port 8000
```

## Páginas afetadas
- app.py
- pages/client_dashboard.py
- pages/forms.py
- pages/financial.py
- pages/documents.py
- pages/mesas.py
- public_app.py

## Próximos passos para SaaS real
- Login real com senha/OAuth e tenants.
- Banco PostgreSQL com Alembic.
- Worker assíncrono para WhatsApp.
- Storage externo para documentos.
- Auditoria completa por usuário.
