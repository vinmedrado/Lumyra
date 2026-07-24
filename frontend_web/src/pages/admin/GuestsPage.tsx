import { useCallback, useEffect, useState } from 'react';
import { DataTable } from '../../components/ui/DataTable';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { LoadingState } from '../../components/ui/LoadingState';
import { PageHeader } from '../../components/ui/PageHeader';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { demoActions, useDemoStore, type DemoRsvpStatus } from '../../demo/demoStore';
import { eventsApi, guestsApi, hasStoredAccessToken } from '../../services/api';
import type { Guest } from '../../types/domain';

export function GuestsPage() {
  const isVisualDemo = !hasStoredAccessToken();
  const demo = useDemoStore();
  const [rows, setRows] = useState<Guest[]>([]);
  const [loading, setLoading] = useState(!isVisualDemo);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (isVisualDemo) return;
    setLoading(true);
    setError('');
    try {
      const events = await eventsApi.list();
      if (!events.length) throw new Error('Cadastre um evento antes de incluir convidados.');
      const response = await guestsApi.list({ event_id: events[0].id, page: 1, page_size: 100 });
      setRows(response.items);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Não foi possível carregar convidados.');
    } finally {
      setLoading(false);
    }
  }, [isVisualDemo]);

  useEffect(() => { void load(); }, [load]);

  if (loading) return <LoadingState label="Carregando convidados..." />;
  if (error) return <ErrorState description={error} onRetry={load} />;

  const displayRows: Guest[] = isVisualDemo ? demo.guests.map(guest => ({
    id: guest.id,
    name: guest.name,
    phone: guest.phone,
    rsvp_status: guest.status,
    table_name: demo.tables.find(table => table.id === guest.tableId)?.name || 'Sem mesa',
    group_name: guest.group,
  })) : rows;

  return <>
    <PageHeader
      eyebrow={isVisualDemo ? 'Demonstração visual' : 'Dados da API'}
      title="Convidados"
      subtitle={`${displayRows.length} convidado(s) exibido(s), com RSVP e mesa consolidados entre as personas.`}
    />
    {displayRows.length ? <DataTable rows={displayRows} columns={[
      { key: 'name', header: 'Nome' },
      { key: 'phone', header: 'Telefone' },
      {
        key: 'rsvp_status',
        header: 'RSVP',
        render: guest => isVisualDemo
          ? <select aria-label={`RSVP de ${guest.name}`} value={guest.rsvp_status || 'pending'} onChange={event => demoActions.updateGuestStatus(Number(guest.id), event.target.value as DemoRsvpStatus)} className="rounded-xl border border-brand-100 bg-white px-3 py-2 text-xs font-bold"><option value="confirmed">Confirmado</option><option value="pending">Pendente</option><option value="declined">Não irá</option></select>
          : <StatusBadge status={guest.rsvp_status === 'confirmed' ? 'success' : guest.rsvp_status === 'pending' ? 'warning' : 'neutral'}>{guest.rsvp_status || 'pending'}</StatusBadge>,
      },
      {
        key: 'table_name',
        header: 'Mesa',
        render: guest => isVisualDemo
          ? <select aria-label={`Mesa de ${guest.name}`} value={demo.guests.find(item => item.id === guest.id)?.tableId || ''} onChange={event => demoActions.assignGuestTable(Number(guest.id), event.target.value ? Number(event.target.value) : null)} className="rounded-xl border border-brand-100 bg-white px-3 py-2 text-xs"><option value="">Sem mesa</option>{demo.tables.map(table => <option key={table.id} value={table.id}>{table.name}</option>)}</select>
          : guest.table_name || 'Sem mesa',
      },
      { key: 'group_name', header: 'Grupo' },
    ]} /> : <EmptyState title="Nenhum convidado cadastrado ainda" description="Importe uma planilha, CSV ou VCF para começar." actionLabel="Importar convidados" />}
  </>;
}
