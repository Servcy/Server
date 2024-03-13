from django.urls import path

from iam.views import (
    UpdateUserOnBoardedEndpoint,
    UpdateUserTourCompletedEndpoint,
    UserEndpoint,
    UserLastProjectWithWorkspaceEndpoint,
    UserWorkspaceInvitationsViewSet,
    WorkSpaceAvailabilityCheckEndpoint,
    WorkspaceInvitationsViewset,
    WorkspaceJoinEndpoint,
    WorkspaceMemberUserEndpoint,
    WorkspaceMemberUserViewsEndpoint,
    WorkSpaceMemberViewSet,
    WorkSpaceViewSet,
)


urlpatterns = [
    path(
        "me",
        UserEndpoint.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "deactivate",
            }
        ),
        name="users",
    ),
    path(
        "me/settings",
        UserEndpoint.as_view(
            {
                "get": "retrieve_my_settings",
            }
        ),
        name="users",
    ),
    path(
        "me/onboard",
        UpdateUserOnBoardedEndpoint.as_view(),
        name="user-onboard",
    ),
    path(
        "me/tour/completed",
        UpdateUserTourCompletedEndpoint.as_view(),
        name="user-tour",
    ),
    path(
        "me/last/visited/workspace/project",
        UserLastProjectWithWorkspaceEndpoint.as_view(),
        name="workspace-project-details",
    ),
    path(
        "workspace/slug/check",
        WorkSpaceAvailabilityCheckEndpoint.as_view(),
        name="workspace-availability",
    ),
    path(
        "workspaces",
        WorkSpaceViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="workspace",
    ),
    path(
        "workspace/<str:slug>",
        WorkSpaceViewSet.as_view(
            {
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="workspace",
    ),
    path(
        "workspace/<str:slug>/invitations",
        WorkspaceInvitationsViewset.as_view(
            {
                "get": "list",
                "post": "create",
            },
        ),
        name="workspace-invitations",
    ),
    path(
        "workspace/<str:slug>/invitations/<int:pk>",
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
        "me/workspace/invitations",
        UserWorkspaceInvitationsViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            },
        ),
        name="user-workspace-invitations",
    ),
    path(
        "workspace/<str:slug>/invitations/<int:pk>/join",
        WorkspaceJoinEndpoint.as_view(),
        name="workspace-join",
    ),
    path(
        "workspace/<str:slug>/members",
        WorkSpaceMemberViewSet.as_view({"get": "list"}),
        name="workspace-member",
    ),
    path(
        "workspace/<str:slug>/members/<int:pk>",
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
        "workspace/<str:slug>/members/leave",
        WorkSpaceMemberViewSet.as_view(
            {
                "post": "leave",
            },
        ),
        name="leave-workspace-members",
    ),
    path(
        "workspace/<str:slug>/members/me",
        WorkspaceMemberUserEndpoint.as_view(),
        name="workspace-member-details",
    ),
    path(
        "workspace/<str:slug>/views",
        WorkspaceMemberUserViewsEndpoint.as_view(),
        name="workspace-member-views-details",
    ),
]
