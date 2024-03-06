from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from app.views.auth import AuthenticationView
from app.views.logout import LogoutView

urlpatterns = [
    path("authentication", AuthenticationView.as_view(), name="Authentication View"),
    path("refresh-token", TokenRefreshView.as_view(), name="Refresh Token"),
    path("logout", LogoutView.as_view(), name="Logout View"),
    path("integration/", include("integration.urls")),
    path("inbox/", include("inbox.urls")),
    path("webhook/", include("webhook.urls")),
    path("document/", include("document.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("project/", include("project.urls")),
    path("notification/", include("notification.urls")),
]
