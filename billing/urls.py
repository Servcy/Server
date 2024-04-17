from django.urls import path

from billing.views import WorkspaceSubscriptionView, RazorpayView

urlpatterns = [
    path(
        "<slug:workspace_slug>/subscription",
        WorkspaceSubscriptionView.as_view(),
        name="workspace-subscription",
    ),
    path(
        "<slug:workspace_slug>/razorpay",
        RazorpayView.as_view({"post": "post", "get": "get", "patch": "patch"}),
        name="workspace-subscription",
    ),
]
