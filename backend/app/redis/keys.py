def stock(activity_id: int | str) -> str:
    return f'activity:{activity_id}:stock'


def reservation(activity_id: int | str, user_id: int | str) -> str:
    return f'activity:{activity_id}:user:{user_id}:reservation'


def idempotency(user_id: int | str, endpoint: str, key: str) -> str:
    return f'idempotency:{user_id}:{endpoint}:{key}'
