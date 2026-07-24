import { useEffect, useMemo, useState } from 'react';
import { RealtimeClient } from '../services/realtime';
import type { RealtimeEvent } from '../types/domain';
import { useAuth } from './useAuth';

export function useRealtime(eventId?: number) {
  const { user, isAuthenticated } = useAuth();
  const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'fallback'>('disconnected');
  const [lastEvent, setLastEvent] = useState<RealtimeEvent | null>(null);
  const client = useMemo(() => new RealtimeClient(user?.tenant_id || 1, eventId), [user?.tenant_id, eventId]);

  useEffect(() => {
    if (!isAuthenticated) return;
    const unsubscribe = client.subscribe((event) => {
      if (event.type === 'connection_status') setStatus((event.payload as any).status);
      else setLastEvent(event);
    });
    client.connect();
    const heartbeat = window.setInterval(() => client.send('heartbeat', { page: window.location.pathname }), 20000);
    return () => { window.clearInterval(heartbeat); unsubscribe(); client.disconnect(); };
  }, [client, isAuthenticated]);

  return { status, lastEvent, isLive: status === 'connected' };
}
