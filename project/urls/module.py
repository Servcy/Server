from django.urls import path

from project.views import (
    ModuleArchiveUnarchiveEndpoint,
    ModuleFavoriteViewSet,
    ModuleIssueViewSet,
    ModuleLinkViewSet,
    ModuleUserPropertiesEndpoint,
    ModuleViewSet,
)

urlpatterns = [
    path(
        "<str:workspace_slug>/<int:project_id>/modules/",
        ModuleViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-modules",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/modules/<int:pk>/",
        ModuleViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-modules",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:issue_id>/modules/",
        ModuleIssueViewSet.as_view(
            {
                "post": "create_issue_modules",
            }
        ),
        name="issue-module",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/modules/<int:module_id>/issues/",
        ModuleIssueViewSet.as_view(
            {
                "post": "create_module_issues",
                "get": "list",
            }
        ),
        name="project-module-issues",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/modules/<int:module_id>/issues/<int:issue_id>/",
        ModuleIssueViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-module-issues",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/modules/<int:module_id>/links/",
        ModuleLinkViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-issue-module-links",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/modules/<int:module_id>/links/<int:pk>/",
        ModuleLinkViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-issue-module-links",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/modules/favorite/",
        ModuleFavoriteViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="user-favorite-module",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/modules/<int:module_id>/favorite/",
        ModuleFavoriteViewSet.as_view(
            {
                "delete": "destroy",
            }
        ),
        name="user-favorite-module",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/modules/<int:module_id>/user-properties/",
        ModuleUserPropertiesEndpoint.as_view(),
        name="cycle-user-filters",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/modules/<int:module_id>/archive/",
        ModuleArchiveUnarchiveEndpoint.as_view(),
        name="module-archive-unarchive",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/archived-modules/",
        ModuleArchiveUnarchiveEndpoint.as_view(),
        name="module-archive-unarchive",
    ),
]
