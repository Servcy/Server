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
from django.views.decorators.http import require_http_methods

from inbox.repository import InboxRepository
from integration.repository import IntegrationRepository
from integration.services.trello import TrelloService
from project.repository import ProjectRepository
from task.repository import TaskRepository

logger = logging.getLogger(__name__)

EVENT_MAP = {
    "addAttachmentToCard": "Added an attachment to a card",
    "addChecklistToCard": "Added a checklist to a card",
    "addMemberToBoard": "Added a member to a board",
    "addMemberToCard": "Added a member to a card",
    "commentCard": "Commented on a card",
    "convertToCardFromCheckItem": "Converted a check item to a card",
    "createBoard": "Created a board",
    "createCard": "Created a card",
    "deleteCard": "Deleted a card",
    "moveCardFromBoard": "Moved a card from one board to another",
    "moveCardToBoard": "Moved a card to a different board",
    "moveListFromBoard": "Moved a list from one board to another",
    "moveListToBoard": "Moved a list to a different board",
    "removeChecklistFromCard": "Removed a checklist from a card",
    "updateBoard": "Updated board details",
    "updateCard": "Updated card details",
    "updateCheckItemStateOnCard": "Updated check item state on a card",
    "updateChecklist": "Updated checklist details",
    "updateList": "Updated list details",
    "addLabelToCard": "Added a label to a card",
    "createCheckItem": "Created a check item",
    "createLabel": "Created a label",
    "deleteAttachmentFromCard": "Deleted an attachment from a card",
    "deleteCheckItem": "Deleted a check item",
    "deleteComment": "Deleted a comment",
    "deleteLabel": "Deleted a label",
    "removeLabelFromCard": "Removed a label from a card",
    "updateCheckItem": "Updated check item details",
    "updateComment": "Updated comment details",
}


def base64Digest(secret):
    """
    Returns a base64 encoded string of the hmac digest of the secret.
    """
    secret_bytes = secret.encode() if isinstance(secret, str) else secret
    client_secret_bytes = settings.TRELLO_APP_CLIENT_SECRET.encode()
    mac = hmac.new(client_secret_bytes, secret_bytes, hashlib.sha1)
    return base64.b64encode(mac.digest())


def is_from_trello(header, request_body, user_integration_id):
    """
    Checks if the request is from Trello.
    """
    hashed_header = base64Digest(header)
    hashed_body = base64Digest(
        base64Digest(
            request_body.decode()
            + f"{settings.BACKEND_URL}/webhook/trello/{user_integration_id}"
        )
    )
    return hmac.compare_digest(hashed_header, hashed_body)


@csrf_exempt
@require_http_methods(["POST", "HEAD"])
def trello(request, user_integration_id):
    """
    Trello webhook.
    """
    try:
        headers = request.headers
        if request.method == "HEAD":
            return HttpResponse(status=200)
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
        body = json.loads(request.body.decode())
        action = body["action"]
        logger.info(
            f"Received a request from Trello.",
            extra={
                "action": action,
                "headers": headers,
            },
        )
        if action["type"] not in EVENT_MAP.keys():
            return HttpResponse(status=200)
    except Exception:
        logger.exception(
            f"An error occurred while processing trello webhook.",
            extra={
                "body": request.body,
                "headers": headers,
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=500, content="Internal Server Error")
