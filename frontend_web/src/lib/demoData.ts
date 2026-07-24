import type { EventSummary, Guest, GuestPortalContext, Insight, Metric } from '../types/domain';

export const demoEvent: EventSummary = { id: 1, name: 'Casamento Ana & João', date: '2026-09-12', location: 'Espaço Jardim Imperial', status: 'Em organização' };
export const demoMetrics: Metric[] = [
  { label: 'Convidados', value: 248, helper: 'lista atual', status: 'info' },
  { label: 'Confirmados', value: 184, helper: '74% de confirmação', trend: '+12 esta semana', status: 'success' },
  { label: 'Pendentes', value: 49, helper: 'precisam de contato', status: 'warning' },
  { label: 'Mensagens com erro', value: 6, helper: 'reenfileirar campanha', status: 'danger' }
];
export const demoGuests: Guest[] = [
  { id: 1, name: 'Mariana Souza', phone: '+55 11 99999-0001', rsvp_status: 'confirmed', table_name: 'Mesa 04', group_name: 'Família Souza' },
  { id: 2, name: 'Carlos Lima', phone: '+55 11 98888-0002', rsvp_status: 'pending', table_name: 'Sem mesa', group_name: 'Amigos faculdade' },
  { id: 3, name: 'Bianca Alves', phone: '+55 11 97777-0003', rsvp_status: 'declined', table_name: 'Mesa 08', group_name: 'Trabalho' }
];
export const demoInsights: Insight[] = [
  { severity: 'critical', title: 'Convidados sem mesa', message: '18 convidados confirmados ainda não têm mesa definida.', action: 'Revisar mapa', count: 18, related_page: '/admin/tables' },
  { severity: 'warning', title: 'RSVP pendente', message: '49 convidados ainda não responderam ao convite.', action: 'Enviar lembrete', count: 49, related_page: '/admin/campaigns' },
  { severity: 'info', title: 'Progresso saudável', message: 'A taxa de confirmação está acima de 70%.', action: 'Ver analytics', count: 74, related_page: '/admin/analytics' }
];

export const DEMO_GUEST_TOKEN = 'lumyra-demo-invitation-token';

export const demoGuestPortalContext: GuestPortalContext = {
  event: {
    id: 1,
    name: 'Casamento Ana & João',
    date: '12 de setembro de 2026 · 16h30',
    location: 'Espaço Jardim Imperial · São Paulo',
  },
  invitation: {
    tenant_id: 1,
    event_id: 1,
    guest_id: 101,
    type: 'family',
    label: 'Família Oliveira',
    members: [
      { id: 101, name: 'Marina Oliveira', category: 'Família', status: 'pending' },
      { id: 102, name: 'Rafael Oliveira', category: 'Família', status: 'pending' },
      { id: 103, name: 'Clara Oliveira', category: 'Família', status: 'pending' },
    ],
  },
  response: {},
  playlist: {
    playlist_url: 'https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M',
    title: 'Playlist colaborativa do casamento',
    description: 'Uma seleção para entrar no clima da celebração.',
    etiquette_message: 'Sugira com carinho: os noivos fazem a curadoria final.',
  },
};
