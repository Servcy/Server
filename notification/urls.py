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
        "users/me/notification-preferences/",
        UserNotificationPreferenceEndpoint.as_view(),
        name="user-notification-preferences",
    ),
    path(
        "workspace/<str:slug>/users/notifications/",
        NotificationViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="notifications",
    ),
    path(
        "workspace/<str:slug>/users/notifications/<int:pk>/",
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
        "workspace/<str:slug>/users/notifications/<int:pk>/read/",
        NotificationViewSet.as_view(
            {
                "post": "mark_read",
                "delete": "mark_unread",
            }
        ),
        name="notifications",
    ),
    path(
        "workspace/<str:slug>/users/notifications/<int:pk>/archive/",
        NotificationViewSet.as_view(
            {
                "post": "archive",
                "delete": "unarchive",
            }
        ),
        name="notifications",
    ),
    path(
        "workspace/<str:slug>/unread/",
        UnreadNotificationEndpoint.as_view(),
        name="unread-notifications",
    ),
    path(
        "workspace/<str:slug>/users/notifications/mark-all-read/",
        MarkAllReadNotificationViewSet.as_view(
            {
                "post": "create",
            }
        ),
        name="mark-all-read-notifications",
    ),
]
