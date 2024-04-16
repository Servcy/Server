from rest_framework.response import Response
import razorpay
from billing.models import Subscription
from billing.serializers import SubscriptionSerializer
from common.permissions import WorkspaceUserPermission
from common.views import BaseAPIView, BaseViewSet

from django.conf import settings


class WorkspaceSubscriptionView(BaseAPIView):
    """
    This view will handle the workspace subscriptions
    """

    permission_classes = [WorkspaceUserPermission]

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


class RazorpayView(BaseViewSet):
    """
    This view will handle the razorpay payment gateway
    """

    _api_key = settings.RAZORPAY_API_KEY
    _api_secret = settings.RAZORPAY_API_SECRET

    permission_classes = [WorkspaceUserPermission]

    def post(self, request, workspace_slug):
        """
        This method will create a subscription and return the subscription details
        """
        client = razorpay.Client(auth=(self._api_key, self._api_secret))
        plan_id = request.data.get("plan_id")
        return Response({})

    def get(self, request, workspace_slug):
        """
        This method will return the available subscription plans
        """
        client = razorpay.Client(auth=(self._api_key, self._api_secret))
        plans = client.plan.all()
        return Response(plans)
