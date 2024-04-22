from django.urls import path

from project.views import TrackedTimeAttachmentViewSet, TrackedTimeViewSet

urlpatterns = [
    path(
        "<str:workspace_slug>/timer",
        TrackedTimeViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="fetch-timesheet",
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
        "<str:workspace_slug>/<int:project_id>/<int:issue_id>/time-slot-attachment",
        TrackedTimeAttachmentViewSet.as_view(
            {
                "get": "retrieve",
                "post": "create",
                "delete": "destroy",
            }
        ),
        name="time-slot-attachment",
    ),
]
