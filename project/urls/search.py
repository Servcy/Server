from django.urls import path

from project.views import GlobalSearchEndpoint, IssueSearchEndpoint

urlpatterns = [
    path(
        "<str:workspace_slug>/search/",
        GlobalSearchEndpoint.as_view(),
        name="global-search",
    ),
    path(
        "<str:workspace_slug>/projects/<int:project_id>/search-issues/",
        IssueSearchEndpoint.as_view(),
        name="project-issue-search",
    ),
]
