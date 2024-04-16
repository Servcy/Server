from django.urls import path

from billing.views import WorkspaceSubscriptionView

urlpatterns = [
    path(
        "<slug:workspace_slug>/subscription",
        WorkspaceSubscriptionView.as_view(),
        name="workspace-subscription",
    ),
]
