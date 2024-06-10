import json
import logging
import traceback

from django.conf import settings
from common.billing import PLAN_LIMITS
from dataclasses import asdict
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from paddle_billing import Client
from paddle_billing.Notifications import Secret, Verifier

from billing.models import Subscription, SubscriptionWebhookEvent

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def paddle_hook(request):
    try:
        paddle = Client(settings.PADDLE_SECRET_KEY)
        body = json.loads(request.body)
        headers = request.headers
        integrity_check = Verifier().verify(
            request, Secret(settings.PADDLE_WEBHOOK_SECRET)
        )
        if not integrity_check:
            logger.error(
                "Paddle Webhook failed due to signature mismatch",
                extra={"body": body, "headers": headers},
            )
            return HttpResponse(status=403)
        event_id = body.get("event_id")
        if SubscriptionWebhookEvent.objects.filter(event_id=event_id).exists():
            return HttpResponse(status=200, content="Event already processed")
        event_type = body.get("event_type")
        customer_id = body.get("customer_id")
        customer_details = paddle.customers.get(customer_id)
        subscription_id = body.get("data", {}).get("id")
        subscription_details = paddle.subscriptions.get(subscription_id)
        plan_details = {
            "name": "Plus" if subscription_details.items[0].price.id == settings.PADDLE_PLUS_PRICE_ID else "Business",
        }
        if event_type == "subscription.created":
            Subscription.objects.create(
                subscription_id=subscription_id,
                customer_details=asdict(customer_details),
                plan_details=plan_details,
                limits=PLAN_LIMITS[plan_details["name"].lower()],
                is_active=False,
            )
        elif event_type == "subscription.activated":
            Subscription.objects.filter(subscription_id=subscription_id).update(
                is_active=True
            )
        elif event_type in ["subscription.canceled", "subscription.paused", "subscription.past_due"]:
            Subscription.objects.filter(subscription_id=subscription_id).update(
                is_active=False
            )
        elif event_type == "subscription.resumed":
            Subscription.objects.filter(subscription_id=subscription_id).update(
                is_active=True
            )
        return HttpResponse(status=200)
    except Exception as err:
        logger.exception(
            "Paddle Webhook failed",
            extra={
                "body": body,
                "headers": headers,
                "error": str(err),
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=500)
