from django.conf import settings
from django.contrib import admin
from django.urls import path

from .apis.auth import Authentication

urlpatterns = [
    path("admin", admin.site.urls),
    path("authentication", Authentication.as_view(), name="AuAuthentication Manager"),
]
