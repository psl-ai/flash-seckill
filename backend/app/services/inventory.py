from dataclasses import dataclass
import uuid, threading

@dataclass
class ReservationResult:
    code: str
    reservation_id: str | None = None

class InventoryService:
    def __init__(self):
        self._stocks = {}; self._users = {}; self._idem = {}; self._lock = threading.Lock()
    def seed(self, activity_id: str, quantity: int):
        with self._lock: self._stocks[activity_id] = quantity
    def available(self, activity_id: str) -> int: return self._stocks.get(activity_id, 0)
    def reserve(self, activity_id, user_id, key, request_hash=''):
        with self._lock:
            idem = self._idem.get((user_id, key))
            if idem:
                return ReservationResult('IDEMPOTENT_REPLAY' if idem[1] == request_hash else 'IDEMPOTENT_CONFLICT', idem[0])
            if (activity_id, user_id) in self._users: return ReservationResult('ALREADY_REGISTERED')
            if self._stocks.get(activity_id, 0) <= 0: return ReservationResult('SOLD_OUT')
            rid = str(uuid.uuid4()); self._stocks[activity_id] -= 1
            self._users[(activity_id, user_id)] = rid; self._idem[(user_id, key)] = (rid, request_hash)
            return ReservationResult('SUCCESS', rid)
    def release(self, activity_id, reservation_id):
        with self._lock:
            for pair, rid in list(self._users.items()):
                if pair[0] == activity_id and rid == reservation_id:
                    del self._users[pair]; self._stocks[activity_id] = self._stocks.get(activity_id, 0) + 1
                    return ReservationResult('SUCCESS', reservation_id)
            return ReservationResult('NOT_FOUND')
