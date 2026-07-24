import { PageHeader } from '../../components/ui/PageHeader';
import { SpotifyPlaylistCard } from '../../components/ui/SpotifyPlaylistCard';
import { MusicSuggestionsList } from '../../components/ui/MusicSuggestionsList';
import { useDemoStore } from '../../demo/demoStore';

export function PlaylistPage() {
  const state = useDemoStore();
  return <>
    <PageHeader
      eyebrow="Experiência dos noivos"
      title="Playlist do casamento"
      subtitle="Uma forma simples e elegante de envolver os convidados antes da festa começar."
    />
    <div className="grid gap-6">
      <SpotifyPlaylistCard playlist={{ playlist_url: state.playlist.url, title: state.playlist.title, description: state.playlist.description, etiquette_message: state.playlist.etiquette }} />
      <MusicSuggestionsList readonly />
    </div>
  </>;
}
