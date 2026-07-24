# Lumyra — Final Portfolio Release

## Incluído neste patch

- Limpeza de cache, logs e bancos locais.
- `.gitignore` profissional para GitHub público.
- README premium com arquitetura, comandos, badges e screenshots.
- Placeholders de screenshots.
- Seed de dados demo controlados.
- Docker Compose revisado com nomes Lumyra.
- `.env.example` completo.
- Documentação de arquitetura, deploy e demo mode.

## Validações recomendadas

```bash
python -m compileall .
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
cd frontend_web
npm install
npm run build
npm run lint
```

## Antes do GitHub

- Substituir screenshots placeholders por imagens reais.
- Confirmar que nenhum `.env`, `.db`, `.sqlite3`, `storage/` ou `logs/` foi versionado.
- Rodar o seed demo em ambiente local, não commitar banco gerado.
