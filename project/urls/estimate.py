from django.urls import path

from project.views import BulkEstimatePointEndpoint, ProjectEstimatePointEndpoint

urlpatterns = [
    path(
        "<str:workspace_slug>/<int:project_id>/project-estimates/",
        ProjectEstimatePointEndpoint.as_view(),
        name="project-estimate-points",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/estimates/",
        BulkEstimatePointEndpoint.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="bulk-create-estimate-points",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/estimates/<int:estimate_id>/",
        BulkEstimatePointEndpoint.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="bulk-create-estimate-points",
    ),
]
