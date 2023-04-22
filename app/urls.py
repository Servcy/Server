from django.conf import settings
from django.contrib import admin
from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .apis.auth import Authentication

urlpatterns = [
    path("admin", admin.site.urls),
    path("authentication", Authentication.as_view(), name="AuAuthentication Manager"),
]

if settings.DEBUG:
    urlpatterns.extend(
        [
            path("swagger/schema/", SpectacularAPIView.as_view(), name="schema"),
            path(
                "swagger",
                SpectacularSwaggerView.as_view(),
                name="swagger-ui",
            ),
            path(
                "swagger/schema/redoc",
                SpectacularRedocView.as_view(),
                name="redoc",
            ),
        ]
    )
