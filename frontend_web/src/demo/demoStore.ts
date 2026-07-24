import { useSyncExternalStore } from 'react';

export type DemoRsvpStatus = 'confirmed' | 'pending' | 'declined';
export type DemoSeverity = 'success' | 'info' | 'warning' | 'critical';

export interface DemoGuest {
  id: number;
  name: string;
  phone: string;
  email: string;
  group: string;
  category: string;
  status: DemoRsvpStatus;
  tableId: number | null;
  needsBus: boolean;
  dietary: string;
}

export interface DemoTable {
  id: number;
  name: string;
  capacity: number;
  zone: string;
}

export interface DemoExpense {
  id: number;
  vendor: string;
  category: string;
  amount: number;
  dueDate: string;
  paid: boolean;
}

export interface DemoDocument {
  id: number;
  name: string;
  category: string;
  owner: string;
  updatedAt: string;
  viewed: boolean;
}

export interface DemoTimelineItem {
  id: number;
  title: string;
  date: string;
  owner: string;
  completed: boolean;
}

export interface DemoCampaign {
  id: number;
  name: string;
  audience: string;
  sent: number;
  delivered: number;
  read: number;
  replies: number;
  status: 'draft' | 'scheduled' | 'sent';
  scheduledAt: string;
}

export interface DemoForm {
  id: number;
  name: string;
  fields: number;
  responses: number;
  active: boolean;
}

export interface DemoMessage {
  id: number;
  guest: string;
  channel: 'WhatsApp' | 'E-mail';
  template: string;
  status: 'delivered' | 'read' | 'failed' | 'queued';
  sentAt: string;
}

export interface DemoMusicSuggestion {
  id: number;
  guest: string;
  song: string;
  artist: string;
  message: string;
  status: 'pending' | 'approved' | 'added' | 'rejected';
}

export interface DemoNotification {
  id: number;
  title: string;
  message: string;
  severity: DemoSeverity;
  read: boolean;
  createdAt: string;
}

export interface DemoActivity {
  id: number;
  message: string;
  actor: string;
  action: string;
  createdAt: string;
}

export interface DemoAudit {
  id: number;
  actor: string;
  action: string;
  entity: string;
  result: 'success' | 'warning';
  createdAt: string;
}

export interface DemoState {
  version: 3;
  updatedAt: string;
  event: {
    id: number;
    name: string;
    date: string;
    location: string;
    ceremonyTime: string;
    status: string;
    couple: string;
    guestGoal: number;
  };
  guests: DemoGuest[];
  tables: DemoTable[];
  expenses: DemoExpense[];
  documents: DemoDocument[];
  timeline: DemoTimelineItem[];
  campaigns: DemoCampaign[];
  forms: DemoForm[];
  messages: DemoMessage[];
  musicSuggestions: DemoMusicSuggestion[];
  playlist: {
    url: string;
    title: string;
    description: string;
    etiquette: string;
  };
  notifications: DemoNotification[];
  activity: DemoActivity[];
  audit: DemoAudit[];
  settings: {
    whatsappConnected: boolean;
    remindersEnabled: boolean;
    clientPortalEnabled: boolean;
  };
}

const STORAGE_KEY = 'lumyra_portfolio_demo_v3';
const listeners = new Set<() => void>();

function now() {
  return new Date().toISOString();
}

