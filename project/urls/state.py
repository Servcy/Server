from django.urls import path

from project.views import StateViewSet

urlpatterns = [
    path(
        "<str:workspace_slug>/<int:project_id>/states",
        StateViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-states",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/states/<int:pk>",
        StateViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-state",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/states/<int:pk>/mark-default",
        StateViewSet.as_view(
            {
                "post": "mark_as_default",
            }
        ),
        name="project-state",
    ),
]
