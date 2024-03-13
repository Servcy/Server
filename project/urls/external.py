from django.urls import path

from project.views import GPTIntegrationEndpoint

urlpatterns = [
    path(
        "<str:workspace_slug>/<int:project_id>/ai-assistant/",
        GPTIntegrationEndpoint.as_view(),
        name="importer",
    ),
]
