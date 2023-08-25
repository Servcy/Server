import os
from configparser import RawConfigParser
from pathlib import Path

import newrelic.agent
from django.core.wsgi import get_wsgi_application

BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_FILE = BASE_DIR / "config/config.ini"

NEW_RELIC_CONFIG_FILE = BASE_DIR / "config/new_relic.ini"

config = RawConfigParser()

config.read(CONFIG_FILE)

HOST_TYPE = config.get("main", "host_type")

DEBUG = HOST_TYPE == "development"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

application = get_wsgi_application()

if not DEBUG:
    newrelic.agent.initialize(NEW_RELIC_CONFIG_FILE)
    application = newrelic.agent.WSGIApplicationWrapper(application)
