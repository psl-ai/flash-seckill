import os
from celery import Celery
celery_app = Celery('miaoqiang', broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'), backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2'))
celery_app.conf.beat_schedule = {'reconcile': {'task': 'app.tasks.registration_tasks.reconcile_activity_stock', 'schedule': 60.0}}
