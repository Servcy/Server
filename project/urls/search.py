from django.urls import path

from project.views import GlobalSearchEndpoint, IssueSearchEndpoint

urlpatterns = [
    path(
        "workspace/<str:slug>/search/",
        GlobalSearchEndpoint.as_view(),
        name="global-search",
    ),
    path(
        "workspace/<str:slug>/projects/<int:project_id>/search-issues/",
        IssueSearchEndpoint.as_view(),
        name="project-issue-search",
    ),
]
