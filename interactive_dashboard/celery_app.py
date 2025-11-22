import os
from celery import Celery
from celery.schedules import crontab
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s:%(name)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interactive_dashboard.settings')

app = Celery('interactive_dashboard')

logger.info("🚀 Initializing Celery app...")
app.config_from_object('django.conf.settings', namespace='CELERY')

app.autodiscover_tasks(['dashboard'])

logger.info("🕒 Setting Celery beat schedule...")

app.conf.beat_schedule = {
    'update-booking-cache-every-5-minutes': {
        'task': 'dashboard.tasks.update_booking_cache',
        'schedule': crontab(minute='*/20'),
        'options': {'queue': 'booking_queue'},
    },
    'update-validator-cache-every-10-minutes': {
        'task': 'dashboard.tasks.update_validator_cache',
        'schedule': crontab(minute='*/30'),
        'options': {'queue': 'validator_queue'},
    },
    'update-user-cache-every-15-minutes': {
        'task': 'dashboard.tasks.update_user_cache',
        'schedule': crontab(minute='*/25'),
        'options': {'queue': 'user_queue'},
    },
}

logger.info("✅ Celery app successfully configured and beat schedule loaded.")
