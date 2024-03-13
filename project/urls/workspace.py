from django.urls import path

from project.views import (
    UserActivityEndpoint,
    UserActivityGraphEndpoint,
    UserIssueCompletedGraphEndpoint,
    UserProfileProjectsStatisticsEndpoint,
    UserWorkspaceDashboardEndpoint,
    UserWorkSpacesEndpoint,
    WorkspaceCyclesEndpoint,
    WorkspaceEstimatesEndpoint,
    WorkspaceLabelsEndpoint,
    WorkspaceModulesEndpoint,
    WorkspaceStatesEndpoint,
    WorkspaceUserActivityEndpoint,
    WorkspaceUserProfileIssuesEndpoint,
    WorkspaceUserProfileStatsEndpoint,
)

urlpatterns = [
    path(
        "workspace/<str:slug>/user-stats/<int:user_id>/",
        WorkspaceUserProfileStatsEndpoint.as_view(),
        name="workspace-user-stats",
    ),
    path(
        "workspace/<str:slug>/user-activity/<int:user_id>/",
        WorkspaceUserActivityEndpoint.as_view(),
        name="workspace-user-activity",
    ),
    path(
        "workspace/<str:slug>/user-issues/<int:user_id>/",
        WorkspaceUserProfileIssuesEndpoint.as_view(),
        name="workspace-user-profile-issues",
    ),
    path(
        "workspace/<str:slug>/labels/",
        WorkspaceLabelsEndpoint.as_view(),
        name="workspace-labels",
    ),
    path(
        "workspace/<str:slug>/states/",
        WorkspaceStatesEndpoint.as_view(),
        name="workspace-state",
    ),
    path(
        "workspace/<str:slug>/estimates/",
        WorkspaceEstimatesEndpoint.as_view(),
        name="workspace-estimate",
    ),
    path(
        "workspace/<str:slug>/modules/",
        WorkspaceModulesEndpoint.as_view(),
        name="workspace-modules",
    ),
    path(
        "workspace/<str:slug>/cycles/",
        WorkspaceCyclesEndpoint.as_view(),
        name="workspace-cycles",
    ),
    path(
        "me/activities/",
        UserActivityEndpoint.as_view(),
        name="user-activities",
    ),
    path(
        "me/workspaces",
        UserWorkSpacesEndpoint.as_view(),
        name="user-workspace",
    ),
    path(
        "me/workspace/<str:slug>/activity-graph/",
        UserActivityGraphEndpoint.as_view(),
        name="user-activity-graph",
    ),
    path(
        "me/workspace/<str:slug>/issues-completed-graph/",
        UserIssueCompletedGraphEndpoint.as_view(),
        name="completed-graph",
    ),
    path(
        "workspace/<str:slug>/user-project-stats/<int:user_id>/",
        UserProfileProjectsStatisticsEndpoint.as_view(),
        name="workspace-user-profile-page",
    ),
    path(
        "me/workspace/<str:slug>/dashboard/",
        UserWorkspaceDashboardEndpoint.as_view(),
        name="user-workspace-dashboard",
    ),
]
