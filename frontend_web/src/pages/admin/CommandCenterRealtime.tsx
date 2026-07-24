import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, MessageCircle } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { MetricCard } from '../../components/ui/MetricCard';
import { PageHeader } from '../../components/ui/PageHeader';
import { LiveIndicator } from '../../components/realtime/LiveIndicator';
import { useRealtime } from '../../hooks/useRealtime';
import { useDemoStore } from '../../demo/demoStore';
import { hasStoredAccessToken, notificationsApi } from '../../services/api';
import type { ActivityItem, OnlineUser } from '../../types/domain';

export function CommandCenterRealtime() {
  const isVisualDemo = !hasStoredAccessToken();
  const demo = useDemoStore();
  const { status, lastEvent } = useRealtime();
  const [events, setEvents] = useState<string[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [online, setOnline] = useState<OnlineUser[]>([]);
  useEffect(() => {
    if (isVisualDemo) return;
    notificationsApi.activity().then(d => setActivity(d.items || [])).catch(() => undefined);
    notificationsApi.presence().then(d => setOnline(d.items || [])).catch(() => undefined);
  }, [isVisualDemo]);
  useEffect(() => { if (lastEvent) setEvents(prev => [`${lastEvent.type}`, ...prev].slice(0, 8)); }, [lastEvent]);
  const displayActivity: ActivityItem[] = isVisualDemo ? demo.activity.map(item => ({ id: item.id, action_type: item.action, message: item.message, created_at: item.createdAt })) : activity;
  const eventNames = isVisualDemo ? demo.activity.slice(0, 8).map(item => item.action) : events;
  const onlineCount = isVisualDemo ? 3 : online.length;
  const criticalCount = isVisualDemo ? demo.notifications.filter(item => item.severity === 'critical' && !item.read).length : 0;
  return <><PageHeader eyebrow="Ao vivo" title="Command Center Realtime" subtitle="Eventos, jobs, alertas, usuários online e atividade operacional sem refresh manual." actions={<LiveIndicator status={isVisualDemo ? 'connected' : status} />} />
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <MetricCard metric={{ label: 'Eventos realtime', value: eventNames.length, helper: 'Recebidos na demo', status: 'info' }} />
      <MetricCard metric={{ label: 'Usuários online', value: onlineCount, helper: 'Assessoria · noivos · portal', status: 'success' }} />
      <MetricCard metric={{ label: 'Alertas críticos', value: criticalCount, helper: 'Exigem atenção', status: criticalCount ? 'danger' : 'success' }} />
      <MetricCard metric={{ label: 'Jobs ativos', value: demo.campaigns.filter(item => item.status === 'scheduled').length, helper: 'Campanhas agendadas', status: 'warning' }} />
    </div>
    <div className="mt-6 grid gap-6 lg:grid-cols-3"><Card><h2 className="flex items-center gap-2 text-lg font-black dark:text-white"><Activity size={18}/>Eventos ao vivo</h2><div className="mt-4 space-y-2">{eventNames.map((e, idx) => <p key={`${e}-${idx}`} className="rounded-2xl bg-slate-50 p-3 text-sm dark:bg-slate-900">{e}</p>)}</div></Card><Card><h2 className="flex items-center gap-2 text-lg font-black dark:text-white"><MessageCircle size={18}/>Atividades recentes</h2><div className="mt-4 space-y-3">{displayActivity.slice(0, 5).map(item => <p key={item.id} className="text-sm text-slate-600 dark:text-slate-300">{item.message}</p>)}</div></Card><Card><h2 className="flex items-center gap-2 text-lg font-black dark:text-white"><AlertTriangle size={18}/>Alertas vivos</h2><div className="mt-4 space-y-2">{demo.notifications.filter(item => !item.read).slice(0, 3).map(item => <p key={item.id} className={`rounded-2xl p-3 text-sm font-bold ${item.severity === 'critical' ? 'bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-200' : 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-200'}`}>{item.message}</p>)}</div></Card></div>
  </>;
}
