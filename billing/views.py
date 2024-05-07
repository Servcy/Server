import razorpay
from django.conf import settings
from rest_framework.response import Response

from billing.models import Subscription
from billing.serializers import SubscriptionSerializer
from common.billing import PLAN_LIMITS, PLAN_DETAILS
from common.permissions import WorkspaceUserPermission
from common.views import BaseAPIView, BaseViewSet
from iam.models import Workspace


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
                    "subscription_details": {},
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
                "subscription_details": {},
                "is_active": True,
            }
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
        plan_name = request.data.get("plan_name")
        if plan_name not in ["Plus", "Business"]:
            return Response(
                {"error": "Please provide a valid plan_name to create a subscription"},
                status=400,
            )
        plan = client.plan.create(
            data=PLAN_DETAILS[plan_name],
        )
        if Subscription.objects.filter(
            workspace__slug=workspace_slug, is_active=True
        ).exists():
            return Response(
                {"error": "Subscription already exists for the workspace"},
                status=400,
            )
        workspace = Workspace.objects.get(slug=workspace_slug)
        subscription = client.subscription.create(
            data={
                "plan_id": plan["id"],
                "customer_notify": 1,  # Notify the customer about the subscription
                "total_count": 60,  # 60 months
            }
        )
        Subscription.objects.create(
            plan_details=plan,
            workspace=workspace,
            subscription_details=subscription,
            limits=PLAN_LIMITS[str(plan["item"]["name"]).lower()],
            is_active=False,
            created_by=request.user,
            updated_by=request.user,
        )
        return Response(subscription)

    def delete(self, request, workspace_slug):
        """
        This method will cancel the subscription, effective at the end of the current billing cycle
        """
        subscription = Subscription.objects.filter(
            workspace__slug=workspace_slug, is_active=True
        ).first()
        if not subscription:
            return Response(
                {"error": "No active subscription found for the workspace"},
                status=400,
            )
        client = razorpay.Client(auth=(self._api_key, self._api_secret))
        client.subscription.cancel(
            subscription.subscription_details["id"],
            {"cancel_at_cycle_end": 1},
        )
        return Response({"message": "Subscription cancelled successfully"})
