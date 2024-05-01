from django.urls import path

from billing.views import RazorpayView, WorkspaceSubscriptionView

urlpatterns = [
    path(
        "<slug:workspace_slug>/subscription",
        WorkspaceSubscriptionView.as_view(),
        name="workspace-subscription",
    ),
    path(
        "<slug:workspace_slug>/razorpay",
        RazorpayView.as_view({"post": "post", "delete": "delete"}),
        name="workspace-subscription",
    ),
]
