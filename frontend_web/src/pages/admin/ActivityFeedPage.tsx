import { useEffect, useState } from 'react';
import { PageHeader } from '../../components/ui/PageHeader';
import { Card } from '../../components/ui/Card';
import { notificationsApi } from '../../services/api';
import type { ActivityItem } from '../../types/domain';

export function ActivityFeedPage() {
  const [items, setItems] = useState<ActivityItem[]>([]);
  useEffect(() => { notificationsApi.activity().then(data => setItems(data.items || [])).catch(() => setItems([])); }, []);
  return <><PageHeader eyebrow="Colaboração" title="Activity Feed" subtitle="Linha do tempo operacional com ações recentes do tenant e evento." />
    <Card><div className="relative border-l border-slate-200 pl-5 dark:border-slate-800">{items.length === 0 && <p className="text-sm text-slate-500">As atividades aparecerão aqui em tempo real.</p>}{items.map(item => <div key={item.id} className="mb-5"><span className="absolute -left-1.5 mt-1 h-3 w-3 rounded-full bg-primary" /><p className="font-bold text-ink dark:text-white">{item.message}</p><p className="text-xs text-slate-500">{item.action_type} • {item.created_at}</p></div>)}</div></Card>
  </>;
}
