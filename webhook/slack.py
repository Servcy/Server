import json
import logging
import traceback

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def slack(request):
    try:
        body = json.loads(request.body)
        if body["type"] == "url_verification":
            return HttpResponse(body["challenge"])
        logger.info(f"Received slack webhook: {body}")
        return HttpResponse(status=200)
    except Exception:
        logger.error(
            f"An error occurred while processing slack webhook.\n{traceback.format_exc()}"
        )
        return HttpResponse(status=500)
