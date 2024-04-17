import json
import logging
import traceback
import razorpay as Razorpay
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from billing.models import SubscriptionWebhookEvent, Subscription

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def razorpay(request):
    try:
        body = json.loads(request.body)
        headers = request.headers
        client = Razorpay.Client(
            auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET)
        )
        client.utility.verify_webhook_signature(
            request.body.decode("utf-8"),
            headers.get("X-Razorpay-Signature"),
            settings.RAZORPAY_API_SECRET,
        )
        event = body.get("event")
        event_id = headers.get("X-Razorpay-Event-Id")
        if event not in [
            "subscription.authenticated",
            "subscription.cancelled",
            "subscription.paused",
        ]:
            return HttpResponse(status=200)
        if SubscriptionWebhookEvent.objects.filter(event_id=event_id).exists():
            return HttpResponse(status=200)
        SubscriptionWebhookEvent.objects.create(event_id=event_id)
        return HttpResponse(status=200)
    except Exception as err:
        logger.exception(
            "Razorpay Webhook failed",
            extra={
                "body": body,
                "headers": headers,
                "error": str(err),
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=500)
