from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from repositories.database import connect, init_db
from services.guest_portal_service import ensure_link_for_guest


def _create_family_invitation() -> tuple[int, list[int], str]:
    init_db()
    with connect() as conn:
        event_id = int(
            conn.execute(
                """
                INSERT INTO events(tenant_id, name, date, location)
                VALUES (1, 'Evento Família API', '2026-10-10', 'Espaço Teste')
                """
            ).lastrowid
        )
        guest_ids = []
        for name in ("Luzia Teste", "Roberto Teste"):
            guest_ids.append(
                int(
                    conn.execute(
                        """
                        INSERT INTO guests(
                            event_id, tenant_id, name, original_name, group_name,
                            invitation_type, invitation_label, category
                        ) VALUES (?, 1, ?, ?, 'Família Teste', 'family', 'Luzia & Família', 'Família')
                        """,
                        (event_id, name, name),
                    ).lastrowid
                )
            )
    return event_id, guest_ids, ensure_link_for_guest(event_id, guest_ids[0])


def test_public_portal_loads_and_saves_family_rsvp():
    event_id, guest_ids, token = _create_family_invitation()

    with TestClient(app) as client:
        read = client.get(f"/public/guest/{token}")
        assert read.status_code == 200
        data = read.json()["data"]
        assert data["event"]["id"] == event_id
        assert data["invitation"]["type"] == "family"
        assert {member["id"] for member in data["invitation"]["members"]} == set(guest_ids)

        saved = client.post(
            f"/public/guest/{token}/rsvp",
            json={
                "members": [
                    {"guest_id": guest_ids[0], "status": "confirmed"},
                    {"guest_id": guest_ids[1], "status": "declined"},
                ],
                "phone": "5511999999999",
                "needs_bus": True,
                "bus_pickup_point": "Shopping Central",
                "dietary_restrictions": "Sem lactose",
                "notes": "Teste de integração",
            },
        )

    assert saved.status_code == 200
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT guest_id, confirm_presence
            FROM guest_portal_responses
            WHERE event_id=?
            ORDER BY guest_id
            """,
            (event_id,),
        ).fetchall()
    assert {int(row["guest_id"]): row["confirm_presence"] for row in rows} == {
        guest_ids[0]: "confirmed",
        guest_ids[1]: "declined",
    }


def test_public_portal_rejects_guest_outside_invitation():
    _, guest_ids, token = _create_family_invitation()
    with connect() as conn:
        outsider_id = int(
            conn.execute(
                """
                INSERT INTO guests(
                    event_id, tenant_id, name, original_name, invitation_type, invitation_label
                ) VALUES (1, 1, 'Pessoa Externa', 'Pessoa Externa', 'individual', 'Pessoa Externa')
                """
            ).lastrowid
        )

    with TestClient(app) as client:
        response = client.post(
            f"/public/guest/{token}/rsvp",
            json={"members": [{"guest_id": outsider_id, "status": "confirmed"}], "needs_bus": False},
        )

    assert response.status_code == 400
    assert outsider_id not in guest_ids


def test_demo_invitation_is_available_when_demo_mode_is_enabled():
    with TestClient(app) as client:
        response = client.get("/public/guest/lumyra-demo-invitation-token")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["event"]["name"] == "Casamento Ana & João"
    assert data["invitation"]["members"]
