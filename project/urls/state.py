from django.urls import path

from project.views import StateViewSet

urlpatterns = [
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/states/",
        StateViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-states",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/states/<int:pk>/",
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
        "workspaces/<str:slug>/projects/<int:project_id>/states/<int:pk>/mark-default/",
        StateViewSet.as_view(
            {
                "post": "mark_as_default",
            }
        ),
        name="project-state",
    ),
]
