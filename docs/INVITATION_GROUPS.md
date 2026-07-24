# Convites individuais e convites família/grupo

O Lumyra agora diferencia dois tipos de convite no portal do convidado:

- **Convite individual**: usado quando a pessoa foi convidada sozinha. Exemplo: `Marina Oliveira`.
- **Convite família/grupo**: usado quando um convite representa várias pessoas. Exemplo: `Luzia & Família`.

## Experiência no portal

Quando o convite é família/grupo, o portal mostra a lista de pessoas vinculadas ao mesmo convite e permite confirmar cada uma separadamente.

Exemplo:

- Luzia Oliveira — confirma presença
- Roberto Oliveira — confirma presença
- Ana Clara Oliveira — responder depois
- Pedro Oliveira — não irá

Quando o convite é individual, o portal mantém a experiência simples, exibindo apenas a pessoa convidada.

## Campos suportados

A estrutura passa a aceitar:

- `invitation_type`: `individual` ou `family`
- `invitation_label`: nome exibido no convite, como `Luzia & Família`
- `group_name`: agrupamento interno/familiar já existente

## Importação

A importação continua compatível com os campos antigos. Se existir coluna de convite, o Lumyra aproveita:

- `convite`
- `nome_convite`
- `tipo_convite`
- `grupo`
- `familia`

Se não houver esses campos, o sistema mantém comportamento individual por padrão.
