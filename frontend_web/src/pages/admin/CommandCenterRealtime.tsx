import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, MessageCircle } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { MetricCard } from '../../components/ui/MetricCard';
import { PageHeader } from '../../components/ui/PageHeader';
import { LiveIndicator } from '../../components/realtime/LiveIndicator';
import { useRealtime } from '../../hooks/useRealtime';
import { notificationsApi } from '../../services/api';
import type { ActivityItem, OnlineUser } from '../../types/domain';

export function CommandCenterRealtime() {
  const { status, lastEvent } = useRealtime();
  const [events, setEvents] = useState<string[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [online, setOnline] = useState<OnlineUser[]>([]);
  useEffect(() => { notificationsApi.activity().then(d => setActivity(d.items || [])).catch(() => undefined); notificationsApi.presence().then(d => setOnline(d.items || [])).catch(() => undefined); }, []);
  useEffect(() => { if (lastEvent) setEvents(prev => [`${lastEvent.type}`, ...prev].slice(0, 8)); }, [lastEvent]);
  return <><PageHeader eyebrow="Ao vivo" title="Command Center Realtime" subtitle="Eventos, jobs, alertas, usuários online e atividade operacional sem refresh manual." actions={<LiveIndicator status={status} />} />
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <MetricCard metric={{ label: 'Eventos realtime', value: events.length, helper: 'Recebidos nesta sessão', status: 'info' }} />
      <MetricCard metric={{ label: 'Usuários online', value: online.length, helper: 'No tenant atual', status: 'success' }} />
      <MetricCard metric={{ label: 'Alertas críticos', value: 2, helper: 'Demo operacional', status: 'danger' }} />
      <MetricCard metric={{ label: 'Jobs ativos', value: 4, helper: 'Fila e workers', status: 'warning' }} />
    </div>
    <div className="mt-6 grid gap-6 lg:grid-cols-3"><Card><h2 className="flex items-center gap-2 text-lg font-black dark:text-white"><Activity size={18}/>Eventos ao vivo</h2><div className="mt-4 space-y-2">{events.map((e, idx) => <p key={idx} className="rounded-2xl bg-slate-50 p-3 text-sm dark:bg-slate-900">{e}</p>)}</div></Card><Card><h2 className="flex items-center gap-2 text-lg font-black dark:text-white"><MessageCircle size={18}/>Atividades recentes</h2><div className="mt-4 space-y-3">{activity.slice(0, 5).map(item => <p key={item.id} className="text-sm text-slate-600 dark:text-slate-300">{item.message}</p>)}</div></Card><Card><h2 className="flex items-center gap-2 text-lg font-black dark:text-white"><AlertTriangle size={18}/>Alertas vivos</h2><div className="mt-4 space-y-2"><p className="rounded-2xl bg-rose-50 p-3 text-sm font-bold text-rose-700 dark:bg-rose-950 dark:text-rose-200">Mensagens com erro aguardando retry</p><p className="rounded-2xl bg-amber-50 p-3 text-sm font-bold text-amber-700 dark:bg-amber-950 dark:text-amber-200">Convidados sem mesa definida</p></div></Card></div>
  </>;
}
