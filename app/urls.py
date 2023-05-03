from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .apis.auth import Authentication
from .apis.logout import LogoutView

urlpatterns = [
    path("authentication", Authentication.as_view(), name="AuAuthentication Manager"),
    path("refresh-token", TokenRefreshView.as_view(), name="Refresh Token"),
    path("logout", LogoutView.as_view(), name="Auth Logout"),
]
