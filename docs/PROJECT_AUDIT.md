# Auditoria técnica do projeto Lumyra

Data da revisão: 24 de julho de 2026.

## Resumo executivo

O Lumyra tem visão de produto, abrangência funcional e identidade visual acima da
média de projetos de portfólio. A arquitetura demonstra experiência com frontend
API-first, backend modular, autenticação, multi-tenancy, jobs, WebSocket e domínio
de negócio real.

O nível atual do repositório é **pleno forte, com sinais de senioridade em produto,
arquitetura e experiência de demonstração**. Ainda não deve ser apresentado como
um SaaS pronto para produção: duas abordagens de persistência seguem em transição e
há lacunas operacionais a fechar antes de atender clientes reais.

Para portfólio, o projeto está publicado no GitHub e no Netlify, com CI e deploy
contínuo validados.

## Inventário revisado

- 298 arquivos rastreáveis no momento da auditoria.
- React 19, TypeScript, Vite, Tailwind, Axios e Wouter em `frontend_web/`.
- FastAPI, JWT, WebSocket, routers e schemas em `backend/`.
- Serviços de domínio em `services/` e persistência em `repositories/` e `db/`.
- Streamlit legado em `pages/`, preservado como painel operacional.
- Worker e scheduler em `workers/` e `services/`.
- Testes Python em `tests/` e testes React com Vitest/Testing Library.
- Docker Compose com API, frontend, Streamlit, worker, scheduler e profile
  opcional de PostgreSQL.
- CI do GitHub, configuração do Netlify, Dockerfiles e documentação de deploy.

## Avaliação por dimensão

| Dimensão | Estado | Leitura |
|---|---:|---|
| Visão de produto e domínio | 9/10 | Fluxos e personas coerentes, forte valor demonstrável |
| UI/identidade visual | 8/10 | Design system consistente e apresentação premium |
| Arquitetura | 7/10 | Boa separação, mas persistência ainda em consolidação |
| Backend e segurança | 7/10 | JWT, tenant boundary e portal público testados |
| Frontend funcional | 8/10 | Todos os módulos principais possuem dados e interações integradas entre personas |
| Testes e qualidade | 7/10 | Backend, componentes, lint, typecheck e build automatizados |
| DevOps/deploy | 8/10 | GitHub Actions e deploy contínuo do Netlify validados |
| Prontidão para produção | 5/10 | Requer PostgreSQL, observabilidade, storage e hardening |

## Melhorias aplicadas durante a auditoria

- Corrigida falha de sintaxe que bloqueava a compilação Python.
- Consolidado SQLite como modo de portfólio entre legado e SQLAlchemy.
- PostgreSQL isolado em profile até a migração estar concluída.
- Dependências frontend fixadas e instalação reprodutível com `npm ci`.
- React Router removido após advisory sem correção; rotas migradas para Wouter.
- CORS configurável e WebSocket protegido por autenticação e escopo de tenant.
- Portal público agora possui API JSON real, convite individual/familiar e RSVP.
- Dashboards principais, autenticação e lista de convidados conectados à API.
- Adicionados testes de integração do portal público e testes de componentes React.
- Adicionados ESLint real, typecheck, testes, build e auditoria de dependências na CI.
- Adicionados `.dockerignore`, `.editorconfig`, `.nvmrc`, Netlify e documentação ADR.
- Substituídas as 17 rotas genéricas por módulos demonstráveis e responsivos.
- Criado estado demo versionado em `localStorage`, com sincronização entre abas.
- Integrados RSVP, sugestões musicais, mesas, financeiro, documentos, campanhas,
  notificações, activity feed e auditoria.
- Publicados repositório GitHub e frontend Netlify com deploy contínuo.

## Riscos e dívida técnica restantes

### Prioridade alta — antes de chamar de produto

1. Finalizar a migração de todos os repositórios para SQLAlchemy/PostgreSQL e
   testar isolamento multi-tenant no banco de produção.
2. Separar dependências Python por runtime/dev e gerar lock reprodutível.
3. Substituir credenciais e providers de demonstração em um eventual ambiente real.
4. Publicar o backend em Render, Railway, Fly.io ou infraestrutura equivalente;
   o Netlify hospeda somente o frontend estático.

### Prioridade média — antes de divulgar amplamente

1. Criar testes E2E Playwright para login, dashboard e RSVP familiar.
2. Gerar screenshots reais e um vídeo curto; a galeria ainda não foi produzida.
3. Adicionar licença, política de segurança e template de pull request.
4. Configurar logs estruturados, rastreamento de erros e métricas.
5. Revisar acessibilidade por teclado, contraste e estados de erro em todas as telas.

### Evolução de produto

1. Storage S3-compatible e URLs assinadas para documentos.
2. Provider real de WhatsApp com webhooks idempotentes.
3. RBAC granular, rate limiting e trilha de auditoria imutável.
4. Backup, restore, retenção e política de privacidade/LGPD.
5. Deploy previews, ambientes separados e migração automatizada.

## Estratégia recomendada de publicação

```text
GitHub
  └─ GitHub Actions: backend tests + frontend lint/test/build/audit

Netlify
  └─ frontend_web/dist
       ├─ VITE_API_BASE_URL=https://api.seu-dominio
       └─ VITE_WS_URL=wss://api.seu-dominio/ws

Backend provider
  └─ FastAPI + worker + scheduler + PostgreSQL + storage persistente
```

Na demonstração pública atual, o Netlify entrega somente o frontend e os dados
fictícios são persistidos no navegador. O backend permanece no GitHub como evidência
arquitetural e pode ser executado localmente. Para uma versão comercial, publicar a
API em um provedor de containers e não usar SQLite efêmero.

## Critério de release de portfólio

- CI verde em `main`.
- Nenhum segredo ou banco rastreado.
- Landing, login, dashboard admin, dashboard cliente e RSVP funcionando.
- Link público do frontend documentado no README.
- Screenshots reais, descrição curta do problema e decisões arquiteturais.
- Aviso explícito de que o backend não está hospedado na demonstração pública.

## Comandos de qualidade

```bash
python -m compileall -q backend components core db integrations migrations models pages repositories scripts services tests workers app.py public_app.py
python -m pytest -q

cd frontend_web
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
npm audit --omit=dev --audit-level=high

docker compose config --quiet
```
