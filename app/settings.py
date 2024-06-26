import datetime
import os
import ssl
from configparser import RawConfigParser
from pathlib import Path

import certifi
from newrelic.agent import NewRelicContextFormatter

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# `config.ini` is a file that contains the secret key and other sensitive information
CONFIG_FILE = BASE_DIR / "config/config.ini"
config = RawConfigParser()
config.read(CONFIG_FILE)

SECRET_KEY = config.get("main", "secret_key")

FERNET_KEY = config.get("main", "fernet_key").encode()

HOST_TYPE = config.get("main", "host_type")

DEBUG = HOST_TYPE == "development"

APPEND_SLASH = False

ALLOWED_HOSTS = ["*"]

THIRD_PARTY_APPS = [
    "corsheaders",  # required for cors
    "storages",  # required for s3
    "rest_framework",  # required for rest framework
    "rest_framework_simplejwt.token_blacklist",  # required for jwt
    "django_crontab",  # required for cron jobs
    "django_filters",  # required for filtering
]

LOCAL_APPS = [
    "iam",
    "integration",
    "inbox",
    "document",
    "project",
    "dashboard",
    "notification",
    "billing",
]

OTHER_APPS = ["app", "webhook", "common"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
]

INSTALLED_APPS += THIRD_PARTY_APPS

INSTALLED_APPS += LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "crum.CurrentRequestUserMiddleware",
    "middlewares.RequestUUIDMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",  # for anonymous users
        "rest_framework.throttling.UserRateThrottle",  # for authenticated users
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/minute",
        "user": "300/minute",
    },
    "EXCEPTION_HANDLER": "common.exceptions.servcy_exception_handler",
}

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS = False

if DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
    ]
else:
    CORS_ALLOWED_ORIGINS = [
        "https://web.servcy.com",
    ]

WSGI_APPLICATION = "app.wsgi.application"

ASGI_APPLICATION = "app.asgi.application"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(days=3),
    "REFRESH_TOKEN_LIFETIME": datetime.timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

# Admin Developer Settings
ADMINS = [
    ("Megham", "megham@servcy.com"),
]

# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config.get("database", "name"),
        "USER": config.get("database", "user"),
        "PASSWORD": config.get("database", "password"),
        "HOST": config.get("database", "host"),
        "PORT": config.get("database", "port"),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Log Settings
