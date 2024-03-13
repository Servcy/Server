from django.urls import path

from project.views import (
    PageFavoriteViewSet,
    PageLogEndpoint,
    PageViewSet,
    SubPagesEndpoint,
)

urlpatterns = [
    path(
        "workspace/<str:slug>/projects/<int:project_id>/pages/",
        PageViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-pages",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/pages/<int:pk>/",
        PageViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-pages",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/user-favorite-pages/",
        PageFavoriteViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="user-favorite-pages",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/user-favorite-pages/<int:page_id>/",
        PageFavoriteViewSet.as_view(
            {
                "delete": "destroy",
            }
        ),
        name="user-favorite-pages",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/pages/",
        PageViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-pages",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/pages/<int:pk>/",
        PageViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-pages",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/pages/<int:page_id>/archive/",
        PageViewSet.as_view(
            {
                "post": "archive",
            }
        ),
        name="project-page-archive",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/pages/<int:page_id>/unarchive/",
        PageViewSet.as_view(
            {
                "post": "unarchive",
            }
        ),
        name="project-page-unarchive",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/archived-pages/",
        PageViewSet.as_view(
            {
                "get": "archive_list",
            }
        ),
        name="project-pages",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/pages/<int:page_id>/lock/",
        PageViewSet.as_view(
            {
                "post": "lock",
            }
        ),
        name="project-pages",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/pages/<int:page_id>/unlock/",
        PageViewSet.as_view(
            {
                "post": "unlock",
            }
        ),
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/pages/<int:page_id>/transactions/",
        PageLogEndpoint.as_view(),
        name="page-transactions",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/pages/<int:page_id>/transactions/<int:transaction>/",
        PageLogEndpoint.as_view(),
        name="page-transactions",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/pages/<int:page_id>/sub-pages/",
        SubPagesEndpoint.as_view(),
        name="sub-page",
    ),
]
