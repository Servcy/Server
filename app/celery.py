import os

from celery import Celery

from app.utils.redis import create_redis_instance

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

redis_instance = create_redis_instance()

app = Celery("servcy")

# Using a string here means the worker will not have to pickle the object when using Windows.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
