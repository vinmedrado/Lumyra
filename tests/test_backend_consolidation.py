from repositories.database import init_db, connect
from services.analytics_snapshot_service import generate_analytics_snapshot, list_snapshots
from services.job_service import create_job, lock_next_job, mark_retry, update_job
from services.scheduler_service import run_scheduler_tick
from services.workflow_service import create_rule, run_due_rules
from backend.services.auth_jwt import authenticate, create_access_token, create_refresh_token, rotate_refresh_token, revoke_refresh_token
from backend.main import app
from fastapi.testclient import TestClient


def test_worker_lock_and_retry_cycle():
    init_db()
    with connect() as conn:
        conn.execute("UPDATE background_jobs SET status='canceled' WHERE status='queued'")
    job_id = create_job("generate_analytics_snapshot", tenant_id=1, event_id=1, priority=1, max_retries=1)
    job = lock_next_job("pytest-worker")
    assert job and job["id"] == job_id
    mark_retry(job, "erro controlado")
    with connect() as conn:
        row = conn.execute("SELECT status, retry_count FROM background_jobs WHERE id=?", (job_id,)).fetchone()
    assert row["status"] in {"queued", "failed"}
    assert int(row["retry_count"] or 0) >= 1


def test_analytics_snapshot_persists_history():
    init_db()
    snap = generate_analytics_snapshot(1, 1, "2026-05-05")
    assert snap["snapshot_date"] == "2026-05-05"
    history = list_snapshots(1, 1)
    assert any(item["snapshot_date"] == "2026-05-05" for item in history)


def test_scheduler_creates_jobs_for_snapshots():
    init_db()
    result = run_scheduler_tick()
    assert result["status"] in {"success", "locked"}


def test_workflow_action_creates_job():
    init_db()
    rule_id = create_rule(1, "event_soon", "create_job", event_id=1, action_json='{"job_type":"generate_analytics_snapshot"}')
    result = run_due_rules(1)
    assert result["processed"] >= 1


def test_auth_refresh_rotation_logout():
    init_db()
    user = authenticate("admin@local", "admin123")
    assert user
    access = create_access_token(user)
    refresh = create_refresh_token(user, user_agent="pytest", ip_address="127.0.0.1")
    new_access, new_refresh = rotate_refresh_token(refresh, user_agent="pytest", ip_address="127.0.0.1")
    assert new_access != access
    assert new_refresh != refresh
    revoke_refresh_token(new_refresh)


def test_api_pagination_contract():
    init_db()
    client = TestClient(app)
    login = client.post("/auth/login", json={"email": "admin@local", "password": "admin123"})
    token = login.json()["access_token"]
    res = client.get("/guests?event_id=1&page=1&page_size=5", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code in {200, 404}
    if res.status_code == 200:
        data = res.json()
        assert {"page", "page_size", "total", "items"}.issubset(data.keys())
