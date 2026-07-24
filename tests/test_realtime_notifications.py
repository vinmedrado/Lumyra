from services.notification_service import create_notification, list_notifications, mark_all_read, unread_count
from services.activity_service import record_activity, list_activity
from services.presence_service import update_presence, list_online_users, acquire_lock
from backend.realtime.events import make_event
from backend.realtime.manager import realtime_manager


def test_notification_center_crud():
    item = create_notification(tenant_id=1, title='Mensagem falhou', message='Retry necessário', severity='warning')
    assert item['id']
    assert unread_count(tenant_id=1) >= 1
    items = list_notifications(tenant_id=1, unread_only=True)
    assert any(n['id'] == item['id'] for n in items)
    assert mark_all_read(tenant_id=1) >= 1


def test_activity_and_presence():
    activity = record_activity(tenant_id=1, user_id=1, action_type='guest_updated', entity_type='guest', entity_id=1, message='Convidado atualizado')
    assert activity['message'] == 'Convidado atualizado'
    assert list_activity(tenant_id=1)
    update_presence(user_id=1, tenant_id=1, current_page='/admin/dashboard')
    assert any(u['user_id'] == 1 for u in list_online_users(tenant_id=1))


def test_optimistic_lock_blocks_other_user():
    first = acquire_lock(tenant_id=1, user_id=1, entity_type='guest', entity_id=999, ttl_seconds=60)
    assert first['locked'] is True
    second = acquire_lock(tenant_id=1, user_id=2, entity_type='guest', entity_id=999, ttl_seconds=60)
    assert second['locked'] is False


def test_realtime_event_shape_and_manager_stats():
    event = make_event('notification_created', tenant_id=1, title='Teste')
    assert event.to_dict()['type'] == 'notification_created'
    assert 'connections' in realtime_manager.stats()
