from django.urls import include, path
from rest_framework import routers

from iam.views import (
    UserLastProjectWithWorkspaceEndpoint,
    UserWorkspaceInvitationsViewSet,
    WorkspaceCyclesEndpoint,
    WorkspaceEstimatesEndpoint,
    WorkspaceInvitationsViewset,
    WorkspaceJoinEndpoint,
    WorkspaceLabelsEndpoint,
    WorkspaceMemberUserEndpoint,
    WorkspaceMemberUserViewsEndpoint,
    WorkSpaceMemberViewSet,
    WorkspaceModulesEndpoint,
    WorkspaceProjectMemberEndpoint,
    WorkspaceStatesEndpoint,
    WorkspaceThemeViewSet,
    WorkspaceUserActivityEndpoint,
    WorkspaceUserProfileEndpoint,
    WorkspaceUserProfileIssuesEndpoint,
    WorkspaceUserProfileStatsEndpoint,
    WorkspaceUserPropertiesEndpoint,
    WorkSpaceViewSet,
)

router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "workspaces/",
        WorkSpaceViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="workspace",
    ),
    path(
        "workspaces/<int:workspace_id>/",
        WorkSpaceViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="workspace",
    ),
    path(
        "workspaces/<int:workspace_id>/invitations/",
        WorkspaceInvitationsViewset.as_view(
            {
                "get": "list",
                "post": "create",
            },
        ),
        name="workspace-invitations",
    ),
    path(
        "workspaces/<int:workspace_id>/invitations/<int:pk>/",
        WorkspaceInvitationsViewset.as_view(
            {
                "delete": "destroy",
                "get": "retrieve",
                "patch": "partial_update",
            }
        ),
        name="workspace-invitations",
    ),
    path(
        "users/me/workspaces/invitations/",
        UserWorkspaceInvitationsViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            },
        ),
        name="user-workspace-invitations",
    ),
    path(
        "workspaces/<int:workspace_id>/invitations/<int:pk>/join/",
        WorkspaceJoinEndpoint.as_view(),
        name="workspace-join",
    ),
    path(
        "workspaces/<int:workspace_id>/members/",
        WorkSpaceMemberViewSet.as_view({"get": "list"}),
        name="workspace-member",
    ),
    path(
        "workspaces/<int:workspace_id>/project-members/",
        WorkspaceProjectMemberEndpoint.as_view(),
        name="workspace-member-roles",
    ),
    path(
        "workspaces/<int:workspace_id>/members/<int:pk>/",
        WorkSpaceMemberViewSet.as_view(
            {
                "patch": "partial_update",
                "delete": "destroy",
                "get": "retrieve",
            }
        ),
        name="workspace-member",
    ),
    path(
        "workspaces/<int:workspace_id>/members/leave/",
        WorkSpaceMemberViewSet.as_view(
            {
                "post": "leave",
            },
        ),
        name="leave-workspace-members",
    ),
    path(
        "users/last-visited-workspace/",
        UserLastProjectWithWorkspaceEndpoint.as_view(),
        name="workspace-project-details",
    ),
    path(
        "workspaces/<int:workspace_id>/workspace-members/me/",
        WorkspaceMemberUserEndpoint.as_view(),
        name="workspace-member-details",
    ),
    path(
        "workspaces/<int:workspace_id>/workspace-views/",
        WorkspaceMemberUserViewsEndpoint.as_view(),
        name="workspace-member-views-details",
    ),
    path(
        "workspaces/<int:workspace_id>/workspace-themes/",
        WorkspaceThemeViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="workspace-themes",
    ),
    path(
        "workspaces/<int:workspace_id>/workspace-themes/<int:pk>/",
        WorkspaceThemeViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="workspace-themes",
    ),
    path(
        "workspaces/<int:workspace_id>/user-stats/<int:user_id>/",
        WorkspaceUserProfileStatsEndpoint.as_view(),
        name="workspace-user-stats",
    ),
    path(
        "workspaces/<int:workspace_id>/user-activity/<int:user_id>/",
        WorkspaceUserActivityEndpoint.as_view(),
        name="workspace-user-activity",
    ),
    path(
        "workspaces/<int:workspace_id>/user-profile/<int:user_id>/",
        WorkspaceUserProfileEndpoint.as_view(),
        name="workspace-user-profile-page",
    ),
    path(
        "workspaces/<int:workspace_id>/user-issues/<int:user_id>/",
        WorkspaceUserProfileIssuesEndpoint.as_view(),
        name="workspace-user-profile-issues",
    ),
    path(
        "workspaces/<int:workspace_id>/labels/",
        WorkspaceLabelsEndpoint.as_view(),
        name="workspace-labels",
    ),
    path(
        "workspaces/<int:workspace_id>/user-properties/",
        WorkspaceUserPropertiesEndpoint.as_view(),
        name="workspace-user-filters",
    ),
    path(
        "workspaces/<int:workspace_id>/states/",
        WorkspaceStatesEndpoint.as_view(),
        name="workspace-state",
    ),
    path(
        "workspaces/<int:workspace_id>/estimates/",
        WorkspaceEstimatesEndpoint.as_view(),
        name="workspace-estimate",
    ),
    path(
        "workspaces/<int:workspace_id>/modules/",
        WorkspaceModulesEndpoint.as_view(),
        name="workspace-modules",
    ),
    path(
        "workspaces/<int:workspace_id>/cycles/",
        WorkspaceCyclesEndpoint.as_view(),
        name="workspace-cycles",
    ),
]
