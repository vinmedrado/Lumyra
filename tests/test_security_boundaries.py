from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.main import app
from backend.services.tenant_access import event_belongs_to_tenant
from repositories.database import connect, ensure_default_event, init_db
from services.guest_portal_service import ensure_link_for_guest


def test_event_access_is_scoped_to_tenant():
    init_db()
    with connect() as conn:
        event_id = ensure_default_event(conn)
        conn.execute("UPDATE events SET tenant_id=1 WHERE id=?", (event_id,))

    assert event_belongs_to_tenant(event_id, 1)
    assert not event_belongs_to_tenant(event_id, 999)


def test_websocket_rejects_connection_without_access_token():
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws?tenant_id=1"):
                pass

    assert exc_info.value.code == 4401


def test_public_music_suggestion_requires_valid_guest_token():
    with TestClient(app) as client:
        response = client.post(
            "/music-suggestions/public",
            json={
                "guest_token": "invalid-token-with-enough-length",
                "song_name": "Perfect",
                "artist_name": "Ed Sheeran",
            },
        )

    assert response.status_code == 403


def test_public_music_suggestion_rejects_client_controlled_tenant():
    with TestClient(app) as client:
        response = client.post(
            "/music-suggestions/public",
            json={
                "guest_token": "invalid-token-with-enough-length",
                "tenant_id": 999,
                "song_name": "Perfect",
                "artist_name": "Ed Sheeran",
            },
        )

    assert response.status_code == 422


def test_public_music_suggestion_derives_scope_from_guest_token():
    init_db()
    with connect() as conn:
        event_id = ensure_default_event(conn)
        conn.execute("UPDATE events SET tenant_id=1 WHERE id=?", (event_id,))
        guest_id = int(
            conn.execute(
                """
                INSERT INTO guests(event_id, tenant_id, name, original_name)
                VALUES (?, 1, ?, ?)
                """,
                (event_id, "Convidado Segurança", "Convidado Segurança"),
            ).lastrowid
        )
    token = ensure_link_for_guest(event_id, guest_id)

    with TestClient(app) as client:
        response = client.post(
            "/music-suggestions/public",
            json={
                "guest_token": token,
                "song_name": "Perfect",
                "artist_name": "Ed Sheeran",
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["tenant_id"] == 1
    assert payload["event_id"] == event_id
    assert payload["guest_id"] == guest_id
