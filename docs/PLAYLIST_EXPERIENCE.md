# Lumyra Playlist Experience

Este patch adiciona uma experiência musical incremental ao Lumyra sem alterar os fluxos existentes.

## O que foi acrescentado

- Configuração de playlist Spotify por evento.
- QR Code público para convidados salvarem/acessarem a playlist.
- Card premium no portal dos convidados.
- Página dedicada para noivos em `/client/playlist`.
- Página administrativa em `/admin/playlist`.
- Endpoint FastAPI `/playlists/{event_id}` e `PUT /playlists`.
- Migration `0006_event_playlist_experience`.
- Serviço isolado `services/playlist_service.py`.

## Mensagem padrão

> Quem faz a festa é você: salve a playlist do casamento e compartilhe suas melhores músicas para esse momento ficar ainda mais inesquecível.

## Aviso de etiqueta

> Pedimos apenas bom senso e carinho: escolha músicas que combinem com o clima do casamento e respeitem todos os convidados.

## Observação

A geração do QR Code usa uma URL de imagem externa no frontend para evitar adicionar novas dependências e reduzir risco de quebra. Em produção, pode ser substituída por geração interna de QR Code.