function seedState(): DemoState {
  return {
    version: 3,
    updatedAt: now(),
    event: {
      id: 1,
      name: 'Casamento Ana & João',
      date: '2026-09-12',
      location: 'Espaço Jardim Imperial · São Paulo',
      ceremonyTime: '16h30',
      status: 'Em organização',
      couple: 'Ana & João',
      guestGoal: 180,
    },
    guests: [
      { id: 101, name: 'Marina Oliveira', phone: '(11) 99911-0101', email: 'marina@example.com', group: 'Família Oliveira', category: 'Família', status: 'pending', tableId: null, needsBus: false, dietary: '' },
      { id: 102, name: 'Rafael Oliveira', phone: '(11) 99911-0102', email: 'rafael@example.com', group: 'Família Oliveira', category: 'Família', status: 'pending', tableId: null, needsBus: false, dietary: '' },
      { id: 103, name: 'Clara Oliveira', phone: '(11) 99911-0103', email: 'clara@example.com', group: 'Família Oliveira', category: 'Criança', status: 'pending', tableId: null, needsBus: false, dietary: '' },
      { id: 104, name: 'Beatriz Souza', phone: '(11) 98841-1204', email: 'bia@example.com', group: 'Família da noiva', category: 'Família', status: 'confirmed', tableId: 1, needsBus: false, dietary: 'Sem lactose' },
      { id: 105, name: 'Carlos Souza', phone: '(11) 98841-1205', email: 'carlos@example.com', group: 'Família da noiva', category: 'Família', status: 'confirmed', tableId: 1, needsBus: true, dietary: '' },
      { id: 106, name: 'Helena Martins', phone: '(11) 97721-2306', email: 'helena@example.com', group: 'Amigos faculdade', category: 'Amigos', status: 'confirmed', tableId: 3, needsBus: false, dietary: 'Vegetariana' },
      { id: 107, name: 'Lucas Martins', phone: '(11) 97721-2307', email: 'lucas@example.com', group: 'Amigos faculdade', category: 'Amigos', status: 'confirmed', tableId: 3, needsBus: false, dietary: '' },
      { id: 108, name: 'Fernanda Lima', phone: '(11) 96631-3408', email: 'fernanda@example.com', group: 'Trabalho', category: 'Colegas', status: 'pending', tableId: null, needsBus: true, dietary: '' },
      { id: 109, name: 'Ricardo Lima', phone: '(11) 96631-3409', email: 'ricardo@example.com', group: 'Trabalho', category: 'Colegas', status: 'declined', tableId: null, needsBus: false, dietary: '' },
      { id: 110, name: 'Patrícia Alves', phone: '(11) 95541-4510', email: 'patricia@example.com', group: 'Padrinhos', category: 'Padrinhos', status: 'confirmed', tableId: 2, needsBus: false, dietary: 'Sem glúten' },
      { id: 111, name: 'André Alves', phone: '(11) 95541-4511', email: 'andre@example.com', group: 'Padrinhos', category: 'Padrinhos', status: 'confirmed', tableId: 2, needsBus: false, dietary: '' },
      { id: 112, name: 'Camila Rocha', phone: '(11) 94451-5612', email: 'camila@example.com', group: 'Amigos do noivo', category: 'Amigos', status: 'pending', tableId: null, needsBus: false, dietary: '' },
      { id: 113, name: 'Gustavo Rocha', phone: '(11) 94451-5613', email: 'gustavo@example.com', group: 'Amigos do noivo', category: 'Amigos', status: 'confirmed', tableId: 4, needsBus: false, dietary: '' },
      { id: 114, name: 'Lúcia Ferreira', phone: '(11) 93361-6714', email: 'lucia@example.com', group: 'Família do noivo', category: 'Família', status: 'confirmed', tableId: 5, needsBus: true, dietary: '' },
      { id: 115, name: 'Paulo Ferreira', phone: '(11) 93361-6715', email: 'paulo@example.com', group: 'Família do noivo', category: 'Família', status: 'declined', tableId: null, needsBus: false, dietary: '' },
    ],
    tables: [
      { id: 1, name: 'Mesa Jardim', capacity: 8, zone: 'Varanda' },
      { id: 2, name: 'Mesa dos Padrinhos', capacity: 10, zone: 'Salão principal' },
      { id: 3, name: 'Mesa Aurora', capacity: 8, zone: 'Salão principal' },
      { id: 4, name: 'Mesa Ipê', capacity: 8, zone: 'Jardim' },
      { id: 5, name: 'Mesa Família', capacity: 10, zone: 'Salão principal' },
      { id: 6, name: 'Mesa Horizonte', capacity: 8, zone: 'Varanda' },
    ],
    expenses: [
      { id: 1, vendor: 'Espaço Jardim Imperial', category: 'Local', amount: 42000, dueDate: '2026-08-05', paid: true },
      { id: 2, vendor: 'Buffet Celebrare', category: 'Buffet', amount: 38500, dueDate: '2026-08-20', paid: true },
      { id: 3, vendor: 'Flores & Afeto', category: 'Decoração', amount: 16800, dueDate: '2026-08-28', paid: false },
      { id: 4, vendor: 'Frame Filmes', category: 'Foto e vídeo', amount: 12400, dueDate: '2026-09-01', paid: false },
      { id: 5, vendor: 'DJ Pulsar', category: 'Música', amount: 6800, dueDate: '2026-09-05', paid: false },
    ],
    documents: [
      { id: 1, name: 'Contrato · Espaço Jardim Imperial.pdf', category: 'Contrato', owner: 'Assessoria', updatedAt: '18/07/2026', viewed: true },
      { id: 2, name: 'Cardápio final · Buffet.pdf', category: 'Buffet', owner: 'Ana & João', updatedAt: '21/07/2026', viewed: true },
      { id: 3, name: 'Layout de decoração.pdf', category: 'Decoração', owner: 'Assessoria', updatedAt: '23/07/2026', viewed: false },
      { id: 4, name: 'Cronograma do grande dia.pdf', category: 'Operação', owner: 'Assessoria', updatedAt: '24/07/2026', viewed: false },
    ],
    timeline: [
      { id: 1, title: 'Definir cardápio final', date: '2026-07-18', owner: 'Ana & João', completed: true },
      { id: 2, title: 'Revisar lista de convidados', date: '2026-07-30', owner: 'Assessoria', completed: false },
      { id: 3, title: 'Fechar mapa de mesas', date: '2026-08-15', owner: 'Ana & João', completed: false },
      { id: 4, title: 'Enviar lembrete de RSVP', date: '2026-08-20', owner: 'Assessoria', completed: false },
      { id: 5, title: 'Reunião final com fornecedores', date: '2026-09-03', owner: 'Todos', completed: false },
      { id: 6, title: 'Casamento', date: '2026-09-12', owner: 'Ana & João', completed: false },
    ],
    campaigns: [
      { id: 1, name: 'Save the date', audience: 'Todos os convidados', sent: 15, delivered: 15, read: 14, replies: 8, status: 'sent', scheduledAt: '10/06/2026 · 10h' },
      { id: 2, name: 'Confirmação de presença', audience: 'RSVP pendente', sent: 6, delivered: 5, read: 4, replies: 2, status: 'sent', scheduledAt: '20/07/2026 · 14h' },
      { id: 3, name: 'Lembrete final de RSVP', audience: 'RSVP pendente', sent: 0, delivered: 0, read: 0, replies: 0, status: 'scheduled', scheduledAt: '20/08/2026 · 10h' },
    ],
    forms: [
      { id: 1, name: 'Confirmação e transporte', fields: 6, responses: 11, active: true },
      { id: 2, name: 'Restrições alimentares', fields: 3, responses: 4, active: true },
      { id: 3, name: 'Pesquisa pós-evento', fields: 8, responses: 0, active: false },
    ],
    messages: [
      { id: 1, guest: 'Beatriz Souza', channel: 'WhatsApp', template: 'Confirmação de presença', status: 'read', sentAt: '20/07 · 14:02' },
      { id: 2, guest: 'Carlos Souza', channel: 'WhatsApp', template: 'Confirmação de presença', status: 'delivered', sentAt: '20/07 · 14:03' },
      { id: 3, guest: 'Fernanda Lima', channel: 'WhatsApp', template: 'Lembrete gentil', status: 'failed', sentAt: '23/07 · 09:18' },
      { id: 4, guest: 'Camila Rocha', channel: 'WhatsApp', template: 'Lembrete gentil', status: 'queued', sentAt: '24/07 · 16:00' },
    ],
    musicSuggestions: [
      { id: 1, guest: 'Helena Martins', song: 'A Thousand Years', artist: 'Christina Perri', message: 'Para a entrada dos noivos!', status: 'approved' },
      { id: 2, guest: 'Gustavo Rocha', song: 'September', artist: 'Earth, Wind & Fire', message: 'Essa coloca todo mundo na pista.', status: 'added' },
    ],
    playlist: {
      url: 'https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M',
      title: 'Playlist colaborativa do casamento',
      description: 'Uma seleção para entrar no clima da celebração.',
      etiquette: 'Sugira com carinho: os noivos fazem a curadoria final.',
    },
    notifications: [
      { id: 1, title: 'RSVP precisa de atenção', message: '6 convidados ainda não responderam.', severity: 'warning', read: false, createdAt: 'Hoje · 09:30' },
      { id: 2, title: 'Documento compartilhado', message: 'O cronograma final já está disponível para os noivos.', severity: 'info', read: false, createdAt: 'Hoje · 08:45' },
      { id: 3, title: 'Pagamento confirmado', message: 'Parcela do Buffet Celebrare marcada como paga.', severity: 'success', read: true, createdAt: 'Ontem · 17:20' },
      { id: 4, title: 'Mensagem não entregue', message: 'Revisar o telefone de Fernanda Lima.', severity: 'critical', read: false, createdAt: 'Ontem · 14:12' },
    ],
    activity: [
      { id: 1, message: 'Cronograma final compartilhado com os noivos', actor: 'Assessoria Demo', action: 'document_shared', createdAt: 'Hoje · 08:45' },
      { id: 2, message: 'Buffet Celebrare marcado como pago', actor: 'Assessoria Demo', action: 'expense_paid', createdAt: 'Ontem · 17:20' },
      { id: 3, message: 'Gustavo Rocha confirmou presença', actor: 'Portal do convidado', action: 'rsvp_updated', createdAt: 'Ontem · 15:04' },
      { id: 4, message: 'Campanha de confirmação enviada', actor: 'Automação', action: 'campaign_sent', createdAt: '20/07 · 14:00' },
    ],
    audit: [
      { id: 1, actor: 'Assessoria Demo', action: 'Atualizou pagamento', entity: 'Buffet Celebrare', result: 'success', createdAt: '23/07 · 17:20' },
      { id: 2, actor: 'Portal do convidado', action: 'Atualizou RSVP', entity: 'Gustavo Rocha', result: 'success', createdAt: '23/07 · 15:04' },
      { id: 3, actor: 'Automação', action: 'Tentou enviar mensagem', entity: 'Fernanda Lima', result: 'warning', createdAt: '23/07 · 14:12' },
    ],
    settings: {
      whatsappConnected: true,
      remindersEnabled: true,
      clientPortalEnabled: true,
    },
  };
}

