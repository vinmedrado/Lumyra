import { PageHeader } from '../../components/ui/PageHeader';
import { SpotifyPlaylistCard } from '../../components/ui/SpotifyPlaylistCard';
import { MusicSuggestionsList } from '../../components/ui/MusicSuggestionsList';

export function PlaylistPage() {
  return <>
    <PageHeader
      eyebrow="Experiência dos noivos"
      title="Playlist do casamento"
      subtitle="Uma forma simples e elegante de envolver os convidados antes da festa começar."
    />
    <div className="grid gap-6">
      <SpotifyPlaylistCard />
      <MusicSuggestionsList readonly />
    </div>
  </>;
}
