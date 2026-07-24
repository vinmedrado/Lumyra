# Checklist para subir no GitHub

## Não subir
- `.env` real ou qualquer arquivo com tokens/senhas.
- `data/*.sqlite`, `data/*.sqlite3`, `data/*.db`.
- `__pycache__/`, `*.pyc`, logs pesados e arquivos temporários.
- Documentos privados reais de clientes/eventos.

## Validação local
```bash
python -m compileall .
python -m pytest -q
cd frontend_web
npm ci
npm run lint
npm run test
npm run build
npm audit --omit=dev --audit-level=high
```

## Rodar local
```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Rodar API e portal público local
```bash
uvicorn backend.main:app --reload
# em outro terminal
cd frontend_web && npm run dev
```

## Produção
- Configurar `.env` no servidor, não no GitHub.
- Usar banco persistente fora do repositório.
- Configurar `GUEST_PORTAL_BASE_URL` com domínio real.
- Validar Evolution API antes de campanhas em massa.
- No Netlify, definir `VITE_API_BASE_URL` e `VITE_WS_URL` apontando para o
  backend publicado em outro provedor.
