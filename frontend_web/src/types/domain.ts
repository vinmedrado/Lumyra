export type Role = 'ADMIN' | 'CLIENT' | 'STAFF';
export type Status = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

export interface User { id?: number; name: string; email: string; role: Role; tenant_id?: number; }
export interface EventSummary { id: number; name: string; date?: string; location?: string; status?: string; }
export interface Guest { id: number; name: string; phone?: string; rsvp_status?: string; table_name?: string; group_name?: string; invitation_type?: 'individual' | 'family'; invitation_label?: string; }
export interface Insight { severity: 'critical' | 'warning' | 'info'; title: string; message: string; action?: string; count?: number; related_page?: string; }
export interface Metric { label: string; value: string | number; helper?: string; trend?: string; status?: Status; }
export interface Paginated<T> { items: T[]; total: number; page: number; page_size: number; }

export interface AnalyticsOverview {
  total_guests: number;
  confirmed: number;
  pending: number;
  declined: number;
  confirmation_rate: number;
  campaign_response_rate: number;
  message_errors: number;
  table_occupancy: Array<{ table_name: string; occupied: number }>;
  financial: { contracted: number; paid: number };
}

export type GuestResponseStatus = 'confirmed' | 'declined' | 'pending';

export interface InvitationMember {
  id: number;
  name: string;
  category?: string;
  status: GuestResponseStatus;
}

export interface GuestPortalContext {
  event: { id: number; name: string; date?: string; location?: string };
  invitation: {
    tenant_id: number;
    event_id: number;
    guest_id: number;
    type: 'individual' | 'family';
    label: string;
    members: InvitationMember[];
  };
  response: {
    phone?: string;
    needs_bus?: number | boolean;
    bus_pickup_point?: string;
    dietary_restrictions?: string;
    notes?: string;
  };
  playlist?: {
    playlist_url: string;
    title: string;
    description?: string;
    etiquette_message?: string;
  } | null;
}

export interface RealtimeEvent<T = Record<string, unknown>> { type: string; tenant_id?: number; event_id?: number; payload: T; created_at?: string; }
export interface NotificationItem { id: number; title: string; message: string; severity: 'success' | 'info' | 'warning' | 'critical'; is_read: number | boolean; created_at: string; related_entity_type?: string; related_entity_id?: number; }
export interface ActivityItem { id: number; action_type: string; entity_type?: string; entity_id?: number; message: string; created_at: string; }
export interface OnlineUser { user_id: number; name?: string; email?: string; role?: Role; current_page?: string; last_seen: string; }
