import { useState } from 'react';
import { Music2 } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { FormInput } from '../../components/ui/FormInput';
import { PageHeader } from '../../components/ui/PageHeader';
import { SpotifyPlaylistCard } from '../../components/ui/SpotifyPlaylistCard';
import { MusicSuggestionsList } from '../../components/ui/MusicSuggestionsList';

export function PlaylistAdminPage() {
  const [url, setUrl] = useState('https://open.spotify.com/');
  const [title, setTitle] = useState('Playlist do casamento');
  const [description, setDescription] = useState('Quem faz a festa é você: salve a playlist do casamento e compartilhe suas melhores músicas para esse momento ficar ainda mais inesquecível.');
  const [etiquette, setEtiquette] = useState('Pedimos apenas bom senso e carinho: escolha músicas que combinem com o clima do casamento e respeitem todos os convidados.');

  return <>
    <PageHeader eyebrow="Experiência musical" title="Playlist e QR Code" subtitle="Configure o link da playlist colaborativa e visualize como os noivos e convidados verão a experiência." />
    <div className="grid gap-6 lg:grid-cols-[.85fr_1.15fr]">
      <Card>
        <div className="mb-5 flex items-center gap-3"><div className="grid h-11 w-11 place-items-center rounded-2xl bg-emerald-50 text-emerald-700"><Music2 /></div><div><h2 className="text-xl font-black text-ink dark:text-white">Configuração</h2><p className="text-sm text-slate-500 dark:text-slate-300">Cole aqui o link público da playlist do Spotify.</p></div></div>
        <div className="space-y-4">
          <FormInput label="Link da playlist Spotify" value={url} onChange={event => setUrl(event.target.value)} placeholder="https://open.spotify.com/playlist/..." />
          <FormInput label="Título" value={title} onChange={event => setTitle(event.target.value)} />
          <label className="block text-sm font-bold text-slate-700 dark:text-slate-200">Mensagem para convidados<textarea value={description} onChange={event => setDescription(event.target.value)} className="mt-2 min-h-28 w-full rounded-3xl border border-brand-100 bg-white px-4 py-3 text-sm outline-none transition focus:border-brand-500 dark:border-white/10 dark:bg-white/10" /></label>
          <label className="block text-sm font-bold text-slate-700 dark:text-slate-200">Aviso de respeito musical<textarea value={etiquette} onChange={event => setEtiquette(event.target.value)} className="mt-2 min-h-24 w-full rounded-3xl border border-brand-100 bg-white px-4 py-3 text-sm outline-none transition focus:border-brand-500 dark:border-white/10 dark:bg-white/10" /></label>
          <Button type="button">Salvar configuração</Button>
          <p className="text-xs text-slate-400">Este patch não altera fluxos existentes. A persistência via API já foi preparada em /playlists para ativação quando desejado.</p>
        </div>
      </Card>
      <SpotifyPlaylistCard playlist={{ playlist_url: url, title, description, etiquette_message: etiquette }} variant="admin" />
    </div>
    <div className="mt-6">
      <MusicSuggestionsList />
    </div>
  </>;
}
