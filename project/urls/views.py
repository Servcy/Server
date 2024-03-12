from django.urls import path

from project.views import (
    GlobalViewIssuesViewSet,
    GlobalViewViewSet,
    IssueViewFavoriteViewSet,
    IssueViewViewSet,
)

urlpatterns = [
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/views/",
        IssueViewViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-view",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/views/<int:pk>/",
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
        "workspaces/<str:slug>/views/",
        GlobalViewViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="global-view",
    ),
    path(
        "workspaces/<str:slug>/views/<int:pk>/",
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
        "workspaces/<str:slug>/issues/",
        GlobalViewIssuesViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="global-view-issues",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/user-favorite-views/",
        IssueViewFavoriteViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="user-favorite-view",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/user-favorite-views/<int:view_id>/",
        IssueViewFavoriteViewSet.as_view(
            {
                "delete": "destroy",
            }
        ),
        name="user-favorite-view",
    ),
]
