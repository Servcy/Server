from django.conf import settings
from paddle_billing import Client
from paddle_billing.Resources.Subscriptions.Operations import PauseSubscription
from rest_framework.response import Response

from billing.models import Subscription
from billing.serializers import SubscriptionSerializer
from common.billing import PLAN_LIMITS
from common.permissions import WorkspaceUserPermission
from common.views import BaseAPIView


class WorkspaceSubscriptionView(BaseAPIView):
    """
    This view will handle the workspace subscriptions
    """

    permission_classes = [WorkspaceUserPermission]

    def get(self, request, workspace_slug):
        """
        This method will return the workspace subscription details
        """
        if request.user.is_superuser:
            return Response(
                {
                    "plan_details": {
                        "name": "Business",
                    },
                    "limits": PLAN_LIMITS["business"],
                    "subscription_id": None,
                    "is_active": True,
                }
            )
        subscription = Subscription.objects.filter(
            workspace__slug=workspace_slug, is_active=True
        ).first()
        if subscription:
            return Response(SubscriptionSerializer(subscription).data)
        return Response(
            {
                "plan_details": {
                    "name": "Starter",
                },
                "limits": PLAN_LIMITS["starter"],
                "subscription_id": None,
                "is_active": True,
            }
        )

    def delete(self, request, workspace_slug):
        """
        This method will cancel the workspace subscription
        """
        paddle = Client(settings.PADDLE_SECRET_KEY)
        subscription = Subscription.objects.filter(
            owner=request.user, workspace__slug=workspace_slug
        ).first()
        if subscription is None:
            return Response({"message": "Subscription not found"}, status=404)
        paddle.subscriptions.cancel(subscription_id=subscription.subscription_id)
        subscription.is_active = False
        subscription.save()

    def put(self, request, workspace_slug):
        """
        This method will pause the workspace subscription
        """
        paddle = Client(settings.PADDLE_SECRET_KEY)
        subscription = Subscription.objects.filter(
            owner=request.user, workspace__slug=workspace_slug
        ).first()
        if subscription is None:
            return Response({"message": "Subscription not found"}, status=404)
        paddle.subscriptions.pause(
            subscription_id=subscription.subscription_id,
            operation=PauseSubscription(effective_from="next_billing_period"),
        )
        subscription.is_active = False
        subscription.save()
