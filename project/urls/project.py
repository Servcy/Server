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
        "workspace/<str:slug>/projects/",
        ProjectViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project",
    ),
    path(
        "workspace/<str:slug>/projects/<int:pk>/",
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
        "workspace/<str:slug>/project-identifiers/",
        ProjectIdentifierEndpoint.as_view(),
        name="project-identifiers",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/invitations/",
        ProjectInvitationsViewset.as_view(
            {
                "get": "list",
                "post": "create",
            },
        ),
        name="project-member-invite",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/invitations/<int:pk>/",
        ProjectInvitationsViewset.as_view(
            {
                "get": "retrieve",
                "delete": "destroy",
            }
        ),
        name="project-member-invite",
    ),
    path(
        "users/me/workspace/<str:slug>/projects/invitations/",
        UserProjectInvitationsViewset.as_view(
            {
                "get": "list",
                "post": "create",
            },
        ),
        name="user-project-invitations",
    ),
    path(
        "users/me/workspace/<str:slug>/project-roles/",
        UserProjectRolesEndpoint.as_view(),
        name="user-project-roles",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/join/<int:pk>/",
        ProjectJoinEndpoint.as_view(),
        name="project-join",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/members/",
        ProjectMemberViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-member",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/members/<int:pk>/",
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
        "workspace/<str:slug>/projects/<int:project_id>/members/leave/",
        ProjectMemberViewSet.as_view(
            {
                "post": "leave",
            }
        ),
        name="project-member",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/project-views/",
        ProjectUserViewsEndpoint.as_view(),
        name="project-view",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/project-members/me/",
        ProjectMemberUserEndpoint.as_view(),
        name="project-member-view",
    ),
    path(
        "workspace/<str:slug>/user-favorite-projects/",
        ProjectFavoritesViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-favorite",
    ),
    path(
        "workspace/<str:slug>/user-favorite-projects/<int:project_id>/",
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
        "workspace/<str:slug>/projects/<int:project_id>/project-deploy-boards/",
        ProjectDeployBoardViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-deploy-board",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/project-deploy-boards/<int:pk>/",
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
