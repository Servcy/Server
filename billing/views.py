from common.views import BaseAPIView
from billing.models import Subscription
from rest_framework.response import Response
from common.permissions import WorkspaceViewerPermission


class WorkspaceSubscriptionView(BaseAPIView):
    """
    This view will handle the workspace subscriptions
    """

    permission_classes = [WorkspaceViewerPermission]

    def get(self, request, workspace_slug):
        """
        This method will return the workspace subscription details
        """
        subscription = Subscription.objects.filter(
            workspace__slug=workspace_slug, is_active=True
        ).first()
        return (
            Response(subscription.data)
            if subscription
            else Response(
                {
                    "plan_details": {
                        "name": "Starter Plan",
                    },
                    "valid_till": None,
                    "subscription_details": {},
                    "is_active": True,
                    "is_trial": True,
                }
            )
        )
