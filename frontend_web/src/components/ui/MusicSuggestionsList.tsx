import { useCallback, useEffect, useState } from 'react';
import { Check, Music2, RefreshCw, X } from 'lucide-react';
import { musicSuggestionsApi } from '../../services/api';
import { Button } from './Button';
import { Card } from './Card';
import { EmptyState } from './EmptyState';
import { StatusBadge } from './StatusBadge';

type Suggestion = {
  id: number;
  guest_name?: string;
  song_name: string;
  artist_name: string;
  message?: string;
  status: string;
  created_at?: string;
};

function statusLabel(status: string) {
  if (status === 'approved') return 'Aprovada';
  if (status === 'rejected') return 'Recusada';
  if (status === 'added') return 'Adicionada';
  return 'Pendente';
}

export function MusicSuggestionsList({ eventId = 1, readonly = false }: { eventId?: number; readonly?: boolean }) {
  const [items, setItems] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const response = await musicSuggestionsApi.list({ event_id: eventId, limit: 100 });
      setItems(response || []);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Não foi possível carregar sugestões.');
    } finally { setLoading(false); }
  }, [eventId]);

  async function update(id: number, status: string) {
    await musicSuggestionsApi.updateStatus(id, status);
    await load();
  }

  useEffect(() => { void load(); }, [load]);

  return <Card>
    <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-3"><div className="grid h-11 w-11 place-items-center rounded-2xl bg-brand-50 text-brand-800 dark:bg-white/10 dark:text-gold-100"><Music2 /></div><div><h2 className="text-xl font-black text-ink dark:text-white">Sugestões dos convidados</h2><p className="text-sm text-slate-500 dark:text-slate-300">Curadoria musical enviada pelo portal do convidado.</p></div></div>
      <Button type="button" variant="secondary" onClick={load}><RefreshCw size={16} /> Atualizar</Button>
    </div>
    {error && <p className="mb-4 rounded-2xl bg-red-50 px-4 py-3 text-sm font-bold text-red-700 dark:bg-red-400/10 dark:text-red-100">{error}</p>}
    {loading ? <p className="text-sm text-slate-500 dark:text-slate-300">Carregando sugestões...</p> : items.length === 0 ? <EmptyState title="Nenhuma sugestão ainda" description="Quando os convidados enviarem músicas pelo portal, elas aparecerão aqui." /> : <div className="space-y-3">
      {items.map(item => <div key={item.id} className="rounded-3xl border border-brand-100 bg-white p-4 shadow-soft dark:border-white/10 dark:bg-white/10">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-lg font-black text-ink dark:text-white">{item.song_name}</p>
            <p className="text-sm font-bold text-slate-500 dark:text-slate-300">{item.artist_name} · sugerida por {item.guest_name || 'Convidado'}</p>
            {item.message && <p className="mt-3 rounded-2xl bg-brand-50 px-4 py-3 text-sm leading-6 text-slate-700 dark:bg-white/10 dark:text-slate-200">“{item.message}”</p>}
          </div>
          <StatusBadge status={item.status === 'approved' || item.status === 'added' ? 'success' : item.status === 'rejected' ? 'danger' : 'warning'}>{statusLabel(item.status)}</StatusBadge>
        </div>
        {!readonly && <div className="mt-4 flex flex-wrap gap-2">
          <Button type="button" variant="secondary" onClick={() => update(item.id, 'approved')}><Check size={16} /> Aprovar</Button>
          <Button type="button" variant="secondary" onClick={() => update(item.id, 'added')}>Marcar adicionada</Button>
          <Button type="button" variant="secondary" onClick={() => update(item.id, 'rejected')}><X size={16} /> Recusar</Button>
        </div>}
      </div>)}
    </div>}
  </Card>;
}
