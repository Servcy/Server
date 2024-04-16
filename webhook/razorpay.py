import json
import logging
import traceback

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def razorpay(request):
    try:
        body = json.loads(request.body)
        headers = request.headers
        logger.info(
            "Razorpay Webhook success",
            extra={
                "body": body,
                "headers": headers,
                "traceback": traceback.format_exc(),
            },
        )
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
