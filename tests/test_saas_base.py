from services.security_service import hash_password, verify_password
from services.storage_service import tenant_root, ensure_storage
from services.job_service import create_job, update_job, list_jobs
from services.health_service import system_health


def test_password_hash_verify():
    hashed = hash_password("senha-segura")
    assert hashed != "senha-segura"
    assert verify_password("senha-segura", hashed)
    assert not verify_password("outra", hashed)


def test_storage_tenant_root():
    assert ensure_storage() is True
    root = tenant_root(1)
    assert root.exists()


def test_job_lifecycle():
    job_id = create_job("teste_pytest", tenant_id=1, event_id=1)
    update_job(job_id, status="running", progress=50)
    update_job(job_id, status="success", progress=100)
    jobs = list_jobs(limit=5, tenant_id=1)
    assert any(int(j["id"]) == int(job_id) and j["status"] == "success" for j in jobs)


def test_system_health_shape():
    health = system_health()
    assert "database_ok" in health
    assert "storage_ok" in health
    assert "total_events" in health
