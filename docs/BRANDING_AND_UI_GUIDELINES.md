# Lumyra — Branding & UI Guidelines

**Nome oficial:** Lumyra
**Subtítulo:** Modern Event Operations Platform

Este patch aplica a identidade visual Lumyra no frontend React, Streamlit quando possível, portal público, favicon, manifest/PWA e documentação.

## Cores oficiais

| Token | Uso | Hex |
|---|---|---|
| Midnight Black | fundos premium, textos fortes, dark mode | `#181210` |
| Lumyra Purple | marca, botões primários, sidebar, foco | `#4B1D95` |
| Lumyra Purple Light | gradientes, estados hover, glow | `#8B5CF6` |
| Elegant Gold | destaques, CTA secundário premium, badges | `#B88937` |
| Elegant Gold Light | fundos suaves e detalhes | `#F8E7B1` |
| Ice White | fundo claro base | `#F7F8FB` |
| Soft Lilac | cards suaves, empty states e highlights | `#F1ECFF` |

## Tipografia

- **Display:** Playfair Display para hero, títulos emocionais e áreas premium.
- **Interface:** Inter para navegação, tabelas, botões e leitura operacional.

## Uso da logo

Assets oficiais em:

```text
frontend_web/src/assets/branding/
  lumyra-logo.svg
  lumyra-logo-dark.svg
  lumyra-icon.svg
  lumyra-mark.svg
  lumyra-brand-board.jpg
```

Regras:

- Usar `lumyra-logo.svg` em fundo claro.
- Usar `lumyra-logo-dark.svg` em fundo escuro.
- Usar `lumyra-icon.svg` como favicon, loading e marca reduzida.
- Evitar baixa opacidade ou contraste ruim.
- Manter respiro visual ao redor da marca.

## Componentes UI

Os componentes foram refinados para usar:

- bordas arredondadas grandes;
- sombras suaves;
- hover com elevação discreta;
- estados de foco acessíveis;
- dark mode compatível;
- `brand`, `gold`, `ink` e `ice` como tokens principais.

Componentes afetados:

- `Button`
- `Card`
- `MetricCard`
- `PageHeader`
- `EmptyState`
- `LoadingState`
- `Sidebar`
- `Topbar`

## Landing page

A landing em `/` agora apresenta Lumyra como produto SaaS premium com:

- hero section com logo;
- CTA para demo;
- portal do convidado;
- módulos principais;
- bloco comercial final;
- identidade visual Lumyra.

## Dark mode

Dark mode usa Midnight Black, Lumyra Purple e Elegant Gold com contraste reforçado.

## PWA / Meta

Arquivos adicionados:

```text
frontend_web/public/favicon.svg
frontend_web/public/logo.svg
frontend_web/public/manifest.json
```

`index.html` foi atualizado com:

- title oficial;
- meta description;
- OpenGraph básico;
- theme-color;
- favicon;
- manifest.

## Streamlit

O Streamlit foi preservado e recebeu apenas refinamento visual seguro:

- título Lumyra;
- subtítulo oficial;
- paleta mais próxima da marca;
- sidebar e hero com cores oficiais.

## Próximos passos visuais

1. Substituir o SVG placeholder por arquivos finais exportados por designer.
2. Criar screenshots reais da aplicação para a landing.
3. Criar kit de ícones em PNG 192/512 para PWA completo.
4. Validar contraste com ferramentas WCAG.
5. Criar guia comercial com mockups para portfólio.
