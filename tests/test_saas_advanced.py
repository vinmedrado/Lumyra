from fastapi.testclient import TestClient
from backend.main import app
from repositories.database import init_db
from services.workflow_service import create_rule, list_rules, run_due_rules
from services.analytics_service import event_analytics
from services.import_service import preview_guest_file


def test_api_health_and_auth():
    init_db()
    client = TestClient(app)
    assert client.get('/health').status_code == 200
    response = client.post('/auth/login', json={'email': 'admin@local', 'password': 'admin123'})
    assert response.status_code == 200
    token = response.json()['access_token']
    me = client.get('/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me.status_code == 200
    assert me.json()['role'] == 'ADMIN'


def test_workflow_engine_basic():
    init_db()
    rule_id = create_rule(1, 'message_failed', 'generate_alert')
    assert rule_id > 0
    assert list_rules(1)
    result = run_due_rules(1)
    assert 'processed' in result


def test_analytics_service_contract():
    init_db()
    data = event_analytics(1)
    assert 'confirmation_rate' in data
    assert 'table_occupancy' in data


def test_import_preview_csv():
    raw = b'nome,telefone,grupo\nAna,11999999999,Familia A\n'
    rows, report = preview_guest_file(raw, 'convidados.csv')
    assert report['total'] == 1
    assert rows[0]['name'] == 'Ana'
