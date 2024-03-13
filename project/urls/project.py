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
    ProjectViewSet,
    UserProjectInvitationsViewset,
    UserProjectRolesEndpoint,
)

urlpatterns = [
    path(
        "<str:workspace_slug>/projects/",
        ProjectViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project",
    ),
    path(
        "<str:workspace_slug>/<int:pk>/",
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
        "<str:workspace_slug>/project-identifiers/",
        ProjectIdentifierEndpoint.as_view(),
        name="project-identifiers",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/invitations/",
        ProjectInvitationsViewset.as_view(
            {
                "get": "list",
                "post": "create",
            },
        ),
        name="project-member-invite",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/invitations/<int:pk>/",
        ProjectInvitationsViewset.as_view(
            {
                "get": "retrieve",
                "delete": "destroy",
            }
        ),
        name="project-member-invite",
    ),
    path(
        "me/<str:workspace_slug>/invitations/",
        UserProjectInvitationsViewset.as_view(
            {
                "get": "list",
                "post": "create",
            },
        ),
        name="user-project-invitations",
    ),
    path(
        "me/<str:workspace_slug>/project-roles/",
        UserProjectRolesEndpoint.as_view(),
        name="user-project-roles",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/join/<int:pk>/",
        ProjectJoinEndpoint.as_view(),
        name="project-join",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/members/",
        ProjectMemberViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-member",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/members/<int:pk>/",
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
        "<str:workspace_slug>/<int:project_id>/members/leave/",
        ProjectMemberViewSet.as_view(
            {
                "post": "leave",
            }
        ),
        name="project-member",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/project-views/",
        ProjectUserViewsEndpoint.as_view(),
        name="project-view",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/project-members/me/",
        ProjectMemberUserEndpoint.as_view(),
        name="project-member-view",
    ),
    path(
        "<str:workspace_slug>/user-favorite-projects/",
        ProjectFavoritesViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-favorite",
    ),
    path(
        "<str:workspace_slug>/user-favorite-projects/<int:project_id>/",
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
        "<str:workspace_slug>/<int:project_id>/project-deploy-boards/",
        ProjectDeployBoardViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-deploy-board",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/project-deploy-boards/<int:pk>/",
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
