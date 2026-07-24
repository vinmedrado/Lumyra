import { ExternalLink, Music2, QrCode } from 'lucide-react';
import { Card } from './Card';
import { Button } from './Button';

export type PlaylistExperience = {
  playlist_url: string;
  title?: string;
  description?: string;
  etiquette_message?: string;
  is_active?: boolean;
};

const fallbackPlaylist: PlaylistExperience = {
  playlist_url: 'https://open.spotify.com/',
  title: 'Playlist do casamento',
  description: 'Quem faz a festa é você: salve a playlist do casamento e compartilhe suas melhores músicas para esse momento ficar ainda mais inesquecível.',
  etiquette_message: 'Pedimos apenas bom senso e carinho: escolha músicas que combinem com o clima do casamento e respeitem todos os convidados.',
  is_active: true,
};

function qrSource(url: string) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=260x260&margin=12&data=${encodeURIComponent(url)}`;
}

export function SpotifyPlaylistCard({ playlist = fallbackPlaylist, variant = 'client' }: { playlist?: PlaylistExperience; variant?: 'client' | 'guest' | 'admin' }) {
  const data = { ...fallbackPlaylist, ...playlist };
  const isGuest = variant === 'guest';

  return <Card className="relative overflow-hidden border-emerald-100 bg-gradient-to-br from-white via-emerald-50/50 to-gold-50 dark:border-white/10 dark:from-white/10 dark:via-emerald-950/30 dark:to-brand-950/60">
    <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-emerald-400/15 blur-3xl" />
    <div className="grid gap-6 lg:grid-cols-[1fr_260px] lg:items-center">
      <div>
        <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-emerald-100 px-3 py-1 text-xs font-black uppercase tracking-[.18em] text-emerald-800 dark:bg-emerald-400/10 dark:text-emerald-100">
          <Music2 size={15} /> Experiência musical
        </div>
        <h2 className="lumyra-display text-4xl font-black text-ink dark:text-white">{isGuest ? 'Quem faz a festa é você' : data.title}</h2>
        <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-300">{data.description}</p>
        <div className="mt-5 rounded-3xl border border-amber-200 bg-amber-50/80 p-4 text-sm font-semibold leading-6 text-amber-900 dark:border-amber-200/20 dark:bg-amber-300/10 dark:text-amber-100">
          {data.etiquette_message}
        </div>
        <div className="mt-5 flex flex-wrap gap-3">
          <a href={data.playlist_url} target="_blank" rel="noreferrer"><Button>Abrir playlist <ExternalLink size={16} /></Button></a>
          <span className="inline-flex items-center gap-2 rounded-2xl border border-emerald-200 bg-white px-4 py-2 text-sm font-black text-emerald-800 dark:border-white/10 dark:bg-white/10 dark:text-emerald-100"><QrCode size={16} /> Escaneie e salve</span>
        </div>
      </div>
      <div className="mx-auto w-full max-w-[260px] rounded-[2rem] border border-white bg-white p-4 shadow-soft dark:border-white/10 dark:bg-white/10">
        <img src={qrSource(data.playlist_url)} alt="QR Code da playlist do casamento" className="h-full w-full rounded-[1.4rem] bg-white p-2" />
        <p className="mt-3 text-center text-xs font-bold text-slate-500 dark:text-slate-300">Aponte a câmera para participar</p>
      </div>
    </div>
  </Card>;
}
