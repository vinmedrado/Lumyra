from __future__ import annotations

from datetime import datetime, timedelta

from db.session import create_all, get_session
from db.models import (
    ActivityFeed,
    AnalyticsSnapshot,
    BackgroundJob,
    Event,
    EventPlaylist,
    EventMusicSuggestion,
    Guest,
    MessageLog,
    Notification,
    Tenant,
    User,
)
from services.security_service import hash_password


def seed_demo_data() -> None:
    """Cria dados de demonstração controlados para portfólio, sem dados reais."""
    create_all()
    with get_session() as session:
        tenant = session.query(Tenant).filter_by(slug="lumyra-demo").first()
        if not tenant:
            tenant = Tenant(name="Lumyra Demo Events", slug="lumyra-demo")
            session.add(tenant)
            session.flush()

        users = [
            ("Assessoria Demo", "admin@lumyra.demo", "ADMIN"),
            ("Ana & João", "noivos@lumyra.demo", "CLIENT"),
            ("Equipe Check-in", "staff@lumyra.demo", "STAFF"),
        ]
        for name, email, role in users:
            if not session.query(User).filter_by(email=email).first():
                session.add(User(tenant_id=tenant.id, name=name, email=email, role=role, password_hash=hash_password("admin123"), is_active=True))

        event = session.query(Event).filter_by(tenant_id=tenant.id, name="Casamento Ana & João").first()
        if not event:
            event = Event(tenant_id=tenant.id, name="Casamento Ana & João", date="2026-09-19", location="Espaço Jardim Aurora")
            session.add(event)
            session.flush()


        if not session.query(EventPlaylist).filter_by(tenant_id=tenant.id, event_id=event.id).first():
            session.add(EventPlaylist(
                tenant_id=tenant.id,
                event_id=event.id,
                playlist_url="https://open.spotify.com/",
                title="Playlist do casamento",
                description="Quem faz a festa é você: salve a playlist do casamento e compartilhe suas melhores músicas para esse momento ficar ainda mais inesquecível.",
                etiquette_message="Pedimos apenas bom senso e carinho: escolha músicas que combinem com o clima do casamento e respeitem todos os convidados.",
                is_active=True,
            ))


        if not session.query(EventMusicSuggestion).filter_by(tenant_id=tenant.id, event_id=event.id).first():
            suggestions = [
                ("Marina Oliveira", "Perfect", "Ed Sheeran", "Essa combina muito com a entrada dos noivos."),
                ("Rafael Lima", "Treasure", "Bruno Mars", "Boa para abrir a pista depois da valsa."),
                ("Beatriz Souza", "A Thousand Years", "Christina Perri", "Clássica e emocionante."),
            ]
            for guest_name, song_name, artist_name, message in suggestions:
                session.add(EventMusicSuggestion(
                    tenant_id=tenant.id,
                    event_id=event.id,
                    guest_name=guest_name,
                    song_name=song_name,
                    artist_name=artist_name,
                    message=message,
                    status="pending",
                    source="seed_demo_data",
                ))

        guests = [
            ("Marina Oliveira", "5511999000001", "", "individual", "Marina Oliveira", "Amigos", "Mesa 03"),
            ("Luzia Oliveira", "5511999000002", "Família Oliveira", "family", "Luzia & Família", "Família", "Mesa 01"),
            ("Carlos Oliveira", "5511999000003", "Família Oliveira", "family", "Luzia & Família", "Família", "Mesa 01"),
            ("Ana Clara Oliveira", "5511999000004", "Família Oliveira", "family", "Luzia & Família", "Família", "Mesa 01"),
            ("Rafael Lima", "5511999000005", "", "individual", "Rafael Lima", "Amigos", "Mesa 04"),
            ("Helena Martins", "5511999000006", "Família Martins", "family", "Helena & Família", "Família", None),
            ("Pedro Martins", "5511999000007", "Família Martins", "family", "Helena & Família", "Família", None),
        ]
        existing = {g.name for g in session.query(Guest).filter_by(event_id=event.id).all()}
        for name, phone, group, invitation_type, invitation_label, category, table in guests:
            if name not in existing:
                session.add(Guest(tenant_id=tenant.id, event_id=event.id, name=name, phone=phone, group_name=group, invitation_type=invitation_type, invitation_label=invitation_label, category=category, final_table=table))

        today = datetime.utcnow().date()
        for i in range(7):
            day = today - timedelta(days=6 - i)
            if not session.query(AnalyticsSnapshot).filter_by(tenant_id=tenant.id, event_id=event.id, snapshot_date=str(day)).first():
                session.add(AnalyticsSnapshot(
                    tenant_id=tenant.id,
                    event_id=event.id,
                    snapshot_date=str(day),
                    total_guests=248,
                    confirmed_guests=140 + i * 7,
                    pending_guests=max(0, 92 - i * 6),
                    declined_guests=8 + i,
                    messages_sent=180 + i * 12,
                    messages_failed=max(0, 9 - i),
                    expenses_total=82000.0,
                    expenses_paid=42000.0 + i * 3000,
                    tables_occupancy_rate=58.0 + i * 4.5,
                ))

        messages = [
            ("sent", "Convite enviado via WhatsApp"),
            ("failed", "Telefone inválido no primeiro disparo"),
            ("sent", "Lembrete de RSVP enviado"),
        ]
        for status, detail in messages:
            session.add(MessageLog(tenant_id=tenant.id, event_id=event.id, status=status, detail=detail, provider="demo", attempt_number=1))

        session.add(Notification(tenant_id=tenant.id, type="warning", severity="warning", title="Convidados sem mesa", message="Existem convidados confirmados ainda sem mesa definida.", related_entity_type="guest"))
        session.add(Notification(tenant_id=tenant.id, type="success", severity="info", title="Demo pronta", message="Dados de demonstração criados com sucesso."))
        session.add(ActivityFeed(tenant_id=tenant.id, action_type="demo_seed", entity_type="event", entity_id=event.id, message="Ambiente demo Lumyra preparado para apresentação."))
        session.add(BackgroundJob(tenant_id=tenant.id, event_id=event.id, type="generate_analytics_snapshot", status="queued", priority=50, metadata_json={"source": "seed_demo_data"}))

    print("Demo data seeded successfully.")


if __name__ == "__main__":
    seed_demo_data()
