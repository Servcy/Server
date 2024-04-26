from django.urls import path

from project.views import ProjectExpenseViewSet

urlpatterns = [
    path(
        "<str:workspace_slug>/<int:project_id>/expense",
        ProjectExpenseViewSet.as_view(
            {
                "get": "list",
                "post": "create",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="importer",
    ),
]
