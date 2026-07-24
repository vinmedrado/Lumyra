# Sugestões Musicais — Lumyra

Este patch adiciona a experiência **Sugira uma música** ao módulo de playlist do casamento.

## O que foi incluído

- Tabela `event_music_suggestions`.
- Migration `0007_event_music_suggestions`.
- Service `services/music_suggestion_service.py`.
- Router FastAPI `/music-suggestions`.
- Formulário público no portal do convidado.
- Lista de sugestões na área dos noivos.
- Curadoria na área admin/assessoria.
- Dados demo no `scripts/seed_demo_data.py`.

## Fluxo

1. Noivos/assessoria cadastram o link da playlist do Spotify.
2. Convidado acessa o portal.
3. Convidado sugere música, artista e mensagem opcional.
4. Noivos/assessoria visualizam as sugestões.
5. Sugestões podem ser marcadas como:
   - `pending`
   - `approved`
   - `rejected`
   - `added`

## API

### Criar sugestão pública

```http
POST /music-suggestions/public
```

Payload:

```json
{
  "tenant_id": 1,
  "event_id": 1,
  "guest_name": "Marina Oliveira",
  "song_name": "Perfect",
  "artist_name": "Ed Sheeran",
  "message": "Essa combina com os noivos."
}
```

### Listar sugestões

```http
GET /music-suggestions?event_id=1
```

### Atualizar status

```http
PATCH /music-suggestions/{id}/status
```

Payload:

```json
{
  "status": "approved"
}
```

## Observação

Este patch não usa OAuth nem API oficial do Spotify. A playlist continua sendo criada pelos noivos no Spotify, e o Lumyra exibe link, QR Code, embed/experiência visual e coleta sugestões musicais para curadoria manual.
