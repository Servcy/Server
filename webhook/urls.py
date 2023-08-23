from django.urls import path

from webhook.google import google
from webhook.microsoft import microsoft

urlpatterns = [
    path("microsoft", microsoft, name="Microsoft Webhook"),
    path("google", google, name="Google Webhook"),
]
