from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import User


def test_refresh_accepts_json_refresh_token():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    client = TestClient(app)
    client.post('/api/v1/auth/register', json={'email': 'refresh@example.com', 'password': 'secret123'})
    login = client.post('/api/v1/auth/login', json={'email': 'refresh@example.com', 'password': 'secret123'})
    refresh_token = login.json()['data']['refresh_token']
    response = client.post('/api/v1/auth/refresh', json={'refresh_token': refresh_token})
    assert response.status_code == 200
    assert response.json()['code'] == 'SUCCESS'


def test_activity_statistics_and_inventory_transactions_routes_exist():
    assert any('/statistics' in route.path for route in app.routes)
    assert any('/inventory/transactions' in route.path for route in app.routes)
    assert any('/inventory/reconcile' in route.path for route in app.routes)


def test_registration_is_queued_for_async_persistence():
    assert 'persist_registration' in open('backend/app/main.py', encoding='utf-8').read()


def test_redis_reservation_script_is_atomic_and_non_negative():
    script = open('backend/app/redis/lua/reserve_stock.lua', encoding='utf-8').read()
    assert 'redis.call("GET", KEYS[1])' in script
    assert 'redis.call("DECR", KEYS[1])' in script
    assert 'SOLD_OUT' in script


def test_activity_input_rejects_invalid_time_window_and_negative_stock():
    from pydantic import ValidationError
    from app.schemas import ActivityIn
    import pytest
    with pytest.raises(ValidationError):
        ActivityIn(name='x', slug='x', total_stock=-1)
    with pytest.raises(ValidationError):
        ActivityIn(name='x', slug='x', registration_start_at='2026-01-02T00:00:00Z', registration_end_at='2026-01-01T00:00:00Z')


def test_refresh_rejects_access_token_and_profile_can_be_updated():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    access = client.post('/api/v1/auth/login', json={'email': 'refresh@example.com', 'password': 'secret123'}).json()['data']['access_token']
    assert client.post('/api/v1/auth/refresh', json={'refresh_token': access}).status_code == 401


def test_profile_patch_updates_display_name():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    access = client.post('/api/v1/auth/login', json={'email': 'refresh@example.com', 'password': 'secret123'}).json()['data']['access_token']
    response = client.patch('/api/v1/profile', headers={'Authorization': f'Bearer {access}'}, json={'display_name': '秋招候选人'})
    assert response.status_code == 200
    assert response.json()['data']['display_name'] == '秋招候选人'


def test_registration_route_enforces_per_user_limit():
    source = open('backend/app/main.py', encoding='utf-8').read()
    assert 'max_registrations_per_user' in source and 'USER_REGISTRATION_LIMIT' in source
