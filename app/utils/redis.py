from urllib.parse import urlparse

import redis
from django.conf import settings


def create_redis_instance():
    """
    Returns a redis instance
    - If REDIS_SSL is True, it will return a redis instance with SSL enabled
    """

    if settings.REDIS_SSL:
        url = urlparse(settings.REDIS_URL)
        instance = redis.Redis(
            host=url.hostname,
            port=url.port,
            password=url.password,
            ssl=True,
            ssl_cert_reqs=None,
        )
    else:
        instance = redis.Redis.from_url(settings.REDIS_URL, db=0)
    return instance