function readStoredState(): DemoState {
  if (typeof window === 'undefined') return seedState();
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return seedState();
    const parsed = JSON.parse(raw) as DemoState;
    return parsed.version === 3 ? parsed : seedState();
  } catch {
    return seedState();
  }
}

let currentState = readStoredState();

function emit() {
  listeners.forEach(listener => listener());
}

function commit(next: DemoState) {
  currentState = { ...next, updatedAt: now() };
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(currentState));
  } catch {
    // The demo remains usable in memory when storage is unavailable.
  }
  emit();
}

function appendActivity(state: DemoState, message: string, actor: string, action: string): DemoState {
  const id = Date.now();
  return {
    ...state,
    activity: [{ id, message, actor, action, createdAt: 'Agora' }, ...state.activity].slice(0, 30),
    audit: [{ id, actor, action: message, entity: state.event.name, result: 'success' as const, createdAt: 'Agora' }, ...state.audit].slice(0, 40),
  };
}

export const demoActions = {
  reset() {
    commit(seedState());
  },
  updateGuestStatus(guestId: number, status: DemoRsvpStatus) {
    const guest = currentState.guests.find(item => item.id === guestId);
    if (!guest) return;
    const next = {
      ...currentState,
      guests: currentState.guests.map(item => item.id === guestId ? { ...item, status } : item),
    };
    commit(appendActivity(next, `${guest.name} teve o RSVP atualizado para ${status}`, 'Assessoria Demo', 'rsvp_updated'));
  },
  assignGuestTable(guestId: number, tableId: number | null) {
    const guest = currentState.guests.find(item => item.id === guestId);
    if (!guest) return;
    const table = currentState.tables.find(item => item.id === tableId);
    const next = {
      ...currentState,
      guests: currentState.guests.map(item => item.id === guestId ? { ...item, tableId } : item),
    };
    commit(appendActivity(next, `${guest.name} foi movido para ${table?.name || 'sem mesa'}`, 'Assessoria Demo', 'table_assignment'));
  },
  submitFamilyRsvp(payload: {
    members: Array<{ guestId: number; status: DemoRsvpStatus }>;
    phone: string;
    needsBus: boolean;
    dietary: string;
  }) {
    const memberIds = new Set(payload.members.map(member => member.guestId));
    const nextGuests = currentState.guests.map(guest => {
      if (!memberIds.has(guest.id)) return guest;
      const response = payload.members.find(member => member.guestId === guest.id);
      return {
        ...guest,
        status: response?.status || guest.status,
        phone: guest.id === 101 && payload.phone ? payload.phone : guest.phone,
        needsBus: payload.needsBus,
        dietary: payload.dietary || guest.dietary,
      };
    });
    const confirmed = payload.members.filter(member => member.status === 'confirmed').length;
    const base = {
      ...currentState,
      guests: nextGuests,
      notifications: [{
        id: Date.now(),
        title: 'Novo RSVP recebido',
        message: `Família Oliveira respondeu: ${confirmed} confirmado(s).`,
        severity: 'success' as const,
        read: false,
        createdAt: 'Agora',
      }, ...currentState.notifications],
    };
    commit(appendActivity(base, `Família Oliveira enviou o RSVP com ${confirmed} confirmado(s)`, 'Portal do convidado', 'rsvp_updated'));
  },
  toggleExpensePaid(expenseId: number) {
    const expense = currentState.expenses.find(item => item.id === expenseId);
    if (!expense) return;
    const paid = !expense.paid;
    const next = {
      ...currentState,
      expenses: currentState.expenses.map(item => item.id === expenseId ? { ...item, paid } : item),
    };
    commit(appendActivity(next, `${expense.vendor} marcado como ${paid ? 'pago' : 'pendente'}`, 'Assessoria Demo', 'expense_updated'));
  },
  toggleTimeline(itemId: number) {
    const item = currentState.timeline.find(entry => entry.id === itemId);
    if (!item) return;
    const next = {
      ...currentState,
      timeline: currentState.timeline.map(entry => entry.id === itemId ? { ...entry, completed: !entry.completed } : entry),
    };
    commit(appendActivity(next, `Etapa “${item.title}” atualizada`, 'Ana & João', 'timeline_updated'));
  },
  markDocumentViewed(documentId: number) {
    const document = currentState.documents.find(item => item.id === documentId);
    if (!document) return;
    const next = {
      ...currentState,
      documents: currentState.documents.map(item => item.id === documentId ? { ...item, viewed: true } : item),
    };
    commit(appendActivity(next, `${document.name} foi visualizado`, 'Ana & João', 'document_viewed'));
  },
  sendCampaign(campaignId: number) {
    const campaign = currentState.campaigns.find(item => item.id === campaignId);
    if (!campaign) return;
    const pending = currentState.guests.filter(guest => guest.status === 'pending').length;
    const next = {
      ...currentState,
      campaigns: currentState.campaigns.map(item => item.id === campaignId ? {
        ...item,
        status: 'sent' as const,
        sent: pending,
        delivered: Math.max(0, pending - 1),
        read: Math.max(0, pending - 2),
      } : item),
      notifications: [{
        id: Date.now(),
        title: 'Campanha enviada',
        message: `${campaign.name} foi enviada para ${pending} convidado(s).`,
        severity: 'success' as const,
        read: false,
        createdAt: 'Agora',
      }, ...currentState.notifications],
    };
    commit(appendActivity(next, `Campanha “${campaign.name}” enviada`, 'Assessoria Demo', 'campaign_sent'));
  },
  addMusicSuggestion(guest: string, song: string, artist: string, message: string) {
    const next = {
      ...currentState,
      musicSuggestions: [{
        id: Date.now(),
        guest,
        song,
        artist,
        message,
        status: 'pending' as const,
      }, ...currentState.musicSuggestions],
      notifications: [{
        id: Date.now() + 1,
        title: 'Nova sugestão musical',
        message: `${guest} sugeriu “${song}”.`,
        severity: 'info' as const,
        read: false,
        createdAt: 'Agora',
      }, ...currentState.notifications],
    };
    commit(appendActivity(next, `${guest} sugeriu ${song} · ${artist}`, 'Portal do convidado', 'music_suggested'));
  },
  updateMusicSuggestionStatus(suggestionId: number, status: DemoMusicSuggestion['status']) {
    const suggestion = currentState.musicSuggestions.find(item => item.id === suggestionId);
    if (!suggestion) return;
    const next = {
      ...currentState,
      musicSuggestions: currentState.musicSuggestions.map(item => item.id === suggestionId ? { ...item, status } : item),
    };
    commit(appendActivity(next, `Sugestão “${suggestion.song}” marcada como ${status}`, 'Assessoria Demo', 'music_curated'));
  },
  updatePlaylist(playlist: DemoState['playlist']) {
    const next = { ...currentState, playlist };
    commit(appendActivity(next, 'Configuração da playlist atualizada', 'Assessoria Demo', 'playlist_updated'));
  },
  markNotificationRead(notificationId: number) {
    commit({
      ...currentState,
      notifications: currentState.notifications.map(item => item.id === notificationId ? { ...item, read: true } : item),
    });
  },
  markAllNotificationsRead() {
    commit({
      ...currentState,
      notifications: currentState.notifications.map(item => ({ ...item, read: true })),
    });
  },
  updateSetting(key: keyof DemoState['settings'], value: boolean) {
    const next = { ...currentState, settings: { ...currentState.settings, [key]: value } };
    commit(appendActivity(next, `Configuração ${key} alterada`, 'Assessoria Demo', 'settings_updated'));
  },
};

