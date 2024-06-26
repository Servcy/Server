from django.urls import path

from project.views import (
    ActiveCycleEndpoint,
    CycleArchiveUnarchiveEndpoint,
    CycleDateCheckEndpoint,
    CycleFavoriteViewSet,
    CycleIssueViewSet,
    CycleUserPropertiesEndpoint,
    CycleViewSet,
    TransferCycleIssueEndpoint,
)

urlpatterns = [
    path(
        "<str:workspace_slug>/active-cycles/",
        ActiveCycleEndpoint.as_view(),
        name="workspace-active-cycle",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/cycles/<int:cycle_id>/archive/",
        CycleArchiveUnarchiveEndpoint.as_view(),
        name="cycle-archive-unarchive",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/archived-cycles/",
        CycleArchiveUnarchiveEndpoint.as_view(),
        name="cycle-archive-unarchive",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/cycles/",
        CycleViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-cycle",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/cycles/<int:pk>/",
        CycleViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-cycle",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/cycles/<int:cycle_id>/cycle-issues/",
        CycleIssueViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-issue-cycle",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/cycles/<int:cycle_id>/cycle-issues/<int:issue_id>/",
        CycleIssueViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-issue-cycle",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/cycles/date-check/",
        CycleDateCheckEndpoint.as_view(),
        name="project-cycle-date",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/user-favorite-cycles/",
        CycleFavoriteViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="user-favorite-cycle",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/user-favorite-cycles/<int:cycle_id>/",
        CycleFavoriteViewSet.as_view(
            {
                "delete": "destroy",
            }
        ),
        name="user-favorite-cycle",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/cycles/<int:cycle_id>/transfer-issues/",
        TransferCycleIssueEndpoint.as_view(),
        name="transfer-issues",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/cycles/<int:cycle_id>/user-properties/",
        CycleUserPropertiesEndpoint.as_view(),
        name="cycle-user-filters",
    ),
]
