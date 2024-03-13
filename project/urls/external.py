from django.urls import path

from project.views import GPTIntegrationEndpoint

urlpatterns = [
    path(
        "workspace/<str:slug>/projects/<int:project_id>/ai-assistant/",
        GPTIntegrationEndpoint.as_view(),
        name="importer",
    ),
]
