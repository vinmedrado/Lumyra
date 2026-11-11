# QA e revisão de segurança — novembro de 2026

## Alterações validadas
- Novas senhas exigem `passlib[bcrypt]`; se o componente não estiver disponível, a aplicação falha explicitamente, em vez de criar hash SHA-256 sem salt.
- A leitura de hashes SHA-256 antigos foi preservada para compatibilidade e futura migração de credenciais.
- A suíte verifica limites entre tenants, acesso ao portal público, RSVP, tokens de convidados, WebSocket e os caminhos de hash.
- Corrigidos testes que dependiam de eventos de setembro/outubro de 2026, já passados. Apenas convites sintéticos de demonstração têm sua data atualizada quando vencida; eventos reais encerrados continuam bloqueados.
- `axios` atualizado de **1.18.1 para 1.21.1**, com lockfile reproduzível; `npm audit --omit=dev --audit-level=high` encerrou a auditoria de produção sem vulnerabilidades reportadas.

## Limites
- A leitura de hashes legados deve ser eliminada apenas com um plano de migração e de atualização das credenciais reais, sem bloquear contas.
- Auditoria npm de produção não cobre dependências de desenvolvimento: a árvore de desenvolvimento ainda pode conter alertas.
- Os testes não validam autorização em um deploy real, provedores WhatsApp, segredo de produção ou integrações externas.
- Nenhuma base real, conta, evento ou configuração de produção foi modificada nesta revisão.
