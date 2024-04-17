from rest_framework.response import Response
import razorpay
from billing.models import Subscription
from billing.serializers import SubscriptionSerializer
from common.permissions import WorkspaceUserPermission
from common.views import BaseAPIView, BaseViewSet
from common.billing import PLAN_LIMITS
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
                    "limits": PLAN_LIMITS["starter"],
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
        if not plan_id:
            return Response(
                {"error": "Please provide the plan_id to create a subscription"},
                status=400,
            )
        plan = client.plan.fetch(plan_id)
        if Subscription.objects.filter(
            workspace__slug=workspace_slug, is_active=True
        ).exists():
            return Response(
                {"error": "Subscription already exists for the workspace"},
                status=400,
            )
        subscription = client.subscription.create(
            data={
                "plan_id": plan_id,
                "customer_notify": 1,  # Notify the customer about the subscription
                "total_count": 60,  # 60 months
                "customer_id": request.user.email,
            }
        )
        Subscription.objects.create(
            plan_details=plan,
            subscription_details=subscription,
            limits=PLAN_LIMITS[str(plan["item"]["name"]).lower()],
            valid_till=None,
            is_active=False,
            created_by=request.user,
            updated_by=request.user,
        )
        return Response(subscription)

    def get(self, request, workspace_slug):
        """
        This method will return the available subscription plans
        """
        client = razorpay.Client(auth=(self._api_key, self._api_secret))
        plans = client.plan.all()
        return Response(plans)
