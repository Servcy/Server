from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from app.views.auth import Authentication
from app.views.logout import LogoutView

urlpatterns = [
    path("authentication", Authentication.as_view(), name="Authentication Manager"),
    path("refresh-token", TokenRefreshView.as_view(), name="Refresh Token"),
    path("logout", LogoutView.as_view(), name="Auth Logout"),
    path("integration/", include("integration.urls")),
]
