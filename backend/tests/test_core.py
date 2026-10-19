import pytest
from app.services.inventory import InventoryService, ReservationResult
from app.services.activity import transition_status, ActivityStatus
from app.core.security import create_access_token, decode_token, hash_password, verify_password

def test_password_and_jwt_roundtrip():
    hashed = hash_password('secret')
    assert hashed != 'secret' and verify_password('secret', hashed)
    token = create_access_token({'sub': 'u1', 'role': 'admin'})
    assert decode_token(token)['sub'] == 'u1'

def test_activity_state_flow():
    assert transition_status(ActivityStatus.DRAFT, 'publish') == ActivityStatus.PUBLISHED
    assert transition_status(ActivityStatus.PUBLISHED, 'open') == ActivityStatus.REGISTRATION_OPEN
    with pytest.raises(ValueError):
        transition_status(ActivityStatus.DRAFT, 'end')

def test_atomic_inventory_and_idempotency():
    inv = InventoryService()
    inv.seed('a', 2)
    one = inv.reserve('a', 'u1', 'k1')
    assert one.code == 'SUCCESS' and inv.available('a') == 1
    replay = inv.reserve('a', 'u1', 'k1')
    assert replay.code == 'IDEMPOTENT_REPLAY'
    duplicate = inv.reserve('a', 'u1', 'k2')
    assert duplicate.code == 'ALREADY_REGISTERED'
    assert inv.reserve('a', 'u2', 'k3').code == 'SUCCESS'
    assert inv.reserve('a', 'u3', 'k4').code == 'SOLD_OUT'
    assert inv.release('a', one.reservation_id).code == 'SUCCESS'

def test_idempotency_conflict():
    inv = InventoryService(); inv.seed('a', 1)
    assert inv.reserve('a', 'u1', 'same', request_hash='x').code == 'SUCCESS'
    assert inv.reserve('a', 'u1', 'same', request_hash='y').code == 'IDEMPOTENT_CONFLICT'
