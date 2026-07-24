import { useEffect, useState } from 'react';
import { PageHeader } from '../../components/ui/PageHeader';
import { Card } from '../../components/ui/Card';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { demoActions, useDemoStore } from '../../demo/demoStore';
import { hasStoredAccessToken, notificationsApi } from '../../services/api';
import type { NotificationItem } from '../../types/domain';

export function NotificationsPage() {
  const isVisualDemo = !hasStoredAccessToken();
  const demo = useDemoStore();
  const [items, setItems] = useState<NotificationItem[]>([]);
  useEffect(() => {
    if (isVisualDemo) return;
    notificationsApi.list().then(data => setItems(data.items || [])).catch(() => setItems([]));
  }, [isVisualDemo]);
  const displayItems: NotificationItem[] = isVisualDemo ? demo.notifications.map(item => ({
    id: item.id,
    title: item.title,
    message: item.message,
    severity: item.severity,
    is_read: item.read,
    created_at: item.createdAt,
  })) : items;
  return <><PageHeader eyebrow="Realtime" title="Central de notificações" subtitle="Alertas internos, workflows, erros de mensagem e pendências críticas em um só lugar." />
    <div className="grid gap-3">{displayItems.length === 0 && <Card><p className="text-slate-500">Nenhuma notificação encontrada.</p></Card>}{displayItems.map(item => <button key={item.id} className="text-left" onClick={() => isVisualDemo && demoActions.markNotificationRead(item.id)}><Card className={`flex items-start justify-between gap-4 ${item.is_read ? 'opacity-65' : ''}`}><div><h3 className="font-black text-ink dark:text-white">{item.title}</h3><p className="mt-1 text-sm text-slate-500">{item.message}</p><p className="mt-2 text-xs text-slate-400">{item.created_at}{isVisualDemo && !item.is_read ? ' · clique para marcar como lida' : ''}</p></div><StatusBadge status={item.severity === 'critical' ? 'danger' : item.severity === 'warning' ? 'warning' : item.severity === 'success' ? 'success' : 'info'}>{item.severity}</StatusBadge></Card></button>)}</div>
  </>;
}
