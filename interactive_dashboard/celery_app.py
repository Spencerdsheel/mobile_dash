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
    'update-dashboard-data-every-5-minutes': {
        'task': 'dashboard.tasks.update_dashboard_data',
        'schedule': crontab(minute='*/5')
    },
}

# import os
# from celery import Celery
# from celery.schedules import crontab

# # Set the default Django settings module for the 'celery' program.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interactive_dashboard.settings')

# app = Celery('interactive_dashboard')

# #Load task modules from all registere Django app configs.
# app.config_from_object('django.conf.settings', namespace='CELERY')
# app.autodiscover_tasks(['dashboard'])

# #Define the beat schedule to run task every n minutes.
# app.conf.beat_schedule = {
#     'update-dashboard-data-every-5-minutes':{
#         'task': 'dashboard.tasks.update_dashboard_data',
#         'schedule': crontab(minute='*/5')  #Every 5 minutes
#     },  
# }