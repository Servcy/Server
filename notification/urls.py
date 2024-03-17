from django.urls import include, path
from rest_framework import routers

from notification.views import (
    MarkAllReadNotificationViewSet,
    NotificationViewSet,
    UnreadNotificationEndpoint,
    UserNotificationPreferenceEndpoint,
)

router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "preferences",
        UserNotificationPreferenceEndpoint.as_view(),
        name="user-notification-preferences",
    ),
    path(
        "<str:workspace_slug>",
        NotificationViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="notifications",
    ),
    path(
        "<str:workspace_slug>/<int:pk>",
        NotificationViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="notifications",
    ),
    path(
        "<str:workspace_slug>/<int:pk>/read",
        NotificationViewSet.as_view(
            {
                "post": "mark_read",
                "delete": "mark_unread",
            }
        ),
        name="notifications",
    ),
    path(
        "<str:workspace_slug>/<int:pk>/archive",
        NotificationViewSet.as_view(
            {
                "post": "archive",
                "delete": "unarchive",
            }
        ),
        name="notifications",
    ),
    path(
        "<str:workspace_slug>/unread",
        UnreadNotificationEndpoint.as_view(),
        name="unread-notifications",
    ),
    path(
        "<str:workspace_slug>/read",
        MarkAllReadNotificationViewSet.as_view(
            {
                "post": "create",
            }
        ),
        name="mark-all-read-notifications",
    ),
]
