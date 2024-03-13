from django.urls import path

from project.views import (
    GlobalViewIssuesViewSet,
    GlobalViewViewSet,
    IssueViewFavoriteViewSet,
    IssueViewViewSet,
)

urlpatterns = [
    path(
        "<str:workspace_slug>/<int:project_id>/views/",
        IssueViewViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-view",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/views/<int:pk>/",
        IssueViewViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-view",
    ),
    path(
        "<str:workspace_slug>/views/",
        GlobalViewViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="global-view",
    ),
    path(
        "<str:workspace_slug>/views/<int:pk>/",
        GlobalViewViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="global-view",
    ),
    path(
        "<str:workspace_slug>/issues/",
        GlobalViewIssuesViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="global-view-issues",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/views/favorite/",
        IssueViewFavoriteViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="user-favorite-view",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/views/<int:view_id>/favorite/",
        IssueViewFavoriteViewSet.as_view(
            {
                "delete": "destroy",
            }
        ),
        name="user-favorite-view",
    ),
]
