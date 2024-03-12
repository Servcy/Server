from django.urls import path

from project.views import (
    ProjectDeployBoardViewSet,
    ProjectFavoritesViewSet,
    ProjectIdentifierEndpoint,
    ProjectInvitationsViewset,
    ProjectJoinEndpoint,
    ProjectMemberUserEndpoint,
    ProjectMemberViewSet,
    ProjectPublicCoverImagesEndpoint,
    ProjectUserViewsEndpoint,
    UserProfileProjectsStatisticsEndpoint,
    ProjectViewSet,
    UserProjectInvitationsViewset,
    UserProjectRolesEndpoint,
)

urlpatterns = [
    path(
        "workspaces/<str:slug>/projects/",
        ProjectViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:pk>/",
        ProjectViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project",
    ),
    path(
        "workspaces/<str:slug>/project-identifiers/",
        ProjectIdentifierEndpoint.as_view(),
        name="project-identifiers",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/invitations/",
        ProjectInvitationsViewset.as_view(
            {
                "get": "list",
                "post": "create",
            },
        ),
        name="project-member-invite",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/invitations/<int:pk>/",
        ProjectInvitationsViewset.as_view(
            {
                "get": "retrieve",
                "delete": "destroy",
            }
        ),
        name="project-member-invite",
    ),
    path(
        "users/me/workspaces/<str:slug>/projects/invitations/",
        UserProjectInvitationsViewset.as_view(
            {
                "get": "list",
                "post": "create",
            },
        ),
        name="user-project-invitations",
    ),
    path(
        "users/me/workspaces/<str:slug>/project-roles/",
        UserProjectRolesEndpoint.as_view(),
        name="user-project-roles",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/join/<int:pk>/",
        ProjectJoinEndpoint.as_view(),
        name="project-join",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/members/",
        ProjectMemberViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-member",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/members/<int:pk>/",
        ProjectMemberViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-member",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/members/leave/",
        ProjectMemberViewSet.as_view(
            {
                "post": "leave",
            }
        ),
        name="project-member",
    ),
    path(
        "workspaces/<str:slug>/user-project-stats/<int:user_id>/",
        UserProfileProjectsStatisticsEndpoint.as_view(),
        name="workspace-user-profile-page",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/project-views/",
        ProjectUserViewsEndpoint.as_view(),
        name="project-view",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/project-members/me/",
        ProjectMemberUserEndpoint.as_view(),
        name="project-member-view",
    ),
    path(
        "workspaces/<str:slug>/user-favorite-projects/",
        ProjectFavoritesViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-favorite",
    ),
    path(
        "workspaces/<str:slug>/user-favorite-projects/<int:project_id>/",
        ProjectFavoritesViewSet.as_view(
            {
                "delete": "destroy",
            }
        ),
        name="project-favorite",
    ),
    path(
        "project-covers/",
        ProjectPublicCoverImagesEndpoint.as_view(),
        name="project-covers",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/project-deploy-boards/",
        ProjectDeployBoardViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-deploy-board",
    ),
    path(
        "workspaces/<str:slug>/projects/<int:project_id>/project-deploy-boards/<int:pk>/",
        ProjectDeployBoardViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-deploy-board",
    ),
]
