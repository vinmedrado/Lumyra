import { apiBaseUrl, getStoredAccessToken } from './api';
import type { RealtimeEvent } from '../types/domain';

type Listener = (event: RealtimeEvent) => void;

export class RealtimeClient {
  private socket: WebSocket | null = null;
  private listeners = new Set<Listener>();
  private reconnectTimer: number | undefined;
  private reconnectAttempts = 0;
  private manualClose = false;
  public status: 'disconnected' | 'connecting' | 'connected' | 'fallback' = 'disconnected';

  constructor(private tenantId?: number, private eventId?: number) {}

  connect() {
    if (this.socket || this.status === 'connecting') return;
    this.manualClose = false;
    this.status = 'connecting';
    const configuredWebSocketUrl = import.meta.env.VITE_WS_URL as string | undefined;
    const base = configuredWebSocketUrl || `${apiBaseUrl().replace(/^http/, 'ws').replace(/\/$/, '')}/ws`;
    const params = new URLSearchParams();
    const token = getStoredAccessToken();
    if (token) params.set('token', token);
    if (this.tenantId) params.set('tenant_id', String(this.tenantId));
    if (this.eventId) params.set('event_id', String(this.eventId));
    this.socket = new WebSocket(`${base}?${params.toString()}`);
    this.socket.onopen = () => { this.status = 'connected'; this.reconnectAttempts = 0; this.emit({ type: 'connection_status', payload: { status: 'connected' } }); };
    this.socket.onmessage = (message) => {
      try { this.emit(JSON.parse(message.data)); } catch { /* ignore malformed event */ }
    };
    this.socket.onclose = () => { this.socket = null; this.status = 'disconnected'; this.emit({ type: 'connection_status', payload: { status: 'disconnected' } }); if (!this.manualClose) this.scheduleReconnect(); };
    this.socket.onerror = () => { this.status = 'fallback'; this.emit({ type: 'connection_status', payload: { status: 'fallback' } }); };
  }

  disconnect() {
    this.manualClose = true;
    if (this.reconnectTimer) window.clearTimeout(this.reconnectTimer);
    this.socket?.close();
    this.socket = null;
  }

  subscribe(listener: Listener) { this.listeners.add(listener); return () => this.listeners.delete(listener); }

  send(type: string, payload: Record<string, unknown> = {}) {
    if (this.socket?.readyState === WebSocket.OPEN) this.socket.send(JSON.stringify({ type, ...payload }));
  }

  private scheduleReconnect() {
    const delay = Math.min(15000, 1000 * 2 ** this.reconnectAttempts++);
    this.reconnectTimer = window.setTimeout(() => this.connect(), delay);
  }

  private emit(event: RealtimeEvent) { this.listeners.forEach(listener => listener(event)); }
}
