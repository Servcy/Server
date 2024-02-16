import base64
import hashlib
import hmac
import json
import logging
import traceback

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from inbox.repository import InboxRepository
from integration.repository import IntegrationRepository
from integration.repository.events import DisabledUserIntegrationEventRepository
from integration.utils.events import is_event_and_action_disabled
from project.repository import ProjectRepository
from task.repository import TaskRepository

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def jira(request):
    try:
        headers = request.headers
        body = request.body
        logger.info("Received Jira webhook.", extra={"headers": headers, "body": body})
        return HttpResponse(status=200, content="OK")
    except Exception:
        logger.exception(
            f"An error occurred while processing jira webhook.",
            extra={
                "body": body,
                "headers": headers,
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=500, content="Internal Server Error")
