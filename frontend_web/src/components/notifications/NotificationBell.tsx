import { useCallback, useEffect, useState } from 'react';
import { Bell, CheckCheck } from 'lucide-react';
import { demoActions, useDemoStore } from '../../demo/demoStore';
import { hasStoredAccessToken, notificationsApi } from '../../services/api';
import type { NotificationItem, RealtimeEvent } from '../../types/domain';
import { Button } from '../ui/Button';

const severityClass: Record<string, string> = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-200',
  info: 'border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-200',
  warning: 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200',
  critical: 'border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-800 dark:bg-rose-950 dark:text-rose-200',
};

export function NotificationBell({ lastEvent }: { lastEvent?: RealtimeEvent | null }) {
  const demoState = useDemoStore();
  const isStaticDemo = !hasStoredAccessToken();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);

  const load = useCallback(async () => {
    if (isStaticDemo) return;
    try {
      const data = await notificationsApi.list();
      setItems(data.items || []);
      setUnread(data.unread_count || 0);
    } catch { /* API pode estar offline no modo demo */ }
  }, [isStaticDemo]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (!isStaticDemo && lastEvent?.type === 'notification_created') {
      const item = lastEvent.payload as unknown as NotificationItem;
      setItems(prev => [item, ...prev].slice(0, 8));
      setUnread(prev => prev + 1);
    }
  }, [isStaticDemo, lastEvent]);

  async function markAll() {
    if (isStaticDemo) {
      demoActions.markAllNotificationsRead();
      return;
    }
    await notificationsApi.markAllRead();
    setUnread(0);
    setItems(prev => prev.map(item => ({ ...item, is_read: true })));
  }

  async function markOne(id: number) {
    if (isStaticDemo) {
      demoActions.markNotificationRead(id);
      return;
    }
    await notificationsApi.markRead(id);
    setItems(prev => prev.map(item => item.id === id ? { ...item, is_read: true } : item));
    setUnread(prev => Math.max(0, prev - 1));
  }

  const displayItems: NotificationItem[] = isStaticDemo
    ? demoState.notifications.slice(0, 8).map(item => ({
      id: item.id,
      title: item.title,
      message: item.message,
      severity: item.severity,
      is_read: item.read,
      created_at: item.createdAt,
    }))
    : items;
  const unreadCount = isStaticDemo
    ? demoState.notifications.filter(item => !item.read).length
    : unread;

  return <div className="relative">
    <button onClick={() => setOpen(v => !v)} className="relative rounded-2xl border border-slate-200 bg-white p-2 text-slate-700 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
      <Bell size={18} />
      {unreadCount > 0 && <span className="absolute -right-1 -top-1 rounded-full bg-rose-500 px-1.5 py-0.5 text-[10px] font-black text-white">{unreadCount}</span>}
    </button>
    {open && <div className="absolute right-0 mt-3 w-[340px] overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-center justify-between border-b border-slate-100 p-4 dark:border-slate-800">
        <div><p className="text-sm font-black text-slate-900 dark:text-white">Notificações</p><p className="text-xs text-slate-500">Alertas vivos da operação</p></div>
        <button onClick={markAll} className="inline-flex items-center gap-1 text-xs font-bold text-primary"><CheckCheck size={14}/>Ler todas</button>
      </div>
      <div className="max-h-96 overflow-y-auto p-3">
        {displayItems.length === 0 && <p className="p-4 text-sm text-slate-500">Nenhuma notificação por enquanto.</p>}
        {displayItems.map(item => <button type="button" onClick={() => void markOne(item.id)} key={item.id} className={`mb-2 block w-full rounded-2xl border p-3 text-left ${severityClass[item.severity] || severityClass.info}`}>
          <div className="flex items-start justify-between gap-2"><strong className="text-sm">{item.title}</strong>{!item.is_read && <span className="h-2 w-2 rounded-full bg-current" />}</div>
          <p className="mt-1 text-xs opacity-80">{item.message}</p>
        </button>)}
      </div>
      <div className="border-t border-slate-100 p-3 dark:border-slate-800"><Button variant="secondary" className="w-full" onClick={() => window.location.href='/admin/notifications'}>Abrir central</Button></div>
    </div>}
  </div>;
}
