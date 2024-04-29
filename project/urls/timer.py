from django.urls import path

from project.views import TrackedTimeAttachmentViewSet, TrackedTimeViewSet

urlpatterns = [
    path(
        "<str:workspace_slug>/timer/<str:view_key>",
        TrackedTimeViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="fetch-timesheet",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/member-wise-time-logged",
        TrackedTimeViewSet.as_view(
            {
                "get": "project_member_wise_time_duration",
            }
        ),
        name="member-wise-time-logged",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/member-wise-estimate",
        TrackedTimeViewSet.as_view(
            {
                "get": "member_wise_estimate",
            }
        ),
        name="member-wise-estimate",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/<int:time_log_id>/delete-time-log",
        TrackedTimeViewSet.as_view(
            {
                "delete": "delete",
            }
        ),
        name="delete-time-log",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/<int:time_log_id>/update-time-log",
        TrackedTimeViewSet.as_view(
            {
                "patch": "update",
            }
        ),
        name="update-time-log",
    ),
    path(
        "<str:workspace_slug>/is-timer-running",
        TrackedTimeViewSet.as_view(
            {
                "get": "is_timer_running",
            }
        ),
        name="is-timer-running",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/<int:issue_id>/start-timer",
        TrackedTimeViewSet.as_view(
            {
                "post": "create",
            }
        ),
        name="start-issue-timer",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/<int:timer_id>/stop-timer",
        TrackedTimeViewSet.as_view(
            {
                "post": "stop_timer",
            }
        ),
        name="stop-issue-timer",
    ),
    path(
        "<int:tracked_time_id>/tracked-time-snapshot",
        TrackedTimeAttachmentViewSet.as_view(
            {
                "get": "get",
                "post": "post",
            }
        ),
        name="tracked-time-snapshot",
    ),
    path(
        "<int:tracked_time_id>/tracked-time-snapshot/<int:pk>",
        TrackedTimeAttachmentViewSet.as_view(
            {
                "delete": "delete",
            }
        ),
        name="tracked-time-snapshot-delete",
    ),
]
