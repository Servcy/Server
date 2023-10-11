import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def asana(request):
    try:
        if "X-Hook-Secret" in request.headers:
            return HttpResponse(
                status=200, headers={"X-Hook-Secret": request.headers["X-Hook-Secret"]}
            )
        return HttpResponse(status=200)
    except Exception as err:
        logger.exception(
            f"An error occurred while processing asana webhook.",
            exc_info=True,
            extra={"body": request.body, "headers": request.headers},
        )
        return HttpResponse(status=500)
