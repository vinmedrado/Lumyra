import axios, { AxiosError } from 'axios';
import type {
  AnalyticsOverview,
  EventSummary,
  Guest,
  GuestPortalContext,
  GuestResponseStatus,
  Insight,
  Paginated,
  User,
} from '../types/domain';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const api = axios.create({ baseURL: API_BASE_URL, timeout: 15000 });

function getAccessToken() { return localStorage.getItem('access_token'); }
function getRefreshToken() { return localStorage.getItem('refresh_token'); }
function setTokens(access?: string, refresh?: string) {
  if (access) localStorage.setItem('access_token', access);
  if (refresh) localStorage.setItem('refresh_token', refresh);
}
function clearTokens() { localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); }

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original: any = error.config;
    if (error.response?.status === 401 && !original?._retry && getRefreshToken()) {
      original._retry = true;
      try {
        const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, { refresh_token: getRefreshToken() });
        setTokens(data.access_token, data.refresh_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch { clearTokens(); window.location.href = '/login'; }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  async login(email: string, password: string) {
    const { data } = await api.post('/auth/login', { email, password });
    setTokens(data.access_token, data.refresh_token);
    return data;
  },
  async me(): Promise<User> { const { data } = await api.get('/auth/me'); return data; },
  async logout() { try { await api.post('/auth/logout', { refresh_token: getRefreshToken() }); } finally { clearTokens(); } }
};

export const eventsApi = {
  list: async (): Promise<EventSummary[]> => (await api.get('/events')).data.data,
};
export const guestsApi = {
  list: async (params = {}): Promise<Paginated<Guest>> => (await api.get('/guests', { params })).data,
  export: async () => (await api.get('/guests/export')).data,
  import: async (file: File) => { const body = new FormData(); body.append('file', file); return (await api.post('/guests/import', body)).data; }
};
export const formsApi = { list: async () => (await api.get('/forms')).data, responses: async () => (await api.get('/forms/responses')).data };
export const messagesApi = { campaigns: async () => (await api.get('/campaigns')).data, logs: async (params = {}) => (await api.get('/messages/logs', { params })).data };
export const financialApi = { expenses: async (params = {}) => (await api.get('/expenses', { params })).data, vendors: async () => (await api.get('/vendors')).data };
export const insightsApi = {
  list: async (eventId: number): Promise<Insight[]> => (
    await api.get('/insights', { params: { event_id: eventId } })
  ).data.data,
};
export const documentsApi = { list: async (params = {}) => (await api.get('/documents', { params })).data };
export const analyticsApi = {
  overview: async (eventId: number): Promise<AnalyticsOverview> => (
    await api.get('/analytics', { params: { event_id: eventId } })
  ).data.data,
};
export const tenantsApi = { list: async () => (await api.get('/tenants')).data };

export function getStoredAccessToken() { return getAccessToken(); }
export function apiBaseUrl() { return API_BASE_URL; }
export const notificationsApi = {
  list: async (params = {}) => (await api.get('/notifications', { params })).data,
  markRead: async (id: number) => (await api.post(`/notifications/${id}/read`)).data,
  markAllRead: async () => (await api.post('/notifications/read-all')).data,
  activity: async () => (await api.get('/notifications/activity')).data,
  presence: async () => (await api.get('/notifications/presence')).data,
};

export type PlaylistPayload = {
  event_id: number;
  playlist_url: string;
  title?: string;
  description?: string;
  etiquette_message?: string;
  is_active?: boolean;
};
export const playlistsApi = {
  read: async (eventId: number) => (await api.get(`/playlists/${eventId}`)).data.data,
  save: async (payload: PlaylistPayload) => (await api.put('/playlists', payload)).data.data,
};

export type MusicSuggestionPayload = {
  guest_token: string;
  guest_name?: string;
  song_name: string;
  artist_name: string;
  message?: string;
};

export const musicSuggestionsApi = {
  createPublic: async (payload: MusicSuggestionPayload) => (await api.post('/music-suggestions/public', payload)).data.data,
  list: async (params = {}) => (await api.get('/music-suggestions', { params })).data.data,
  updateStatus: async (id: number, status: string) => (await api.patch(`/music-suggestions/${id}/status`, { status })).data.data,
};

export type GuestPortalSubmitPayload = {
  members: Array<{ guest_id: number; status: GuestResponseStatus }>;
  phone?: string;
  needs_bus: boolean;
  bus_pickup_point?: string;
  dietary_restrictions?: string;
  notes?: string;
};

export const guestPortalApi = {
  read: async (token: string): Promise<GuestPortalContext> => (
    await api.get(`/public/guest/${encodeURIComponent(token)}`)
  ).data.data,
  submit: async (token: string, payload: GuestPortalSubmitPayload) => (
    await api.post(`/public/guest/${encodeURIComponent(token)}/rsvp`, payload)
  ).data.data,
};

export function hasStoredAccessToken() { return Boolean(getAccessToken()); }
export function isDemoMode() { return import.meta.env.VITE_DEMO_MODE !== 'false'; }
