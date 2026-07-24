import { useEffect, useState } from 'react';
import { PageHeader } from '../../components/ui/PageHeader';
import { Card } from '../../components/ui/Card';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { notificationsApi } from '../../services/api';
import type { NotificationItem } from '../../types/domain';

export function NotificationsPage() {
  const [items, setItems] = useState<NotificationItem[]>([]);
  useEffect(() => { notificationsApi.list().then(data => setItems(data.items || [])).catch(() => setItems([])); }, []);
  return <><PageHeader eyebrow="Realtime" title="Central de notificações" subtitle="Alertas internos, workflows, erros de mensagem e pendências críticas em um só lugar." />
    <div className="grid gap-3">{items.length === 0 && <Card><p className="text-slate-500">Nenhuma notificação encontrada.</p></Card>}{items.map(item => <Card key={item.id} className="flex items-start justify-between gap-4"><div><h3 className="font-black text-ink dark:text-white">{item.title}</h3><p className="mt-1 text-sm text-slate-500">{item.message}</p><p className="mt-2 text-xs text-slate-400">{item.created_at}</p></div><StatusBadge status={item.severity === 'critical' ? 'danger' : item.severity === 'warning' ? 'warning' : item.severity === 'success' ? 'success' : 'info'}>{item.severity}</StatusBadge></Card>)}</div>
  </>;
}
