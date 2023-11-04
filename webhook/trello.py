import base64
import hashlib
import hmac
import json
import logging
import traceback
import uuid

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from inbox.repository import InboxRepository
from integration.repository import IntegrationRepository
from integration.services.trello import TrelloService
from project.repository import ProjectRepository
from task.repository import TaskRepository

logger = logging.getLogger(__name__)


def base64Digest(secret):
    """
    Returns a base64 encoded string of the hmac digest of the secret.
    """
    mac = hmac.new(settings.TRELLO_APP_CLIENT_SECRET, secret, hashlib.sha1)
    return base64.b64encode(mac.digest())


def is_from_trello(header, request_body, user_integration_id):
    """
    Checks if the request is from Trello.
    """
    hashed_header = base64Digest(header)
    hashed_body = base64Digest(
        base64Digest(
            request_body
            + f"{settings.BACKEND_URL}/webhook/trello/{user_integration_id}"
        )
    )
    return hmac.compare_digest(hashed_header, hashed_body)


@csrf_exempt
@require_POST
def trello(request, user_integration_id):
    """
    Trello webhook.
    """
    try:
        headers = request.headers
        logger.info(
            f"Received a request from Trello.",
            extra={
                "body": request.body,
                "headers": headers,
            },
        )
        if not is_from_trello(
            headers.get("x-trello-webhook", ""), request.body, user_integration_id
        ):
            logger.warning(
                f"Received a request from an unknown source.",
                extra={
                    "body": request.body,
                    "headers": headers,
                },
            )
            return HttpResponse(status=403)
        body = json.loads(request.body)
    except Exception:
        logger.exception(
            f"An error occurred while processing trello webhook.",
            extra={
                "body": body,
                "headers": headers,
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=500, content="Internal Server Error")
