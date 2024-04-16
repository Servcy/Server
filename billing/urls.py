from billing.views import WorkspaceSubscriptionView
from django.urls import path

urlpatterns = [
    path(
        "<slug:workspace_slug>/subscription",
        WorkspaceSubscriptionView.as_view(),
        name="workspace-subscription",
    ),
]
