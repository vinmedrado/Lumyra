import { useEffect, useState } from 'react';
import { PageHeader } from '../../components/ui/PageHeader';
import { Card } from '../../components/ui/Card';
import { useDemoStore } from '../../demo/demoStore';
import { hasStoredAccessToken, notificationsApi } from '../../services/api';
import type { ActivityItem } from '../../types/domain';

export function ActivityFeedPage() {
  const isVisualDemo = !hasStoredAccessToken();
  const demo = useDemoStore();
  const [items, setItems] = useState<ActivityItem[]>([]);
  useEffect(() => {
    if (isVisualDemo) return;
    notificationsApi.activity().then(data => setItems(data.items || [])).catch(() => setItems([]));
  }, [isVisualDemo]);
  const displayItems: ActivityItem[] = isVisualDemo ? demo.activity.map(item => ({
    id: item.id,
    action_type: item.action,
    message: item.message,
    created_at: `${item.createdAt} · ${item.actor}`,
  })) : items;
  return <><PageHeader eyebrow="Colaboração" title="Activity Feed" subtitle="Linha do tempo operacional com ações recentes do tenant e evento." />
    <Card><div className="relative border-l border-slate-200 pl-5 dark:border-slate-800">{displayItems.length === 0 && <p className="text-sm text-slate-500">As atividades aparecerão aqui em tempo real.</p>}{displayItems.map(item => <div key={item.id} className="mb-5"><span className="absolute -left-1.5 mt-1 h-3 w-3 rounded-full bg-primary" /><p className="font-bold text-ink dark:text-white">{item.message}</p><p className="text-xs text-slate-500">{item.action_type} • {item.created_at}</p></div>)}</div></Card>
  </>;
}
