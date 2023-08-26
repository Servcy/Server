from django.urls import path

from webhook.google import google
from webhook.microsoft import microsoft
from webhook.slack import slack

urlpatterns = [
    path("microsoft", microsoft, name="Microsoft Webhook"),
    path("google", google, name="Google Webhook"),
    path("slack", slack, name="Slack Webhook"),
]
