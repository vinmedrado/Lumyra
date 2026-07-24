import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { useRoute } from 'wouter';
import { CheckCircle2, Heart, MapPin, UsersRound } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { ErrorState } from '../../components/ui/ErrorState';
import { FormInput } from '../../components/ui/FormInput';
import { LoadingState } from '../../components/ui/LoadingState';
import { MusicSuggestionForm } from '../../components/ui/MusicSuggestionForm';
import { Select } from '../../components/ui/Select';
import { SpotifyPlaylistCard } from '../../components/ui/SpotifyPlaylistCard';
import logoDark from '../../assets/branding/lumyra-logo-dark.svg';
import { DEMO_GUEST_TOKEN, demoGuestPortalContext } from '../../lib/demoData';
import { guestPortalApi, isDemoMode } from '../../services/api';
import type { GuestPortalContext, GuestResponseStatus } from '../../types/domain';

const labelClassName = 'text-purple-50/90 dark:text-purple-50/90';

export function GuestPortal() {
  const [, params] = useRoute('/guest/:token');
  const token = params?.token || '';
  const isStaticDemo = isDemoMode() && token === DEMO_GUEST_TOKEN;
  const [context, setContext] = useState<GuestPortalContext | null>(null);
  const [statuses, setStatuses] = useState<Record<number, GuestResponseStatus>>({});
  const [phone, setPhone] = useState('');
  const [needsBus, setNeedsBus] = useState(false);
  const [pickup, setPickup] = useState('');
  const [dietary, setDietary] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = isStaticDemo
        ? demoGuestPortalContext
        : await guestPortalApi.read(token);
      setContext(data);
      setStatuses(Object.fromEntries(data.invitation.members.map(member => [member.id, member.status])));
      setPhone(data.response.phone || '');
      setNeedsBus(Boolean(data.response.needs_bus));
      setPickup(data.response.bus_pickup_point || '');
      setDietary(data.response.dietary_restrictions || '');
      setNotes(data.response.notes || '');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Este convite não está disponível.');
    } finally {
      setLoading(false);
    }
  }, [isStaticDemo, token]);

  useEffect(() => { void load(); }, [load]);

  const confirmedCount = useMemo(
    () => context?.invitation.members.filter(member => statuses[member.id] === 'confirmed').length ?? 0,
    [context, statuses],
  );

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!context) return;
    setSaving(true);
    setError('');
    try {
      const payload = {
        members: context.invitation.members.map(member => ({
          guest_id: member.id,
          status: statuses[member.id] || 'pending',
        })),
        phone,
        needs_bus: needsBus,
        bus_pickup_point: pickup,
        dietary_restrictions: dietary,
        notes,
      };
      const result = isStaticDemo
        ? { members: payload.members.map(member => ({ id: member.guest_id, status: member.status })) }
        : await guestPortalApi.submit(token, payload);
      setStatuses(Object.fromEntries(result.members.map((member: any) => [member.id, member.status])));
      setSent(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Não foi possível salvar sua resposta.');
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="grid min-h-screen place-items-center bg-[#09060f] p-4"><LoadingState label="Abrindo seu convite..." /></div>;
  if (!context) return <div className="grid min-h-screen place-items-center bg-[#09060f] p-4"><ErrorState title="Convite indisponível" description={error} onRetry={load} /></div>;

  if (sent) return <div className="grid min-h-screen place-items-center bg-[radial-gradient(circle_at_20%_10%,rgba(139,92,246,.18),transparent_28%),linear-gradient(135deg,#F7F8FB,#FFF8E8)] p-4 dark:bg-[#09060f]">
    <Card className="max-w-lg text-center">
      <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-emerald-50 text-emerald-600"><CheckCircle2 size={34} /></div>
      <h1 className="lumyra-display mt-4 text-4xl font-black text-ink dark:text-white">Resposta enviada</h1>
      <p className="mt-2 text-slate-500 dark:text-slate-300">A confirmação de <strong>{context.invitation.label}</strong> foi registrada na Lumyra.</p>
      <div className="mt-5 rounded-3xl bg-brand-50 p-4 text-left text-sm text-slate-600 dark:bg-white/10 dark:text-slate-300">
        <p><strong>Confirmados:</strong> {confirmedCount} de {context.invitation.members.length}</p>
        <p><strong>Transporte:</strong> {needsBus ? 'solicitado' : 'não necessário'}</p>
      </div>
      <Button type="button" className="mt-5" onClick={() => setSent(false)}>Editar resposta</Button>
    </Card>
  </div>;

  return <div className="min-h-screen bg-[#09060f] text-white">
    <main className="lumyra-hero mx-auto grid min-h-screen gap-6 p-4 py-8 lg:grid-cols-[.9fr_1.1fr] lg:p-10">
      <section className="flex flex-col justify-center rounded-[2rem] border border-white/10 bg-white/10 p-8 backdrop-blur">
        <img src={logoDark} className="mb-12 h-20 w-fit" alt="Lumyra" />
        <p className="text-sm font-black uppercase tracking-[.28em] text-gold-100">Convite especial</p>
        <h1 className="lumyra-display mt-4 text-6xl font-black">{context.event.name}</h1>
        <p className="mt-4 max-w-md leading-7 text-purple-50">Confirme sua presença de forma simples e segura pelo celular.</p>
        <div className="mt-7 space-y-3 rounded-3xl border border-white/10 bg-white/10 p-5 text-sm text-purple-50">
          {context.event.date && <p><strong>Data:</strong> {context.event.date}</p>}
          {context.event.location && <p className="flex items-center gap-2"><MapPin size={16} /> {context.event.location}</p>}
          <p className="flex items-center gap-2"><UsersRound size={16} /> {context.invitation.type === 'family' ? 'Convite família/grupo' : 'Convite individual'}</p>
        </div>
      </section>

      <Card className="self-center border-white/25 bg-white/[.08] text-white shadow-2xl backdrop-blur-xl dark:text-white">
        <div className="mb-5 flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-2xl bg-white text-brand-800"><Heart /></div>
          <div>
            <p className="text-xs font-black uppercase tracking-[.2em] text-gold-100">Convite para</p>
            <h2 className="text-2xl font-black text-white">{context.invitation.label}</h2>
            <p className="text-sm text-purple-50/80">Escolha uma resposta para cada pessoa.</p>
          </div>
        </div>

        <form onSubmit={submit} className="grid gap-5">
          {isStaticDemo && <p className="rounded-2xl border border-gold-300/30 bg-gold-300/10 px-4 py-3 text-sm font-bold text-gold-100">Demo interativa de portfólio · nenhuma informação será enviada ou armazenada.</p>}
          <div className="rounded-3xl border border-white/10 bg-white/10 p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-black text-white">Quem irá comparecer?</p>
                <p className="text-xs text-purple-50/70">{confirmedCount} de {context.invitation.members.length} confirmado(s)</p>
              </div>
            </div>
            <div className="grid gap-3">
              {context.invitation.members.map(member => <div key={member.id} className="rounded-2xl border border-white/10 bg-white/[.08] p-3">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div><p className="font-black text-white">{member.name}</p><p className="text-xs text-purple-50/70">{member.category || 'Convidado'}</p></div>
                  <select
                    aria-label={`Presença de ${member.name}`}
                    value={statuses[member.id] || 'pending'}
                    onChange={event => setStatuses(current => ({ ...current, [member.id]: event.target.value as GuestResponseStatus }))}
                    className="rounded-xl border border-white/10 bg-white px-3 py-2 text-sm font-bold text-slate-900 outline-none focus:ring-2 focus:ring-gold-300"
                  >
                    <option value="confirmed">Confirma presença</option>
                    <option value="declined">Não irá</option>
                    <option value="pending">Responder depois</option>
                  </select>
                </div>
              </div>)}
            </div>
          </div>

          <FormInput label="Telefone atual" labelClassName={labelClassName} value={phone} onChange={event => setPhone(event.target.value)} placeholder="(11) 99999-9999" />
          <Select label="Precisa de transporte?" labelClassName={labelClassName} value={needsBus ? 'yes' : 'no'} onChange={event => setNeedsBus(event.target.value === 'yes')}>
            <option value="no">Não</option><option value="yes">Sim</option>
          </Select>
          {needsBus && <FormInput label="Ponto de embarque" labelClassName={labelClassName} value={pickup} onChange={event => setPickup(event.target.value)} placeholder="Ex: Shopping ABC" />}
          <FormInput label="Restrição alimentar" labelClassName={labelClassName} value={dietary} onChange={event => setDietary(event.target.value)} placeholder="Ex: vegetariano, sem lactose" />
          <FormInput label="Observações" labelClassName={labelClassName} value={notes} onChange={event => setNotes(event.target.value)} placeholder="Algo que a assessoria precisa saber?" />
          {error && <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{error}</p>}
          <Button disabled={saving}>{saving ? 'Salvando...' : 'Enviar resposta'}</Button>
        </form>
      </Card>

      <div className="lg:col-span-2">
        <div className="grid gap-6 lg:grid-cols-2">
          {context.playlist && <SpotifyPlaylistCard playlist={context.playlist} variant="guest" />}
          <MusicSuggestionForm guestToken={token} guestName={context.invitation.label} />
        </div>
      </div>
    </main>
  </div>;
}
