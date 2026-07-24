import { useCallback, useEffect, useState } from 'react';
import { DataTable } from '../../components/ui/DataTable';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { LoadingState } from '../../components/ui/LoadingState';
import { PageHeader } from '../../components/ui/PageHeader';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { demoGuests } from '../../lib/demoData';
import { eventsApi, guestsApi, hasStoredAccessToken } from '../../services/api';
import type { Guest } from '../../types/domain';

export function GuestsPage() {
  const isVisualDemo = !hasStoredAccessToken();
  const [rows, setRows] = useState<Guest[]>(isVisualDemo ? demoGuests : []);
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

  return <>
    <PageHeader
      eyebrow={isVisualDemo ? 'Demonstração visual' : 'Dados da API'}
      title="Convidados"
      subtitle={`${rows.length} convidado(s) exibido(s), com RSVP e mesa consolidados.`}
    />
    {rows.length ? <DataTable rows={rows} columns={[
      { key: 'name', header: 'Nome' },
      { key: 'phone', header: 'Telefone' },
      {
        key: 'rsvp_status',
        header: 'RSVP',
        render: guest => <StatusBadge status={guest.rsvp_status === 'confirmed' ? 'success' : guest.rsvp_status === 'pending' ? 'warning' : 'neutral'}>{guest.rsvp_status || 'pending'}</StatusBadge>,
      },
      { key: 'table_name', header: 'Mesa' },
      { key: 'group_name', header: 'Grupo' },
    ]} /> : <EmptyState title="Nenhum convidado cadastrado ainda" description="Importe uma planilha, CSV ou VCF para começar." actionLabel="Importar convidados" />}
  </>;
}
