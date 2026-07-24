import { useState } from 'react';
import { CheckCircle2, Music2, Send } from 'lucide-react';
import { isDemoMode, musicSuggestionsApi } from '../../services/api';
import { DEMO_GUEST_TOKEN } from '../../lib/demoData';
import { Button } from './Button';
import { Card } from './Card';
import { FormInput } from './FormInput';

export function MusicSuggestionForm({ guestToken, guestName = '' }: { guestToken: string; guestName?: string }) {
  const [name, setName] = useState(guestName);
  const [song, setSong] = useState('');
  const [artist, setArtist] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  async function submit() {
    setError('');
    if (!song.trim() || !artist.trim()) {
      setError('Informe o nome da música e o artista.');
      return;
    }
    setLoading(true);
    try {
      if (!(isDemoMode() && guestToken === DEMO_GUEST_TOKEN)) {
        await musicSuggestionsApi.createPublic({
          guest_token: guestToken,
          guest_name: name || 'Convidado',
          song_name: song,
          artist_name: artist,
          message,
        });
      }
      setSent(true);
      setSong('');
      setArtist('');
      setMessage('');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Não foi possível enviar sua sugestão agora.');
    } finally {
      setLoading(false);
    }
  }

  return <Card className="relative overflow-hidden border-brand-100 bg-gradient-to-br from-white via-purple-50/70 to-gold-50 dark:border-white/10 dark:from-white/10 dark:via-brand-950/50 dark:to-amber-950/20">
    <div className="pointer-events-none absolute -left-20 -top-20 h-56 w-56 rounded-full bg-brand-400/10 blur-3xl" />
    <div className="mb-5 flex items-start gap-3">
      <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-800 dark:bg-white/10 dark:text-gold-100"><Music2 /></div>
      <div>
        <p className="text-xs font-black uppercase tracking-[.2em] text-gold-600">Sugestão musical</p>
        <h3 className="lumyra-display mt-1 text-3xl font-black text-ink dark:text-white">Tem uma música que não pode faltar?</h3>
        <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">Compartilhe sua sugestão com os noivos. Eles podem aprovar e adicionar manualmente na playlist oficial.</p>
      </div>
    </div>

    {sent ? <div className="rounded-3xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-800 dark:border-emerald-300/20 dark:bg-emerald-400/10 dark:text-emerald-100">
      <div className="flex items-center gap-2 font-black"><CheckCircle2 size={18} /> Sugestão enviada!</div>
      <p className="mt-1 text-sm">Sua música foi enviada para os noivos. Obrigado por participar da festa.</p>
      <Button type="button" variant="secondary" className="mt-4" onClick={() => setSent(false)}>Enviar outra música</Button>
    </div> : <div className="grid gap-4">
      <FormInput label="Seu nome" value={name} onChange={event => setName(event.target.value)} placeholder="Ex: Marina Oliveira" />
      <div className="grid gap-4 md:grid-cols-2">
        <FormInput label="Nome da música" value={song} onChange={event => setSong(event.target.value)} placeholder="Ex: Perfect" />
        <FormInput label="Artista" value={artist} onChange={event => setArtist(event.target.value)} placeholder="Ex: Ed Sheeran" />
      </div>
      <label className="block text-sm font-bold text-slate-700 dark:text-slate-200">Mensagem opcional<textarea value={message} onChange={event => setMessage(event.target.value)} placeholder="Por que essa música combina com a festa?" className="mt-2 min-h-24 w-full rounded-3xl border border-brand-100 bg-white px-4 py-3 text-sm outline-none transition focus:border-brand-500 dark:border-white/10 dark:bg-white/10" /></label>
      {error && <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm font-bold text-red-700 dark:bg-red-400/10 dark:text-red-100">{error}</p>}
      <Button type="button" onClick={submit} disabled={loading}>{loading ? 'Enviando...' : 'Enviar sugestão'} <Send size={16} /></Button>
      {isDemoMode() && guestToken === DEMO_GUEST_TOKEN && <p className="rounded-2xl bg-brand-50 px-4 py-3 text-xs font-bold text-brand-800 dark:bg-white/10 dark:text-purple-100">Demonstração de portfólio: a interação acontece somente neste navegador.</p>}
      <p className="text-xs leading-5 text-slate-500 dark:text-slate-400">A playlist continua sob curadoria dos noivos. Respeito e bom senso prevalecem.</p>
    </div>}
  </Card>;
}
