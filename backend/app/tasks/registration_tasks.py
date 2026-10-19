from .celery_app import celery_app

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def persist_registration(self, registration_id: int): return {'registration_id': registration_id, 'status': 'confirmed'}

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def expire_reservation(self, reservation_id: str): return {'reservation_id': reservation_id, 'status': 'expired'}

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_registration_notification(self, registration_id: int): return {'registration_id': registration_id, 'status': 'sent'}

@celery_app.task
def reconcile_activity_stock(activity_id: int | None = None): return {'activity_id': activity_id, 'status': 'checked'}

@celery_app.task
def cleanup_idempotency_records(): return {'status': 'cleaned'}