export function getDemoStats(state: DemoState) {
  const confirmed = state.guests.filter(guest => guest.status === 'confirmed').length;
  const pending = state.guests.filter(guest => guest.status === 'pending').length;
  const declined = state.guests.filter(guest => guest.status === 'declined').length;
  const seated = state.guests.filter(guest => guest.status === 'confirmed' && guest.tableId).length;
  const contracted = state.expenses.reduce((sum, expense) => sum + expense.amount, 0);
  const paid = state.expenses.filter(expense => expense.paid).reduce((sum, expense) => sum + expense.amount, 0);
  return {
    total: state.guests.length,
    confirmed,
    pending,
    declined,
    seated,
    contracted,
    paid,
    confirmationRate: Math.round((confirmed / Math.max(state.guests.length, 1)) * 100),
    seatingRate: Math.round((seated / Math.max(confirmed, 1)) * 100),
    financialRate: Math.round((paid / Math.max(contracted, 1)) * 100),
  };
}

export function useDemoStore() {
  return useSyncExternalStore(
    listener => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    () => currentState,
    () => currentState,
  );
}

if (typeof window !== 'undefined') {
  window.addEventListener('storage', event => {
    if (event.key !== STORAGE_KEY || !event.newValue) return;
    try {
      const next = JSON.parse(event.newValue) as DemoState;
      if (next.version === 3) {
        currentState = next;
        emit();
      }
    } catch {
      // Ignore invalid data written by another tab.
    }
  });
}