LOG_PATH = os.path.join(BASE_DIR, "logs")
LOG_HANDLER_DEFAULTS = {
    "level": "DEBUG",
    "class": "logging.handlers.RotatingFileHandler",
    "maxBytes": 1024 * 1024 * 10,
    "backupCount": 5,
    "formatter": "verbose_raw" if DEBUG else "verbose_json",
    "filters": ["user_id", "req_id"],
}
LOG_HANDLERS = {}
LOG_LOGGERS = {}
for app in [*LOCAL_APPS, *OTHER_APPS]:
    LOG_HANDLERS[app] = {
        **LOG_HANDLER_DEFAULTS,
        "filename": os.path.join(LOG_PATH, f"{app}.log"),
    }
    LOG_LOGGERS[app] = {
        "handlers": [app],
        "level": "DEBUG",
        "propagate": True,
    }
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose_raw": {
            "format": "[%(asctime)s] %(levelname)s %(user_identity)s %(request_identity)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "verbose_json": {
            "()": NewRelicContextFormatter,
            "format": "[%(asctime)s] %(levelname)s %(user_identity)s %(request_id)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
        "user_id": {"()": "common.logging_filters.UserIdentifier"},
        "req_id": {"()": "common.logging_filters.RequestIdentifier"},
    },
    "handlers": {
        **LOG_HANDLERS,
        "core": {
            **LOG_HANDLER_DEFAULTS,
            "filename": os.path.join(LOG_PATH, "core.log"),
        },
    },
    "loggers": {
        **LOG_LOGGERS,
        "django": {"handlers": ["core"], "propagate": True, "level": "ERROR"},
        "django.request": {
            "handlers": ["core"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# S3 Settings
AWS_STORAGE_BUCKET_NAME = config.get("aws", "bucket")
AWS_S3_REGION_NAME = config.get("aws", "region")
AWS_ACCESS_KEY_ID = config.get("aws", "access")
AWS_SECRET_ACCESS_KEY = config.get("aws", "secret")
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
DEFAULT_FILE_STORAGE = "storage.MediaS3BotoStorage"
MEDIAFILES_LOCATION = "media"

# Redis Config
REDIS_URL = config.get("redis", "url")
REDIS_SSL = REDIS_URL and "rediss" in REDIS_URL

if REDIS_SSL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {"ssl_cert_reqs": False},
            },
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }

# Celery Configuration
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["application/json"]

if REDIS_SSL:
    redis_url = config.get("redis", "url")
    broker_url = (
        f"{redis_url}?ssl_cert_reqs={ssl.CERT_NONE.name}&ssl_ca_certs={certifi.where()}"
    )
    CELERY_BROKER_URL = broker_url
else:
    CELERY_BROKER_URL = REDIS_URL

# Sendgrid
SENDGRID_API_KEY = config.get("sendgrid", "key")
SEND_EMAIL_ENDPOINT = config.get("sendgrid", "endpoint")
SENDGRID_VERIFICATION_TEMPLATE_ID = config.get("sendgrid", "verification_template_id")
SENDGRID_NEW_SIGNUP_TEMPLATE_ID = config.get("sendgrid", "new_signup_template_id")
SENDGRID_WORKSPACE_INVITATION_TEMPLATE_ID = config.get(
    "sendgrid", "workspace_invitation_template_id"
)
SENDGRID_ANALYTICS_EXPORT_TEMPLATE_ID = config.get(
    "sendgrid", "analytics_export_template_id"
)
SENDGRID_FROM_EMAIL = config.get("sendgrid", "from_email")

# Twilio
TWILIO_ACCOUNT_SID = config.get("twilio", "account_sid")
TWILIO_AUTH_TOKEN = config.get("twilio", "auth_token")
TWILLIO_VERIFY_SERVICE_ID = config.get("twilio", "verify_service_id")
TWILIO_NUMBER = config.get("twilio", "from_number")

# OpenAI
OPENAI_API_KEY = config.get("openai", "api_key")
OPENAI_MODEL_ID = config.get("openai", "model_id")
OPENAI_ORGANIZATION_ID = config.get("openai", "organization_id")
OPENAI_MAX_TOKENS = int(config.get("openai", "max_tokens"))

# URLs
FRONTEND_URL = config.get("main", "frontend_url")
BACKEND_URL = config.get("main", "backend_url")

# User Model
AUTH_USER_MODEL = "iam.User"

"""Integration"""
# google
GOOGLE_OAUTH2_CLIENT_ID = config.get("google", "client_id")
GOOGLE_OAUTH2_CLIENT_SECRET = config.get("google", "client_secret")
GOOGLE_OAUTH2_SSO_CLIENT_ID = config.get("google", "sso_client_id")
GOOGLE_OAUTH2_SSO_CLIENT_SECRET = config.get("google", "sso_client_secret")
GOOGLE_PROJECT_ID = config.get("google", "project_id")
GOOGLE_OAUTH2_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
    "email",
    "profile",
]
GOOGLE_PUB_SUB_TOPIC = config.get("google", "pub_sub_topic")
GOOGLE_PUB_SUB_SUBSCRIPTION = config.get("google", "pub_sub_subscription")
GOOGLE_APPLICATION_CREDENTIALS = BASE_DIR / "config/servcy-gcp-service-account-key.json"
GOOGLE_OAUTH2_REDIRECT_URI = f"{FRONTEND_URL}/{config.get('google', 'redirect_uri')}"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(GOOGLE_APPLICATION_CREDENTIALS)
# microsoft
MICROSOFT_APP_NAME = config.get("microsoft", "display_name")
MICROSOFT_APP_CLIENT_ID = config.get("microsoft", "client_id")
MICROSOFT_APP_CLIENT_SECRET_ID = config.get("microsoft", "client_secret_id")
MICROSOFT_APP_CLIENT_SECRET = config.get("microsoft", "client_secret")
MICROSOFT_APP_OBJECT_ID = config.get("microsoft", "object_id")
MICROSOFT_APP_TENANT_ID = config.get("microsoft", "tenant_id")
MICROSOFT_APP_REDIRECT_URI = f"{FRONTEND_URL}/{config.get('microsoft', 'redirect_uri')}"
# Notion
NOTION_APP_CLIENT_ID = config.get("notion", "client_id")
NOTION_APP_CLIENT_SECRET = config.get("notion", "client_secret")
NOTION_APP_REDIRECT_URI = f"{FRONTEND_URL}/{config.get('notion', 'redirect_uri')}"
# Slack
SLACK_APP_CLIENT_ID = config.get("slack", "client_id")
SLACK_APP_TOKEN = config.get("slack", "app_token")
SLACK_APP_CLIENT_SECRET = config.get("slack", "client_secret")
SLACK_APP_VERIFICATION_TOKEN = config.get("slack", "verification_token")
SLACK_APP_REDIRECT_URI = f"{FRONTEND_URL}/{config.get('slack', 'redirect_uri')}"
# Github
GITHUB_APP_CLIENT_ID = config.get("github", "client_id")
GITHUB_APP_CLIENT_SECRET = config.get("github", "client_secret")
GITHUB_WEBHOOK_SECRET = config.get("github", "webhook_secret")
GITHUB_APP_REDIRECT_URI = f"{FRONTEND_URL}/{config.get('github', 'redirect_uri')}"
# Figma
FIGMA_APP_CLIENT_ID = config.get("figma", "client_id")
FIGMA_APP_CLIENT_SECRET = config.get("figma", "client_secret")
FIGMA_APP_REDIRECT_URI = f"{FRONTEND_URL}/{config.get('figma', 'redirect_uri')}"
# Asana
ASANA_APP_CLIENT_ID = config.get("asana", "client_id")
ASANA_APP_CLIENT_SECRET = config.get("asana", "client_secret")
ASANA_APP_REDIRECT_URI = f"{FRONTEND_URL}/{config.get('asana', 'redirect_uri')}"
# Trello
TRELLO_APP_KEY = config.get("trello", "app_key")
TRELLO_APP_CLIENT_SECRET = config.get("trello", "client_secret")
TRELLO_APP_REDIRECT_URI = f"{FRONTEND_URL}/{config.get('trello', 'redirect_uri')}"
# Jira
JIRA_APP_CLIENT_ID = config.get("jira", "client_id")
JIRA_APP_ID = config.get("jira", "app_id")
JIRA_APP_CLIENT_SECRET = config.get("jira", "client_secret")
JIRA_APP_REDIRECT_URI = f"{FRONTEND_URL}/{config.get('jira', 'redirect_uri')}"

# Cron Jobs
CRONJOBS = [
    (
        "0 0 * * *",
        "integration.services.audit.main",
    ),
    (
        "0 * * * *",
        "integration.scripts.notion.poll_new_comments",
    ),
    (
        "*/5 * * * *",
        "notification.scripts.stack_email_notification.main",
    ),
    (
        "*/5 * * * *",
        "iam.scripts.remove_stale_otps",
    ),
]

# paddle
PADDLE_SECRET_KEY = config.get("paddle", "secret_key")
PADDLE_WEBHOOK_SECRET = config.get("paddle", "webhook_secret")
PADDLE_PLUS_PRICE_ID = config.get("paddle", "plus_price_id")

# Unsplash
UNSPLASH_ACCESS_KEY = config.get("unsplash", "access_key")
UNSPLASH_APP_ID = config.get("unsplash", "app_id")
UNSPLASH_SECRET_KEY = config.get("unsplash", "secret_key")
