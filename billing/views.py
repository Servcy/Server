from rest_framework.response import Response

from billing.models import Subscription
from billing.serializers import SubscriptionSerializer
from common.permissions import WorkspaceViewerPermission
from common.views import BaseAPIView


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
            Response(SubscriptionSerializer(subscription).data)
            if subscription
            else Response(
                {
                    "plan_details": {
                        "name": "Starter Plan",
                    },
                    "limits": {
                        "invitations": 5,
                    },
                    "valid_till": None,
                    "subscription_details": {},
                    "is_active": True,
                    "is_trial": True,
                }
            )
        )
