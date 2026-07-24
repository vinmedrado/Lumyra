# ADR 001 — Consolidação da persistência

Status: aceito como transição para o portfólio.

## Contexto

O Lumyra possui duas implementações de persistência:

- o legado usa `sqlite3` diretamente em `repositories/database.py`;
- módulos novos usam SQLAlchemy, Alembic e `DATABASE_URL`.

Configurar PostgreSQL antes de migrar o legado divide os dados entre PostgreSQL
e `data/event_erp.sqlite3`. Essa combinação não é considerada suportada.

## Decisão atual

O ambiente local, CI e Docker de portfólio usam um único arquivo
`data/event_erp.sqlite3`.

- repositórios legados continuam funcionando;
- SQLAlchemy aponta para o mesmo arquivo;
- o lifespan da API cria somente as tabelas SQLAlchemy ainda ausentes;
- PostgreSQL permanece em um profile opcional, sem ser anunciado como pronto.

## Caminho para PostgreSQL

1. Criar interfaces de repositório por domínio.
2. Migrar autenticação, eventos e convidados para SQLAlchemy.
3. Migrar financeiro, documentos, mensagens e automações.
4. Remover DDL e migrations manuais de `repositories/database.py`.
5. Tornar Alembic a única autoridade de schema.
6. Executar a mesma suíte contra SQLite e PostgreSQL em CI.
7. Habilitar PostgreSQL no Compose somente após testes de isolamento por tenant,
   migrations `upgrade/downgrade` e smoke tests passarem.

## Critério de conclusão

Não pode existir import de `sqlite3` fora de ferramentas explícitas de migração,
e todos os routers devem depender de repositórios SQLAlchemy testados.
